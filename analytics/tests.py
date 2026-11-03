import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import Client, TestCase
from django.urls import resolve
from django.utils import timezone

from content.models import Article, PublicationStatus

from .models import ProductEvent, TrafficEvent, TrafficSession
from .tracking import _page_key, record_tool


class InitialTrafficTests(TestCase):
    def test_distinct_article_pages_have_distinct_safe_keys(self):
        for slug in ('articulo-a', 'articulo-b'):
            Article.objects.create(
                title=slug, slug=slug, summary='Resumen sintético', body='<p>Prueba.</p>',
                category=Article.Category.DATA, status=PublicationStatus.PUBLISHED,
                published_at=timezone.now(),
            )
        self.client.get('/blog/articulo-a/')
        self.client.get('/blog/articulo-b/', HTTP_REFERER='http://testserver/blog/articulo-a/')
        events = list(TrafficEvent.objects.filter(kind='PAGE_VIEW').order_by('pk'))
        self.assertEqual(len(events), 2)
        self.assertNotEqual(events[0].page, events[1].page)
        self.assertTrue(events[1].effective_navigation)
        self.assertNotIn('articulo-', str([event.page for event in events]))
        self.client.get('/blog/articulo-b/', HTTP_REFERER='http://testserver/blog/articulo-b/')
        self.assertEqual(TrafficEvent.objects.filter(kind='PAGE_VIEW').count(), 2)

    def test_store_detail_keys_distinguish_products_without_slug_storage(self):
        first = _page_key(resolve('/tienda/producto-a/'))
        second = _page_key(resolve('/tienda/producto-b/'))
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith('store_detail:'))
        self.assertNotIn('producto-a', first)

    def test_invalid_referer_is_uncredited_without_blocking_page(self):
        self.client.get('/')
        for referer in ('', 'http://[', 'https://external.example/'):
            response = self.client.get('/herramientas/', HTTP_REFERER=referer)
            self.assertEqual(response.status_code, 200)
        self.assertFalse(TrafficSession.objects.filter(qualified_at__isnull=False).exists())
        self.assertEqual(self.client.get('/herramientas/', HTTP_REFERER='http://testserver/').status_code, 200)
        self.assertEqual(TrafficSession.objects.filter(qualified_at__isnull=False).count(), 1)
        count = TrafficEvent.objects.filter(kind='PAGE_VIEW').count()
        self.client.get('/herramientas/', HTTP_REFERER='http://testserver/herramientas/')
        self.assertEqual(TrafficEvent.objects.filter(kind='PAGE_VIEW').count(), count)

    def test_operation_cannot_be_reused_for_other_kind_cta_or_session(self):
        first = Client(enforce_csrf_checks=True)
        first.get('/')
        operation = str(uuid.uuid4())
        token = first.cookies['csrftoken'].value
        self.assertEqual(first.post('/analitica/cta/', {'cta': 'tools', 'operation': operation},
                                    HTTP_X_CSRFTOKEN=token).status_code, 204)
        self.assertEqual(first.post('/analitica/cta/', {'cta': 'tools', 'operation': operation},
                                    HTTP_X_CSRFTOKEN=token).status_code, 204)
        self.assertEqual(first.post('/analitica/cta/', {'cta': 'check', 'operation': operation},
                                    HTTP_X_CSRFTOKEN=token).status_code, 400)
        second = Client(enforce_csrf_checks=True)
        second.get('/')
        self.assertEqual(second.post('/analitica/cta/', {'cta': 'tools', 'operation': operation},
                                     HTTP_X_CSRFTOKEN=second.cookies['csrftoken'].value).status_code, 400)
        self.assertEqual(TrafficEvent.objects.filter(operation=operation).count(), 1)
        request = self.client.get('/herramientas/punto-de-equilibrio/').wsgi_request
        record_tool(request, uuid.UUID(operation))
        self.assertFalse(TrafficEvent.objects.filter(kind='TOOL_STARTED', operation=operation).exists())

        tool_operation = uuid.uuid4()
        tool_request = first.get('/herramientas/punto-de-equilibrio/').wsgi_request
        record_tool(tool_request, tool_operation)
        self.assertEqual(first.post('/analitica/cta/', {'cta': 'tools', 'operation': str(tool_operation)},
                                    HTTP_X_CSRFTOKEN=token).status_code, 400)
        self.assertEqual(TrafficEvent.objects.filter(operation=tool_operation, kind='TOOL_STARTED').count(), 1)

    def test_two_distinct_document_navigations_qualify_once(self):
        self.client.get('/')
        session = TrafficSession.objects.get()
        self.assertIsNone(session.qualified_at)
        self.client.get('/herramientas/', HTTP_REFERER='http://testserver/')
        session.refresh_from_db()
        self.assertIsNotNone(session.qualified_at)
        self.client.get('/recursos/', HTTP_REFERER='http://testserver/herramientas/')
        self.assertEqual(TrafficSession.objects.count(), 1)
        self.assertEqual(TrafficSession.objects.filter(qualified_at__isnull=False).count(), 1)
        self.assertEqual(TrafficEvent.objects.filter(kind='PAGE_VIEW', effective_navigation=True).count(), 2)

    def test_reload_prefetch_and_missing_referer_do_not_qualify(self):
        self.client.get('/')
        self.client.get('/', HTTP_REFERER='http://testserver/')
        self.client.get('/herramientas/', HTTP_REFERER='https://untrusted.example/')
        self.client.get('/recursos/', HTTP_PURPOSE='prefetch')
        self.assertEqual(TrafficEvent.objects.filter(kind='PAGE_VIEW').count(), 2)
        self.assertFalse(TrafficSession.objects.filter(qualified_at__isnull=False).exists())
        self.client.get('/recursos/', HTTP_REFERER='http://testserver/herramientas/', HTTP_SEC_FETCH_DEST='image')
        self.assertFalse(TrafficSession.objects.filter(qualified_at__isnull=False).exists())

    def test_real_tool_post_qualifies_once_without_amounts(self):
        page = self.client.get('/herramientas/punto-de-equilibrio/')
        data = {'interaction': page.context['interaction'], 'costs': '75000', 'price': '1200', 'variable_cost': '650'}
        response = self.client.post('/herramientas/punto-de-equilibrio/', data)
        self.assertContains(response, '137</strong>')
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_STARTED').count(), 1)
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_COMPLETED').count(), 1)
        self.assertEqual(TrafficEvent.objects.filter(kind='TOOL_STARTED').count(), 1)
        self.assertEqual(TrafficSession.objects.filter(qualified_at__isnull=False).count(), 1)
        self.client.post('/herramientas/punto-de-equilibrio/', data)
        self.assertEqual(TrafficEvent.objects.filter(kind='TOOL_STARTED').count(), 1)
        self.assertNotIn('75000', str(list(TrafficEvent.objects.values())))

    def test_invalid_tool_submission_still_starts_once(self):
        page = self.client.get('/herramientas/punto-de-equilibrio/')
        self.client.post('/herramientas/punto-de-equilibrio/', {
            'interaction': page.context['interaction'], 'costs': '', 'price': '1200', 'variable_cost': '650',
        })
        self.assertEqual(TrafficEvent.objects.filter(kind='TOOL_STARTED').count(), 1)
        self.assertFalse(ProductEvent.objects.filter(kind='TOOL_COMPLETED').exists())

    def test_home_cta_is_idempotent_and_link_remains_direct(self):
        client = Client(enforce_csrf_checks=True)
        home = client.get('/')
        self.assertContains(home, 'href="/herramientas/" data-home-cta="tools"')
        operation = str(uuid.uuid4())
        data = {'cta': 'tools', 'operation': operation}
        for _ in range(2):
            response = client.post('/analitica/cta/', data, HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value)
            self.assertEqual(response.status_code, 204)
        self.assertEqual(TrafficEvent.objects.filter(kind='CTA_CLICK', cta='tools').count(), 1)
        self.assertEqual(client.get('/herramientas/').status_code, 200)
        self.assertEqual(client.post('/analitica/cta/', {'cta': 'unknown', 'operation': operation},
                                     HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value).status_code, 400)

    def test_analytics_failure_does_not_block_public_page_or_calculation(self):
        with patch('analytics.tracking.TrafficEvent.objects.create', side_effect=DatabaseError('synthetic')):
            self.assertEqual(self.client.get('/').status_code, 200)
        page = self.client.get('/herramientas/punto-de-equilibrio/')
        with patch('core.views.ProductEvent.objects.get_or_create', side_effect=DatabaseError('synthetic')):
            response = self.client.post('/herramientas/punto-de-equilibrio/', {
                'interaction': page.context['interaction'], 'costs': '75000', 'price': '1200', 'variable_cost': '650',
            })
        self.assertContains(response, '137</strong>')

    def test_development_internal_and_bot_are_not_official_traffic(self):
        self.client.get('/')
        self.assertEqual(TrafficSession.objects.get().environment, 'local')
        self.assertFalse(TrafficSession.objects.filter(environment='public').exists())
        bot = Client(HTTP_USER_AGENT='ExampleBot/1.0')
        bot.get('/')
        self.assertEqual(TrafficSession.objects.get(excluded_reason='bot').environment, 'local')
        staff = User.objects.create_user('synthetic', password='synthetic-password', is_staff=True)
        internal = Client()
        internal.force_login(staff)
        internal.get('/')
        self.assertEqual(TrafficSession.objects.get(excluded_reason='internal').environment, 'local')
