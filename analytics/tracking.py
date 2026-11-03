"""Medición local de navegación; no contiene datos de formularios ni URLs completas."""
import hashlib
import logging
import uuid
from urllib.parse import urlsplit

from django.conf import settings
from django.db import DatabaseError
from django.urls import Resolver404, resolve
from django.utils import timezone

from .models import TrafficEvent, TrafficSession

logger = logging.getLogger(__name__)

PUBLIC_PAGES = frozenset({
    'home', 'tools', 'break_even', 'resources', 'lead_magnet_resource',
    'blog', 'article_detail', 'store', 'store_detail', 'contact',
    'about', 'privacy', 'terms', 'entry',
})
HOME_CTAS = frozenset({'explore', 'tools', 'content', 'check', 'resources'})
BOT_MARKERS = ('bot', 'crawler', 'spider', 'headless')


def _session(request):
    identifier = request.session.get('traffic_session_id')
    if identifier:
        session = TrafficSession.objects.filter(pk=identifier).first()
        if session:
            reason = _exclusion_reason(request)
            if reason and not session.excluded_reason:
                TrafficSession.objects.filter(pk=session.pk).update(excluded_reason=reason)
                session.excluded_reason = reason
            return session
    session = TrafficSession.objects.create(environment=settings.DJANGO_ENV, excluded_reason=_exclusion_reason(request))
    request.session['traffic_session_id'] = str(session.pk)
    return session


def _exclusion_reason(request):
    if request.user.is_authenticated and request.user.is_staff:
        return 'internal'
    if any(marker in request.META.get('HTTP_USER_AGENT', '').lower() for marker in BOT_MARKERS):
        return 'bot'
    return ''


def _referer_page(request):
    try:
        referer = urlsplit(request.META.get('HTTP_REFERER', ''))
        same_origin = referer.scheme == request.scheme and referer.netloc == request.get_host()
    except (ValueError, UnicodeError):
        return None
    if not same_origin:
        return None
    try:
        match = resolve(referer.path)
    except (Resolver404, ValueError, UnicodeError):
        return None
    return _page_key(match)


def _page_key(match):
    if match is None or match.url_name not in PUBLIC_PAGES:
        return None
    if match.url_name in ('article_detail', 'store_detail'):
        # El slug público distingue fichas; su hash evita almacenar texto de la URL.
        slug = match.kwargs.get('slug', '')
        digest = hashlib.sha256(slug.encode('utf-8')).hexdigest()[:32]
        return f'{match.url_name}:{digest}'
    return match.url_name


def record_page(request, response):
    if request.method != 'GET' or response.status_code != 200:
        return
    if request.resolver_match is None or request.resolver_match.url_name not in PUBLIC_PAGES:
        return
    if not response.get('Content-Type', '').startswith('text/html'):
        return
    if request.headers.get('Sec-Fetch-Dest', 'document') != 'document':
        return
    if request.headers.get('Purpose', '').lower() == 'prefetch' or request.headers.get('Sec-Purpose', '').lower() == 'prefetch':
        return
    try:
        page = _page_key(request.resolver_match)
        previous = _referer_page(request)
        if previous == page:  # Recarga de la misma ruta, sin nueva navegación.
            return
        session = _session(request)
        effective = bool(previous and session.events.filter(kind='PAGE_VIEW', page=previous).exists())
        TrafficEvent.objects.create(kind='PAGE_VIEW', session=session, page=page, effective_navigation=effective)
        if effective and session.qualified_at is None:
            TrafficSession.objects.filter(pk=session.pk, qualified_at__isnull=True).update(qualified_at=timezone.now())
    except (DatabaseError, AssertionError):
        logger.warning('No se pudo registrar la navegación pública.')


def record_cta(request, cta, operation):
    if cta not in HOME_CTAS:
        return False
    try:
        operation_id = uuid.UUID(operation)
    except (ValueError, TypeError, AttributeError):
        return False
    try:
        session = _session(request)
        event, _ = TrafficEvent.objects.get_or_create(
            operation=operation_id,
            defaults={'kind': 'CTA_CLICK', 'session': session, 'page': 'home', 'cta': cta},
        )
        return (event.kind == 'CTA_CLICK' and event.session_id == session.pk
                and event.page == 'home' and event.cta == cta)
    except (DatabaseError, AssertionError):
        logger.warning('No se pudo registrar el CTA.')
    return True  # La medición fallida no interrumpe el enlace público.


def record_tool(request, execution):
    try:
        session = _session(request)
        event, _ = TrafficEvent.objects.get_or_create(
            operation=execution,
            defaults={'kind': 'TOOL_STARTED', 'session': session, 'page': 'break_even'},
        )
        if event.kind != 'TOOL_STARTED' or event.session_id != session.pk or event.page != 'break_even' or event.cta:
            return
        if session.qualified_at is None:
            TrafficSession.objects.filter(pk=session.pk, qualified_at__isnull=True).update(qualified_at=timezone.now())
    except (DatabaseError, AssertionError):
        logger.warning('No se pudo asociar la interacción de la calculadora a la sesión.')
