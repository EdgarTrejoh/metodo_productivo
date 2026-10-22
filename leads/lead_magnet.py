"""Entrega privada del primer recurso; el archivo se resuelve por clave lógica."""
import hashlib
import secrets
import zipfile
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from analytics.models import ProductEvent
from .models import Consent, Lead, LeadMagnetRequest


RESOURCE_KEY = 'mapa-de-caja-pyme-v0.3'
RESOURCE_FILENAME = 'Mapa_de_Caja_PyME_v0.3.xlsx'
TEXT_VERSION = 'demo-local-d06-v0.1-no-legal'


class PrivateResourceStorage:
    """Interfaz mínima: sustituible por un adaptador privado de O-03."""

    def path_for(self, key):
        if key != RESOURCE_KEY:
            raise ValueError('Recurso desconocido')
        return Path(settings.PRIVATE_RESOURCE_ROOT) / RESOURCE_FILENAME

    def available(self, key):
        path = self.path_for(key)
        if not path.is_file():
            return False
        try:
            with zipfile.ZipFile(path) as workbook:
                names = set(workbook.namelist())
                return '[Content_Types].xml' in names and 'xl/workbook.xml' in names
        except (OSError, zipfile.BadZipFile):
            return False

    def open(self, key):
        return self.path_for(key).open('rb')


storage = PrivateResourceStorage()


def hash_token(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def allowed_request(email, ip):
    """Límite local básico; O-07 definirá un control compartido."""
    email_key = hashlib.sha256(email.encode('utf-8')).hexdigest()
    ip_key = hashlib.sha256(ip.encode('utf-8')).hexdigest()
    for key, limit in ((f'lm-email-{email_key}', 5), (f'lm-ip-{ip_key}', 20)):
        if cache.add(key, 1, timeout=3600):
            continue
        try:
            if cache.incr(key) > limit:
                return False
        except ValueError:
            cache.set(key, 1, timeout=3600)
    return True


def issue_request(name, email, commercial):
    token = secrets.token_urlsafe(32)
    now = timezone.now()
    with transaction.atomic():
        lead = Lead.objects.select_for_update().filter(email__iexact=email).order_by('pk').first()
        created = lead is None
        if created:
            try:
                with transaction.atomic():
                    lead = Lead.objects.create(email=email)
            except IntegrityError:
                lead = Lead.objects.select_for_update().get(email=email)
                created = False
        LeadMagnetRequest.objects.filter(lead=lead, resource_key=RESOURCE_KEY, active=True).update(active=False)
        claim = LeadMagnetRequest.objects.create(
            lead=lead, resource_key=RESOURCE_KEY, name=name,
            token_hash=hash_token(token), issued_at=now,
            expires_at=now + timedelta(hours=72),
        )
        Consent.objects.create(lead=lead, execution=claim.execution, purpose='service', granted=True, text_version=TEXT_VERSION)
        Consent.objects.create(lead=lead, execution=claim.execution, purpose='commercial', granted=commercial, text_version=TEXT_VERSION)
        if created:
            ProductEvent.objects.create(kind='LEAD_CREATED', execution=claim.execution)
    return claim, token


def send_access_email(claim, token, request):
    link = request.build_absolute_uri(reverse('lead_magnet_access', args=[token]))
    body = (
        f'Hola, {claim.name}.\n\n'
        'Gracias por solicitar la plantilla de flujo de efectivo de 13 semanas de Método Productivo.\n'
        f'Para acceder al archivo, abre este enlace: {link}\n\n'
        'El enlace estará disponible durante 3 días y permite hasta tres accesos autorizados.\n'
        'Si no solicitaste el recurso, puedes ignorar este mensaje.'
    )
    try:
        accepted = send_mail(
            'Tu plantilla gratuita de flujo de efectivo de 13 semanas', body,
            settings.DEFAULT_FROM_EMAIL, [claim.lead.email], fail_silently=False,
        )
        if accepted != 1:
            raise RuntimeError('Correo no aceptado por el backend local')
    except Exception:
        claim.email_status = LeadMagnetRequest.EmailStatus.FAILED
        ProductEvent.objects.get_or_create(kind='EMAIL_FAILED', execution=claim.execution)
    else:
        claim.email_status = LeadMagnetRequest.EmailStatus.SENT
    claim.save(update_fields=['email_status'])
    return claim.email_status == LeadMagnetRequest.EmailStatus.SENT
