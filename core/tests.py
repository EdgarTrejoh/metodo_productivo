from django.test import TestCase
from django.urls import reverse


class PortalStructureTests(TestCase):
    def test_public_structure_is_navigable_without_fake_forms(self):
        structural_pages = (
            'tools', 'break_even', 'resources', 'cash_flow_resource',
            'blog', 'contact', 'about', 'privacy', 'terms',
        )
        for name in structural_pages:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Entorno de desarrollo')
                self.assertNotContains(response, '<form')
                self.assertNotContains(response, 'class="section-mark"')

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
