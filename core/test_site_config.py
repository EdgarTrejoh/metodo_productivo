from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from .site_config import load_site_config, notice_config_complete, require_complete_notice_config


EXAMPLE = (settings.BASE_DIR / 'config.example.yaml').read_text(encoding='utf-8')


class SiteConfigurationTests(SimpleTestCase):
    def config_file(self, contents):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / 'config.yaml'
        path.write_text(contents, encoding='utf-8')
        return path

    def test_valid_configuration_fills_draft_without_publishing_it(self):
        complete = (EXAMPLE.replace('nombre_legal: ""', 'nombre_legal: "Persona Sintética"')
                    .replace('domicilio: ""', 'domicilio: "Domicilio sintético"')
                    .replace('correo_arco: ""', 'correo_arco: "arco@example.invalid"')
                    .replace('responsable_atencion: ""', 'responsable_atencion: "Equipo sintético"')
                    .replace('version_aviso: ""', 'version_aviso: "1"')
                    .replace('fecha_actualizacion: ""', 'fecha_actualizacion: "2026-10-30"'))
        path = self.config_file(complete)
        with override_settings(SITE_CONFIG_PATH=path):
            response = self.client.get('/privacidad/')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['site_admin_config_ready'])
            self.assertEqual(require_complete_notice_config()['responsable']['nombre_legal'], 'Persona Sintética')
            self.assertContains(response, '<h1>Aviso de privacidad</h1>')
            self.assertContains(response, 'BORRADOR — NO AUTORIZADO PARA PUBLICACIÓN')
            self.assertContains(response, 'Persona Sintética')
            self.assertContains(response, 'Domicilio sintético')
            self.assertContains(response, 'mailto:arco@example.invalid')
            self.assertContains(response, 'Equipo sintético')
            self.assertContains(response, 'versión 1 · fecha 2026-10-30')
            self.assertContains(response, 'Estas finalidades no dependen de que aceptes recibir publicidad')
            self.assertContains(response, 'Google Cloud')
            self.assertContains(response, 'Brevo')
            self.assertContains(response, 'href="/privacidad/"')
            self.assertNotContains(response, 'Aviso de privacidad en preparación')

    def test_missing_file_keeps_provisional_page_available(self):
        with TemporaryDirectory() as directory:
            with override_settings(SITE_CONFIG_PATH=Path(directory) / 'missing.yaml'):
                response = self.client.get('/privacidad/')
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.context['site_admin_config'])
                self.assertFalse(response.context['site_admin_config_ready'])
                self.assertContains(response, '<h1>Aviso de privacidad</h1>')
                self.assertContains(response, 'Nombre legal pendiente')
                self.assertContains(response, 'BORRADOR — NO AUTORIZADO PARA PUBLICACIÓN')
                with self.assertRaises(ImproperlyConfigured):
                    require_complete_notice_config()

    def test_incomplete_example_cannot_enable_definitive_notice(self):
        path = self.config_file(EXAMPLE)
        self.assertFalse(notice_config_complete(load_site_config(path)))
        with override_settings(SITE_CONFIG_PATH=path):
            response = self.client.get('/privacidad/')
            self.assertContains(response, 'configuración administrativa local está incompleta')
            self.assertContains(response, 'correo ARCO pendiente')
            self.assertContains(response, '4. Finalidad opcional: comunicaciones comerciales')
            self.assertContains(response, '5. Con quién compartimos tus datos')
        with self.assertRaises(ImproperlyConfigured):
            require_complete_notice_config(path)

    def test_nonlocal_environment_keeps_unpublished_placeholder(self):
        with override_settings(DJANGO_ENV='staging'):
            response = self.client.get('/privacidad/')
        self.assertContains(response, 'Aviso de privacidad en preparación')
        self.assertNotContains(response, 'Datos tratados')

    def test_editorial_v11_preserves_approved_topics(self):
        response = self.client.get('/privacidad/')
        for text in (
            'cookies técnicas de sesión y de protección de formularios',
            'El Check PyME no pide datos financieros, patrimoniales ni datos personales sensibles',
            'Los resultados tienen carácter exclusivamente informativo y orientativo',
            'Si lo das, lo usamos únicamente para dar seguimiento a tu solicitud',
            'La casilla para autorizarlo es independiente y aparece desmarcada',
            'registros básicos de uso del portal',
        ):
            with self.subTest(text=text):
                self.assertContains(response, text)
        for marker in (
            '[DETALLAR LOGS Y COOKIES REALES]',
            '[CONFIRMAR CLASIFICACIÓN JURÍDICA DEL INVENTARIO COMPLETO, INCLUIDO TEXTO LIBRE]',
            '[DELIMITAR FINALIDAD Y BASE/MODALIDAD]',
            '[DESCRIBIR COMUNICACIONES REALES, FRECUENCIA/CANAL SI SE APRUEBAN]',
            '[DEFINIR MODALIDAD JURÍDICA Y TEXTO FINAL]',
        ):
            self.assertNotContains(response, marker)
        self.assertContains(response, '24 meses desde tu última interacción')
        self.assertContains(response, 'BORRADOR — NO AUTORIZADO PARA PUBLICACIÓN')

    def test_integral_draft_has_eight_sections_and_approved_policy(self):
        response = self.client.get('/privacidad/?desde=check')
        self.assertEqual(response.status_code, 200)
        for section in ('1. Quién es el responsable', '2. Qué datos recabamos', '3. Para qué usamos tus datos',
                        '4. Finalidad opcional: comunicaciones comerciales', '5. Con quién compartimos tus datos',
                        '6. Cuánto tiempo conservamos tus datos', '7. Tus derechos', '8. Cambios a este aviso'):
            with self.subTest(section=section):
                self.assertContains(response, f'>{section}</h2>')
        for text in ('12 meses después de cerrarse', '24 meses sin actividad',
                     'ese mecanismo aún no está implementado',
                     'El ejercicio de tus derechos de acceso, rectificación, cancelación y oposición es gratuito',
                     'Los videos se cargan solo cuando tú das clic para reproducirlos',
                     'Cualquier modificación se publicará en'):
            with self.subTest(text=text):
                self.assertContains(response, text)
        self.assertContains(response, 'data-privacy-return="check"')
        self.assertContains(response, 'BORRADOR — NO AUTORIZADO PARA PUBLICACIÓN')
        self.assertNotContains(response, '[INSERTAR PLAZOS')
        self.assertNotContains(response, '[MEDIO Y PROCEDIMIENTO APROBADOS]')
        self.assertNotContains(response, 'Anexo: aviso simplificado')
        self.assertContains(response, 'role="region" aria-label="Plazos de conservación"')

    def test_configurable_values_change_without_template_edits(self):
        custom = (EXAMPLE.replace('nombre_legal: ""', 'nombre_legal: "Persona Variable"')
                  .replace('domicilio: ""', 'domicilio: "Domicilio variable"')
                  .replace('correo_arco: ""', 'correo_arco: "derechos@example.invalid"')
                  .replace('responsable_atencion: ""', 'responsable_atencion: "Atención variable"')
                  .replace('version_aviso: ""', 'version_aviso: "1.1"')
                  .replace('fecha_actualizacion: ""', 'fecha_actualizacion: "2026-10-30"')
                  .replace('url_aviso_integral: "/privacidad/"',
                           'url_aviso_integral: "https://example.invalid/privacidad/"')
                  .replace('nombre: "Google Cloud"', 'nombre: "Alojamiento Sintético"')
                  .replace('ubicacion: "Querétaro, México"', 'ubicacion: "Región sintética"')
                  .replace('nombre: "Brevo"', 'nombre: "Correo Sintético"')
                  .replace('ubicacion: "Unión Europea (Francia y Bélgica)"',
                           'ubicacion: "Ubicación sintética"'))
        with override_settings(SITE_CONFIG_PATH=self.config_file(custom)):
            response = self.client.get('/privacidad/')
        for value in ('Persona Variable', 'Domicilio variable', 'mailto:derechos@example.invalid',
                      'Atención variable', 'versión 1.1 · fecha 2026-10-30',
                      'Alojamiento Sintético', 'Región sintética', 'Correo Sintético',
                      'Ubicación sintética', 'href="https://example.invalid/privacidad/"'):
            with self.subTest(value=value):
                self.assertContains(response, value)
        self.assertContains(response, 'BORRADOR — NO AUTORIZADO PARA PUBLICACIÓN')
        self.assertNotContains(response, 'Google Cloud')
        self.assertNotContains(response, 'Brevo')

    def test_notice_url_and_provider_structure_are_validated(self):
        invalid = (
            EXAMPLE.replace('url_aviso_integral: "/privacidad/"', 'url_aviso_integral: "http://example.com/privacidad/"'),
            EXAMPLE.replace('url_aviso_integral: "/privacidad/"', 'url_aviso_integral: "https://example.com/privacidad/?token=1"'),
            EXAMPLE.replace('url_aviso_integral: "/privacidad/"', 'url_aviso_integral: "//example.com/privacidad/"'),
            EXAMPLE.replace('nombre: "Brevo"', 'nombre: 123'),
            EXAMPLE.replace('    correo:\n      nombre:', '    correo:\n      otro:'),
        )
        for contents in invalid:
            with self.subTest(contents=contents[-80:]):
                with self.assertRaises(ImproperlyConfigured):
                    load_site_config(self.config_file(contents))

    def test_invalid_yaml_and_structure_are_rejected(self):
        for contents in ('responsable: [', '[]', '!!python/object/apply:os.system ["echo unsafe"]',
                         'responsable: {}\nprivacidad: {}',
                         EXAMPLE.replace('nombre_legal: ""', 'nombre_legal: 123'),
                         EXAMPLE + '\ncontraseña: ejemplo\n'):
            with self.subTest(contents=contents[:20]):
                with self.assertRaises(ImproperlyConfigured):
                    load_site_config(self.config_file(contents))

    def test_invalid_email_and_date_are_rejected(self):
        for contents in (EXAMPLE.replace('correo_arco: ""', 'correo_arco: "inválido"'),
                         EXAMPLE.replace('fecha_actualizacion: ""', 'fecha_actualizacion: "2026-99-99"')):
            with self.assertRaises(ImproperlyConfigured):
                load_site_config(self.config_file(contents))

    def test_real_file_is_excluded_from_git_and_docker(self):
        for filename in ('.gitignore', '.dockerignore'):
            lines = (settings.BASE_DIR / filename).read_text(encoding='utf-8').splitlines()
            self.assertIn('/config.yaml', lines)
