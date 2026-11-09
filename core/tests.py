from django.test import TestCase
from django.urls import reverse
from analytics.models import ProductEvent
from .break_even import BreakEvenForm, calculate
from decimal import Decimal
from unittest.mock import patch


class PortalStructureTests(TestCase):
    def test_privacy_return_uses_only_controlled_origin(self):
        from_check = self.client.get('/privacidad/?desde=check')
        self.assertContains(from_check, 'Cerrar esta pestaña y continuar con mi Check')
        self.assertContains(from_check, 'Si el navegador no permite cerrarla automáticamente')
        self.assertNotContains(from_check, '← Volver al inicio')
        self.assertNotContains(from_check, '← Volver a la página anterior')

        for url in ('/privacidad/', '/privacidad/?desde=https://example.com'):
            response = self.client.get(url)
            self.assertContains(response, '← Volver a la página anterior')
            self.assertContains(response, 'href="/">Ir al inicio</a>')
            self.assertNotContains(response, 'Cerrar esta pestaña y continuar con mi Check')

    def test_public_structure_is_navigable_without_fake_forms(self):
        structural_pages = (
            'tools', 'resources',
            'blog', 'contact', 'about', 'privacy', 'terms',
        )
        for name in structural_pages:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Entorno de desarrollo')
                if name == 'contact':
                    self.assertContains(response, '<form')
                else:
                    self.assertNotContains(response, '<form')
                self.assertNotContains(response, 'class="section-mark"')
        self.assertContains(self.client.get(reverse('break_even')), '<form')
        self.assertRedirects(self.client.get(reverse('cash_flow_resource')), reverse('lead_magnet_resource'))

    def test_home_links_to_portal_and_existing_check(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, reverse('entry'))
        for name in ('tools', 'resources', 'blog', 'contact', 'about', 'privacy', 'terms'):
            self.assertContains(response, reverse(name))
        self.assertNotContains(response, 'recuperar-diagnostico')
        self.assertEqual(self.client.get(reverse('entry')).status_code, 200)

    def test_section_navigation_and_breadcrumbs(self):
        for name, label in (
            ('tools', 'Herramientas'), ('blog', 'Contenidos'),
            ('resources', 'Recursos'), ('contact', 'Contacto'),
            ('entry', 'Check PyME'),
        ):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertContains(response, 'aria-label="Ruta de navegación"')
                self.assertContains(response, f'<span aria-current="page">{label}</span>')
                self.assertContains(response, f'aria-current="location">{label}</a>')
        self.assertNotContains(self.client.get(reverse('home')), 'aria-label="Ruta de navegación"')
        self.client.post(reverse('start'))
        self.assertNotContains(self.client.get(reverse('question', args=[1])), 'aria-label="Ruta de navegación"')

    def test_content_naming_and_broad_brand_message(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Contenidos</a>', count=2)
        self.assertNotContains(response, '>Blog</a>')
        self.assertContains(response, 'personas y negocios')
        self.assertNotContains(response, 'Cuatro miradas para un mismo negocio.')
        self.assertContains(response, 'class="feature-card', count=4)
        self.assertContains(self.client.get(reverse('entry')), 'check-entry-card')


class BreakEvenTests(TestCase):
    url = '/herramientas/punto-de-equilibrio/'

    def submit(self, costs='75000', price='1200', variable_cost='650', *, reuse=None):
        if reuse is None:
            page = self.client.get(self.url)
            reuse = page.context['interaction']
        return self.client.post(self.url, {
            'interaction': reuse, 'costs': costs, 'price': price,
            'variable_cost': variable_cost,
        }), reuse

    def test_reference_case_and_post_privacy(self):
        response, _ = self.submit()
        self.assertContains(response, 'class="calculator-result result-positive"')
        self.assertContains(response, '>Margen positivo</p>')
        self.assertContains(response, '137</strong>')
        self.assertContains(response, '$164,400.00</strong>')
        self.assertContains(response, '$550.00</strong>')
        self.assertContains(response, '45.8 %</strong>')
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_STARTED').count(), 1)
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_COMPLETED').count(), 1)
        self.assertNotIn('75000', response.request['PATH_INFO'])
        self.assertNotIn('75000', str(self.client.session.items()))
        self.assertFalse(any(hasattr(event, 'costs') for event in ProductEvent.objects.all()))

    def test_invalid_inputs_and_started_only(self):
        for values, message in (
            ({'costs': '', 'price': '1200', 'variable_cost': '650'}, 'Ingresa los costos fijos mensuales.'),
            ({'costs': 'abc', 'price': '1200', 'variable_cost': '650'}, 'Ingresa un importe numérico válido.'),
            ({'costs': '-1', 'price': '1200', 'variable_cost': '650'}, 'Los costos fijos no pueden ser negativos.'),
            ({'costs': '1.001', 'price': '1200', 'variable_cost': '650'}, 'Usa como máximo dos decimales.'),
            ({'costs': '0', 'price': '0', 'variable_cost': '0'}, 'Se requiere un precio positivo'),
            ({'costs': '0', 'price': '1000000000', 'variable_cost': '0'}, 'El importe máximo'),
            ({'costs': '0', 'price': '1', 'variable_cost': '-1'}, 'El costo variable no puede ser negativo.'),
        ):
            with self.subTest(values=values):
                response, _ = self.submit(**values)
                self.assertContains(response, message)
                self.assertNotContains(response, 'id="resultado"')
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_STARTED').count(), 7)
        self.assertFalse(ProductEvent.objects.filter(kind='TOOL_COMPLETED').exists())

    def test_zero_and_negative_margin_are_interpretable(self):
        for costs, price, variable_cost, expected in (
            ('75000', '100', '100', 'Cada venta cubre solo su costo variable'),
            ('0', '100', '100', 'Cada venta cubre solo su costo variable'),
            ('75000', '100', '120', 'Cada venta genera una contribución negativa'),
            ('0', '100', '120', 'Cada venta genera una contribución negativa'),
        ):
            with self.subTest(costs=costs, variable_cost=variable_cost):
                response, _ = self.submit(costs, price, variable_cost)
                self.assertContains(response, expected)
                self.assertContains(response, 'No aplica</strong>', count=2)
                self.assertContains(response, 'result-zero' if price == variable_cost else 'result-negative')
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_COMPLETED').count(), 4)

    def test_negative_reference_has_four_cards_and_same_events(self):
        response, _ = self.submit('65000', '1200', '4500')
        self.assertContains(response, 'class="calculator-result result-negative"')
        self.assertContains(response, '>Margen negativo</p>')
        self.assertContains(response, 'No aplica</strong>', count=2)
        self.assertContains(response, '-$3,300.00</strong>')
        self.assertContains(response, '-275.0 %</strong>')
        self.assertContains(response, 'no existe un punto de equilibrio con ventas positivas')
        self.assertContains(response, 'class="result-card"', count=4)
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_STARTED').count(), 1)
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_COMPLETED').count(), 1)

    def test_zero_margin_visual_state_keeps_exact_values(self):
        response, _ = self.submit('65000', '1200', '1200')
        self.assertContains(response, 'class="calculator-result result-zero"')
        self.assertContains(response, '>Margen cero</p>')
        self.assertContains(response, 'No aplica</strong>', count=2)
        self.assertContains(response, '$0.00</strong>')
        self.assertContains(response, '0.0 %</strong>')
        self.assertContains(response, 'Cada venta cubre solo su costo variable')

    def test_zero_fixed_costs_rounding_and_large_result(self):
        zero, _ = self.submit('0', '100', '25')
        self.assertContains(zero, 'class="calculator-result result-positive"')
        self.assertContains(zero, 'No hay costos fijos mensuales que cubrir')
        self.assertContains(zero, '0</strong>')
        self.assertContains(zero, '$0.00</strong>')
        rounded, _ = self.submit('1', '1.01', '1')
        self.assertContains(rounded, '100</strong>')
        large, _ = self.submit('999999999.99', '0.02', '0.01')
        self.assertContains(large, '99,999,999,999</strong>')
        self.assertContains(large, 'estimación bajo supuestos')

    def test_input_boundaries_and_decimal_precision(self):
        self.assertTrue(BreakEvenForm({'costs': '999999999.99', 'price': '999999999.99', 'variable_cost': '999999999.99'}).is_valid())
        self.assertTrue(BreakEvenForm({'costs': '0', 'price': '0.01', 'variable_cost': '0'}).is_valid())
        self.assertFalse(BreakEvenForm({'costs': '0', 'price': '0.001', 'variable_cost': '0'}).is_valid())
        result = calculate({'costs': Decimal('1'), 'price': Decimal('0.03'), 'variable_cost': Decimal('0.01')})
        self.assertEqual(result['units'], '50')
        self.assertEqual(result['income'], '$1.50')

    def test_replay_does_not_duplicate_and_new_submission_does(self):
        first, token = self.submit()
        self.assertContains(first, '$164,400.00')
        replay, _ = self.submit(reuse=token)
        self.assertRedirects(replay, self.url)
        refreshed = self.client.get(replay['Location'])
        self.assertNotContains(refreshed, 'id="resultado"')
        self.assertNotContains(refreshed, 'value="75000"')
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_STARTED').count(), 1)
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_COMPLETED').count(), 1)
        new_token = refreshed.context['interaction']
        self.submit('10', '2', '1', reuse=new_token)
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_STARTED').count(), 2)
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_COMPLETED').count(), 2)

    def test_page_open_does_not_create_events_and_form_needs_no_javascript(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'method="post"')
        self.assertNotContains(response, '<script')
        self.assertFalse(ProductEvent.objects.exists())
        self.assertContains(response, 'aria-describedby="costs-help')

    def test_server_failure_does_not_mark_completion(self):
        with patch('core.views.calculate', side_effect=RuntimeError('fallo de cálculo')):
            with self.assertRaises(RuntimeError):
                self.submit()
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_STARTED').count(), 1)
        self.assertFalse(ProductEvent.objects.filter(kind='TOOL_COMPLETED').exists())

    def test_clear_after_result_and_error_has_no_events(self):
        result, _ = self.submit()
        self.assertContains(result, 'id="resultado"')
        cleared = self.client.get(self.url)
        self.assertNotContains(cleared, 'id="resultado"')
        self.assertNotContains(cleared, 'value="75000"')
        self.assertEqual(ProductEvent.objects.count(), 2)
        invalid, _ = self.submit(costs='-1')
        self.assertContains(invalid, 'Los costos fijos no pueden ser negativos.')
        self.assertContains(invalid, 'value="1200"')
        cleared_again = self.client.get(self.url)
        self.assertNotContains(cleared_again, 'Los costos fijos no pueden ser negativos.')
        self.assertNotContains(cleared_again, 'value="1200"')
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_STARTED').count(), 2)
        self.assertEqual(ProductEvent.objects.filter(kind='TOOL_COMPLETED').count(), 1)

    def test_negative_money_and_three_level_breadcrumb(self):
        response, _ = self.submit('0', '100', '150')
        self.assertContains(response, '-$50.00</strong>')
        self.assertNotContains(response, '$-50.00')
        self.assertContains(response, f'<a href="{reverse("tools")}">Herramientas</a>')
        self.assertContains(response, '<span aria-current="page">Punto de equilibrio</span>')
        self.assertContains(response, 'aria-label="Ruta de navegación"')
        self.assertContains(response, '>Limpiar</a>')

class EditorialStateTests(TestCase):
    def test_resources_reflects_file_without_promising_email(self):
        for available in (False, True):
            with self.subTest(available=available), patch('core.views.storage.available', return_value=available) as check:
                for name in ('resources',):
                    response = self.client.get(reverse(name))
                    self.assertContains(response, 'Archivo disponible para pruebas' if available else 'Archivo temporalmente no disponible')
                    self.assertNotContains(response, 'Entrega pendiente')
                    self.assertNotContains(response, 'A-03')
                self.assertEqual(check.call_count, 1)

    def test_home_preserves_ctas_and_links_to_store(self):
        response = self.client.get(reverse('home'))
        for cta in ('tools', 'resources', 'store', 'content'):
            self.assertContains(response, f'data-home-cta="{cta}"', count=1)
        self.assertContains(response, 'data-home-cta="check"', count=2)
        self.assertContains(response, 'Plantilla gratuita')
        self.assertContains(response, f'href="{reverse("blog")}" data-home-cta="content">Explorar contenidos')
        self.assertContains(response, f'href="{reverse("entry")}" data-home-cta="check">¿Tienes una PyME? Haz el Check PyME')
        self.assertContains(response, f'href="{reverse("store")}" data-home-cta="store">Ver la tienda')
        for name in ('tools', 'resources', 'blog', 'entry', 'store'):
            self.assertContains(response, reverse(name))

    def test_commercial_pages_do_not_expose_obsolete_project_labels(self):
        for name in ('home', 'tools', 'resources', 'blog', 'store', 'contact'):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                for label in ('Fase A', 'A-03', 'O-08', 'aprobado con salvedades', 'Disponible en desarrollo', 'Portal en desarrollo'):
                    self.assertNotContains(response, label)
                self.assertContains(response, 'Entorno de desarrollo')
        response = self.client.get(reverse('tools'))
        self.assertContains(response, 'Calcula el punto de equilibrio de tu negocio.')
        self.assertContains(response, 'Descubre cuántas unidades de un producto o servicio necesitas vender al mes para cubrir sus costos.')

class AboutPageTests(TestCase):
    def test_about_content_and_routes(self):
        home = self.client.get(reverse('home'))
        self.assertContains(home, f'href="{reverse("about")}">Acerca de</a>')
        response = self.client.get(reverse('about'))
        self.assertContains(response, 'Para decidir mejor, entiende tus números.')
        self.assertContains(response, 'Para quien quiere entender su dinero.')
        self.assertContains(response, 'Primero explico, luego te doy la herramienta.')
        self.assertContains(response, 'Quién está detrás')
        self.assertContains(response, 'Lo que aprendí dentro del sistema financiero.')
        self.assertContains(response, 'Cómo trabajo')
        content = response.content.decode()
        self.assertLess(content.index('about-founder'), content.index('about-audience'))
        self.assertLess(content.index('about-audience'), content.index('about-method'))
        self.assertContains(response, 'Soy Edgar Trejo. Durante más de 25 años trabajé en banca, crédito hipotecario y análisis financiero')
        self.assertContains(response, f'href="{reverse("contact")}">Escríbenos')
        self.assertNotContains(response, 'Empieza por lo que necesitas hoy.')
        self.assertContains(response, '<span aria-current="page">Acerca de</span>')
        self.assertNotContains(response, 'Contenido editorial provisional')
