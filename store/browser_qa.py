"""Verificación visual aislada; ejecutar explícitamente, fuera de la suite habitual."""
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

from content.models import MediaAsset, PublicationStatus
from .models import DigitalProduct


class StoreBrowserQA(StaticLiveServerTestCase):
    def test_catalog_and_admin_in_browser(self):
        with TemporaryDirectory() as media_dir, override_settings(
            MEDIA_ROOT=media_dir, DEBUG=True, STORE_TEST_CHECKOUT_ENABLED=True,
        ):
            buffer = BytesIO()
            Image.new('RGB', (600, 360), '#16786e').save(buffer, format='PNG')
            image = MediaAsset.objects.create(
                name='Imagen sintética de producto', alt_text='Imagen sintética verde',
                image=SimpleUploadedFile('producto.png', buffer.getvalue(), content_type='image/png'),
            )
            DigitalProduct.objects.create(
                name='Producto sintético de QA', slug='producto-sintetico-qa', summary='Ficha ficticia para revisar la tienda.',
                description='Descripción exclusivamente de prueba.', benefits='Beneficio sintético verificable.',
                image=image, status=PublicationStatus.PUBLISHED, version='0.1',
                software_requirements='Software de prueba.', contents='Archivo sintético de prueba.',
                delivery_terms='Condiciones sintéticas de prueba.', price='499.00', currency='MXN',
                private_file_key='archivo-sintetico', stripe_environment='test',
                stripe_test_payment_url='https://buy.stripe.com/test_AbC123456789',
            )
            user = get_user_model().objects.create_user('qa-tienda', password=secrets.token_urlsafe(32), is_staff=True, is_superuser=True)
            device = TOTPDevice.objects.create(user=user, name='qa', confirmed=True)
            self.client.force_login(user)
            session = self.client.session
            session[DEVICE_ID_SESSION_KEY] = device.persistent_id
            session.save()
            env = os.environ.copy()
            env.update({
                'QA_ORIGIN': self.live_server_url,
                'QA_SESSION': self.client.cookies['sessionid'].value,
                'QA_OUTPUT': str(Path(__file__).resolve().parent.parent / 'qa_artifacts'),
            })
            script = Path(__file__).resolve().parent.parent / 'qa_artifacts' / 'b01_store_visual.cjs'
            result = subprocess.run(['node', str(script)], env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=90)
            self.assertEqual(result.returncode, 0, (result.stdout or '') + (result.stderr or ''))
            print(result.stdout.strip())
