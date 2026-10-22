import re
import uuid

from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import F
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from analytics.models import ProductEvent
from .forms import LeadMagnetForm
from .lead_magnet import (
    RESOURCE_FILENAME, RESOURCE_KEY, allowed_request, hash_token,
    issue_request, send_access_email, storage,
)
from .models import LeadMagnetAccess, LeadMagnetRequest
from .models import Consent


def resource_context(**extra):
    return {'available': storage.available(RESOURCE_KEY), **extra}


@require_http_methods(['GET', 'POST'])
def resource(request):
    if request.method == 'GET':
        ProductEvent.objects.create(kind='PAGE_VIEW', execution=uuid.uuid4())
        form = LeadMagnetForm()
    else:
        form = LeadMagnetForm(request.POST)
        if not storage.available(RESOURCE_KEY):
            return render(request, 'lead_magnet/resource.html', resource_context(
                form=form, blocked='El archivo definitivo aún no está disponible. No se enviará un enlace de descarga.'
            ), status=503)
        if form.is_valid():
            email = form.cleaned_data['email']
            if not allowed_request(email, request.META.get('REMOTE_ADDR', 'unknown')):
                form.add_error(None, 'Hay demasiadas solicitudes recientes. Intenta nuevamente más tarde.')
            else:
                claim, token = issue_request(
                    form.cleaned_data['name'], email, form.cleaned_data['commercial'],
                )
                send_access_email(claim, token, request)
                request.session['lead_magnet_claim'] = str(claim.execution)
                return redirect('lead_magnet_thanks')
    return render(request, 'lead_magnet/resource.html', resource_context(form=form))


@require_http_methods(['GET', 'POST'])
def thanks(request):
    execution = request.session.get('lead_magnet_claim')
    if not execution:
        return redirect('lead_magnet_resource')
    claim = LeadMagnetRequest.objects.filter(execution=execution).first()
    if not claim:
        return redirect('lead_magnet_resource')
    if request.method == 'POST' and claim.email_status == LeadMagnetRequest.EmailStatus.FAILED:
        if not storage.available(RESOURCE_KEY):
            return render(request, 'lead_magnet/thanks.html', {'claim': claim, 'blocked': True}, status=503)
        if not allowed_request(claim.lead.email, request.META.get('REMOTE_ADDR', 'unknown')):
            return render(request, 'lead_magnet/thanks.html', {'claim': claim, 'limited': True}, status=429)
        # Se emite un enlace nuevo al reintentar; el anterior queda invalidado.
        claim, token = issue_request(
            claim.name, claim.lead.email,
            Consent.objects.filter(lead=claim.lead, execution=claim.execution,
                                   purpose='commercial', granted=True).exists(),
        )
        send_access_email(claim, token, request)
        request.session['lead_magnet_claim'] = str(claim.execution)
        return redirect('lead_magnet_thanks')
    return render(request, 'lead_magnet/thanks.html', {'claim': claim})


@require_http_methods(['GET', 'POST'])
def access(request, token):
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
        raise Http404
    claim = LeadMagnetRequest.objects.filter(token_hash=hash_token(token), resource_key=RESOURCE_KEY).first()
    if not claim:
        raise Http404
    valid = claim.active and claim.expires_at > timezone.now() and claim.access_count < 3
    if request.method == 'GET':
        request.session[f'lm_operation_{claim.pk}'] = str(uuid.uuid4())
        response = render(request, 'lead_magnet/access.html', {
            'valid': valid, 'available': storage.available(RESOURCE_KEY),
            'remaining': max(0, 3 - claim.access_count),
            'operation': request.session[f'lm_operation_{claim.pk}'],
        }, status=200 if valid else 410)
        response['Cache-Control'] = 'no-store'
        # Chrome enviaría Origin: null al confirmar un formulario bajo no-referrer.
        # strict-origin conserva el origen para CSRF sin incluir el token de la URL.
        response['Referrer-Policy'] = 'strict-origin'
        return response
    operation = request.POST.get('operation', '')
    if operation != request.session.get(f'lm_operation_{claim.pk}'):
        return render(request, 'lead_magnet/access.html', {'valid': False, 'error': 'Esta operación ya no está disponible.'}, status=409)
    try:
        operation_id = uuid.UUID(operation)
    except ValueError:
        raise Http404
    if LeadMagnetAccess.objects.filter(operation=operation_id).exists():
        return render(request, 'lead_magnet/access.html', {'valid': False, 'error': 'La operación ya fue autorizada. Abre de nuevo el enlace para otro acceso.'}, status=409)
    if not storage.available(RESOURCE_KEY):
        return render(request, 'lead_magnet/access.html', {'valid': valid, 'available': False, 'error': 'El archivo no está disponible ahora.'}, status=503)
    try:
        resource_file = storage.open(RESOURCE_KEY)
    except OSError:
        return render(request, 'lead_magnet/access.html', {'valid': valid, 'available': False, 'error': 'El archivo no está disponible ahora.'}, status=503)
    try:
        with transaction.atomic():
            updated = LeadMagnetRequest.objects.filter(
                pk=claim.pk, active=True, expires_at__gt=timezone.now(),
                access_count__lt=3,
            ).update(access_count=F('access_count') + 1)
            if not updated:
                resource_file.close()
                return render(request, 'lead_magnet/access.html', {'valid': False, 'error': 'El enlace venció o agotó sus accesos.'}, status=410)
            LeadMagnetAccess.objects.create(operation=operation_id, request=claim)
            ProductEvent.objects.create(kind='LEADMAGNET_DELIVERED', execution=operation_id)
    except (IntegrityError, DatabaseError):
        resource_file.close()
        return render(request, 'lead_magnet/access.html', {'valid': False, 'error': 'No se pudo autorizar esta operación. Actualiza el enlace e inténtalo de nuevo.'}, status=409)
    response = FileResponse(resource_file, as_attachment=True, filename=RESOURCE_FILENAME,
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Cache-Control'] = 'no-store'
    response['Referrer-Policy'] = 'no-referrer'
    return response
