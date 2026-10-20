"""QA visual opcional; ejecutar explícitamente, fuera de la suite Django habitual."""

import os
import secrets
import subprocess
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice

from .models import MediaAsset


class EditorBrowserQA(StaticLiveServerTestCase):
    def test_editor_and_library_in_browser(self):
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            user = get_user_model().objects.create_user(
                'qa-editor', password=secrets.token_urlsafe(32), is_staff=True, is_superuser=True,
            )
            device = TOTPDevice.objects.create(user=user, name='qa', confirmed=True)
            self.client.force_login(user)
            session = self.client.session
            session[DEVICE_ID_SESSION_KEY] = device.persistent_id
            session.save()
            buffer = BytesIO()
            Image.new('RGB', (180, 100), '#007f72').save(buffer, format='PNG')
            media = MediaAsset.objects.create(
                name='PRUEBA — Gráfico editorial', alt_text='Gráfico sintético de prueba',
                image=SimpleUploadedFile('grafico.png', buffer.getvalue(), content_type='image/png'),
            )
            environment = os.environ.copy()
            environment.update({
                'QA_ORIGIN': self.live_server_url,
                'QA_SESSION': self.client.cookies['sessionid'].value,
                'QA_MEDIA_ID': str(media.pk),
                'QA_OUTPUT': str(Path(__file__).resolve().parent.parent / 'qa_artifacts'),
            })
            script = Path(__file__).resolve().parent.parent / 'qa_artifacts' / 'a05_editor_browser.cjs'
            result = subprocess.run(['node', str(script)], env=environment, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=90)
            self.assertEqual(result.returncode, 0, (result.stdout or '') + (result.stderr or ''))
            print(result.stdout.strip())
