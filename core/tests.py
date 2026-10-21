from django.test import TestCase
from django.urls import reverse
from analytics.models import ProductEvent
from .break_even import BreakEvenForm, calculate
from decimal import Decimal
from unittest.mock import patch


class PortalStructureTests(TestCase):
    def test_public_structure_is_navigable_without_fake_forms(self):
        structural_pages = (
            'tools', 'resources', 'cash_flow_resource',
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
        self.assertContains(response, 'proyectos, trabajo y negocios')
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
