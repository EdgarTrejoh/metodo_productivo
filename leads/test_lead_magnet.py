import re
import logging
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.db import connections
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from analytics.models import ProductEvent
from .lead_magnet import RESOURCE_FILENAME
from .models import Consent, Lead, LeadMagnetAccess, LeadMagnetRequest


class ResourceFixture:
    def setUp(self):
        super().setUp()
        self.resource_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.resource_dir.cleanup)
        self.setting = override_settings(PRIVATE_RESOURCE_ROOT=Path(self.resource_dir.name))
        self.setting.enable()
        self.addCleanup(self.setting.disable)
        cache.clear()
        with zipfile.ZipFile(Path(self.resource_dir.name, RESOURCE_FILENAME), 'w') as book:
            book.writestr('[Content_Types].xml', '<Types/>')
            book.writestr('xl/workbook.xml', '<workbook/>')

    def request_resource(self, commercial=False):
        response = self.client.post(reverse('lead_magnet_resource'), {
            'name': 'Persona sintética', 'email': ' Persona@Example.Invalid ',
            **({'commercial': 'on'} if commercial else {}),
        })
        self.assertEqual(response.status_code, 302)
        return re.search(r'/acceso/([A-Za-z0-9_-]{43})/', mail.outbox[-1].body).group(1)


class LeadMagnetTests(ResourceFixture, TestCase):
    def test_csrf_accepts_local_origin_and_rejects_null_or_foreign_origin(self):
        token = self.request_resource()
        url = reverse('lead_magnet_access', args=[token])
        client = Client(enforce_csrf_checks=True)
        host = '127.0.0.1:8767'
        page = client.get(url, HTTP_HOST=host)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page['Referrer-Policy'], 'strict-origin')
        self.assertEqual(LeadMagnetRequest.objects.get().access_count, 0)
        data = {
            'operation': page.context['operation'],
            'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        }
        logging.disable(logging.WARNING)
        try:
            for origin in ('null', 'http://untrusted.invalid'):
                rejected = client.post(url, data, HTTP_HOST=host, HTTP_ORIGIN=origin)
                self.assertEqual(rejected.status_code, 403)
        finally:
            logging.disable(logging.NOTSET)
        self.assertEqual(LeadMagnetRequest.objects.get().access_count, 0)
        accepted = client.post(url, data, HTTP_HOST=host, HTTP_ORIGIN='http://127.0.0.1:8767')
        self.assertEqual(accepted.status_code, 200)
        self.assertIn(RESOURCE_FILENAME, accepted['Content-Disposition'])
        b''.join(accepted.streaming_content)
        accepted.close()
        self.assertEqual(LeadMagnetRequest.objects.get().access_count, 1)

    def test_missing_file_blocks_request_without_lead(self):
        Path(self.resource_dir.name, RESOURCE_FILENAME).unlink()
        self.assertContains(self.client.get(reverse('lead_magnet_resource')), 'deshabilitada')
        self.assertEqual(self.client.post(reverse('lead_magnet_resource'), {
            'name': 'Prueba', 'email': 'prueba@example.invalid',
        }).status_code, 503)
        self.assertFalse(Lead.objects.exists())

    def test_form_validation_and_optional_commercial_consent(self):
        url = reverse('lead_magnet_resource')
        response = self.client.post(url, {'name': '', 'email': 'incorrecto'})
        self.assertContains(response, 'Escribe tu nombre.')
        self.assertContains(response, 'Escribe un correo electrónico válido.')
        self.assertFalse(Lead.objects.exists())
        self.request_resource()
        lead = Lead.objects.get()
        self.assertEqual(lead.email, 'persona@example.invalid')
        claim = LeadMagnetRequest.objects.get()
        self.assertTrue(Consent.objects.get(execution=claim.execution, purpose='service').granted)
        self.assertFalse(Consent.objects.get(execution=claim.execution, purpose='commercial').granted)
        self.assertEqual(ProductEvent.objects.filter(kind='LEAD_CREATED').count(), 1)

    def test_repeat_request_reuses_lead_and_invalidates_old_link(self):
        old = self.request_resource()
        new = self.request_resource(commercial=True)
        self.assertNotEqual(old, new)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(ProductEvent.objects.filter(kind='LEAD_CREATED').count(), 1)
        self.assertEqual(self.client.get(reverse('lead_magnet_access', args=[old])).status_code, 410)
        self.assertEqual(self.client.get(reverse('lead_magnet_access', args=[new])).status_code, 200)
        self.assertEqual(Consent.objects.filter(purpose='commercial', granted=True).count(), 1)

    def test_email_contents_and_failure_retry(self):
        with patch('leads.lead_magnet.send_mail', side_effect=RuntimeError('fallo sintético')):
            response = self.client.post(reverse('lead_magnet_resource'), {
                'name': 'Persona sintética', 'email': 'persona@example.invalid',
            })
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get(reverse('lead_magnet_thanks')), 'No pudimos enviar')
        self.assertEqual(ProductEvent.objects.filter(kind='EMAIL_FAILED').count(), 1)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(self.client.post(reverse('lead_magnet_thanks')).status_code, 302)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(LeadMagnetRequest.objects.count(), 2)
        self.assertEqual(ProductEvent.objects.filter(kind='EMAIL_FAILED').count(), 1)
        claim = LeadMagnetRequest.objects.latest('pk')
        self.assertEqual(claim.expires_at - claim.issued_at, timedelta(hours=72))
        self.assertIn('3 días', mail.outbox[-1].body)
        self.assertIn('tres accesos', mail.outbox[-1].body)
        self.assertNotIn('Check PyME', mail.outbox[-1].body)

    def test_get_post_limit_and_duplicate_operation(self):
        token = self.request_resource()
        url = reverse('lead_magnet_access', args=[token])
        claim = LeadMagnetRequest.objects.get()
        for count in range(3):
            page = self.client.get(url)
            self.assertEqual(page.status_code, 200)
            self.assertEqual(LeadMagnetRequest.objects.get(pk=claim.pk).access_count, count)
            operation = page.context['operation']
            response = self.client.post(url, {'operation': operation})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b''.join(response.streaming_content).startswith(b'PK'))
            response.close()
            self.assertEqual(self.client.post(url, {'operation': operation}).status_code, 409)
        self.assertEqual(self.client.get(url).status_code, 410)
        self.assertEqual(claim.lead.leadmagnetrequest_set.get(pk=claim.pk).access_count, 3)
        self.assertEqual(LeadMagnetAccess.objects.count(), 3)
        self.assertEqual(ProductEvent.objects.filter(kind='LEADMAGNET_DELIVERED').count(), 3)

    def test_expired_and_missing_private_file_do_not_consume(self):
        token = self.request_resource()
        url = reverse('lead_magnet_access', args=[token])
        page = self.client.get(url)
        Path(self.resource_dir.name, RESOURCE_FILENAME).unlink()
        self.assertEqual(self.client.post(url, {'operation': page.context['operation']}).status_code, 503)
        self.assertEqual(LeadMagnetAccess.objects.count(), 0)
        with zipfile.ZipFile(Path(self.resource_dir.name, RESOURCE_FILENAME), 'w') as book:
            book.writestr('[Content_Types].xml', '<Types/>')
            book.writestr('xl/workbook.xml', '<workbook/>')
        claim = LeadMagnetRequest.objects.get()
        claim.expires_at = timezone.now() - timedelta(seconds=1)
        claim.save(update_fields=['expires_at'])
        self.assertEqual(self.client.post(url, {'operation': page.context['operation']}).status_code, 410)
        self.assertEqual(LeadMagnetRequest.objects.get().access_count, 0)

    def test_private_file_and_purpose_scope(self):
        token = self.request_resource()
        self.assertEqual(self.client.get('/private_resources/' + RESOURCE_FILENAME).status_code, 404)
        self.assertEqual(self.client.get(reverse('entry')).status_code, 200)
        self.assertEqual(self.client.get(reverse('lead_magnet_access', args=[token])).status_code, 200)
        self.assertEqual(ProductEvent.objects.filter(kind='LEADMAGNET_DELIVERED').count(), 0)

    def test_rate_limit_and_page_view(self):
        self.client.get(reverse('lead_magnet_resource'))
        self.assertEqual(ProductEvent.objects.filter(kind='PAGE_VIEW').count(), 1)
        for _ in range(5):
            self.request_resource()
        response = self.client.post(reverse('lead_magnet_resource'), {
            'name': 'Persona sintética', 'email': 'persona@example.invalid',
        })
        self.assertContains(response, 'demasiadas solicitudes')
        self.assertEqual(LeadMagnetRequest.objects.count(), 5)


class ConcurrentAccessTests(ResourceFixture, TransactionTestCase):
    def test_same_operation_cannot_consume_twice(self):
        self.client.post(reverse('lead_magnet_resource'), {
            'name': 'Prueba', 'email': 'prueba@example.invalid',
        })
        token = re.search(r'/acceso/([A-Za-z0-9_-]{43})/', mail.outbox[-1].body).group(1)
        url = reverse('lead_magnet_access', args=[token])
        operation = self.client.get(url).context['operation']
        cookie = self.client.cookies['sessionid'].value

        def submit(_):
            try:
                client = Client()
                client.cookies['sessionid'] = cookie
                response = client.post(url, {'operation': operation})
                if response.streaming:
                    b''.join(response.streaming_content)
                    response.close()
                return response.status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(submit, range(2)))
        self.assertEqual(statuses.count(200), 1, statuses)
        self.assertEqual(LeadMagnetAccess.objects.count(), 1)
        self.assertEqual(LeadMagnetRequest.objects.get().access_count, 1)
        self.assertEqual(ProductEvent.objects.filter(kind='LEADMAGNET_DELIVERED').count(), 1)

    def test_distinct_concurrent_operations_never_exceed_limit(self):
        self.client.post(reverse('lead_magnet_resource'), {
            'name': 'Prueba', 'email': 'prueba@example.invalid',
        })
        token = re.search(r'/acceso/([A-Za-z0-9_-]{43})/', mail.outbox[-1].body).group(1)
        url = reverse('lead_magnet_access', args=[token])
        claim = LeadMagnetRequest.objects.get()
        claim.access_count = 2
        claim.save(update_fields=['access_count'])
        clients = [Client(), Client()]
        operations = [client.get(url).context['operation'] for client in clients]

        def submit(index):
            try:
                response = clients[index].post(url, {'operation': operations[index]})
                if response.streaming:
                    b''.join(response.streaming_content)
                    response.close()
                return response.status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(submit, range(2)))
        self.assertEqual(LeadMagnetRequest.objects.get().access_count, 3)
        self.assertEqual(LeadMagnetAccess.objects.count(), 1)
        self.assertEqual(ProductEvent.objects.filter(kind='LEADMAGNET_DELIVERED').count(), 1)
