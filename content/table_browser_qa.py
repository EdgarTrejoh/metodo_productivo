"""Recorrido visual aislado de tablas; ejecutar esta prueba explícitamente."""

import os
import secrets
import subprocess
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice

from .models import Article, PublicationStatus


class TableBrowserQA(StaticLiveServerTestCase):
    def test_table_editor_roundtrip(self):
        user = get_user_model().objects.create_user(
            'qa-tablas', password=secrets.token_urlsafe(32), is_staff=True, is_superuser=True,
        )
        device = TOTPDevice.objects.create(user=user, name='qa', confirmed=True)
        self.client.force_login(user)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        headings = ''.join(f'<th scope="col">Columna {number}</th>' for number in range(1, 9))
        values = ''.join(f'<td>Dato {number}</td>' for number in range(1, 9))
        Article.objects.create(
            title='PRUEBA — Tabla ancha', slug='prueba-tabla-ancha',
            summary='Tabla sintética de ocho columnas.',
            body=f'<p>Texto de referencia.</p><table><thead><tr>{headings}</tr></thead><tbody><tr>{values}</tr></tbody></table>',
            category=Article.Category.DATA, cta_target=Article.Cta.TOOLS,
            status=PublicationStatus.PUBLISHED, published_at=timezone.now(),
        )
        environment = os.environ.copy()
        environment.update({
            'QA_ORIGIN': self.live_server_url,
            'QA_SESSION': self.client.cookies['sessionid'].value,
            'QA_OUTPUT': str(Path(__file__).resolve().parent.parent / 'qa_artifacts'),
        })
        script = Path(__file__).resolve().parent.parent / 'qa_artifacts' / 'a05_table_browser.cjs'
        result = subprocess.run(
            ['node', str(script)], env=environment, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=120,
        )
        self.assertEqual(result.returncode, 0, (result.stdout or '') + (result.stderr or ''))
        print(result.stdout.strip())
