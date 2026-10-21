"""Recorrido visual aislado de la bandeja A-07; ejecución explícita."""

import os
import secrets
import subprocess
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice

from .models import ContactSubmission


class ContactInboxBrowserQA(StaticLiveServerTestCase):
    def test_inbox_in_browser(self):
        user = get_user_model().objects.create_user(
            'qa-bandeja', password=secrets.token_urlsafe(32), is_staff=True, is_superuser=True,
        )
        device = TOTPDevice.objects.create(user=user, name='qa', confirmed=True)
        self.client.force_login(user)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        ContactSubmission.objects.create(
            category='comment', message='Comentario sintético completo para comprobar el detalle.',
            name='Remitente de prueba', email='comentario@example.invalid',
        )
        ContactSubmission.objects.create(
            category='request', message='Solicitud sintética para seguimiento.',
            name='Solicitante de prueba', email='solicitud@example.invalid',
            status=ContactSubmission.Status.REVIEWING, internal_note='Nota de prueba.',
        )
        ContactSubmission.objects.create(
            category='comment', message='Comentario sintético ya cerrado.',
            name='Otra persona de prueba', email='cerrado@example.invalid',
            status=ContactSubmission.Status.CLOSED,
        )
        environment = os.environ.copy()
        environment.update({
            'QA_ORIGIN': self.live_server_url,
            'QA_SESSION': self.client.cookies['sessionid'].value,
            'QA_OUTPUT': str(Path(__file__).resolve().parent.parent / 'qa_artifacts'),
        })
        script = Path(__file__).resolve().parent.parent / 'qa_artifacts' / 'a07_inbox_browser.cjs'
        result = subprocess.run(
            ['node', str(script)], env=environment, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=90,
        )
        self.assertEqual(result.returncode, 0, (result.stdout or '') + (result.stderr or ''))
        print(result.stdout.strip())
