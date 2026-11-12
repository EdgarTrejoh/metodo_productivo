"""Preparación interna de Checkout con proveedor simulado; sin pagos."""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from store.checkout_provider import ProviderUncertain, SimulatedCheckoutProvider
from store.financial_provider import ProviderUnavailable
from store.file_versions import assert_order_checkout_ready
from store.models import CheckoutRequest, Order, OrderAuditEvent, PaymentAttempt
from store.order_services import (InvalidOrderOperation, OrderConflict,
    _write_authorized_state, _audit_on_sqlite, prepare_payment_attempt)


class CheckoutPending(ValueError):
    pass


@dataclass(frozen=True)
class CheckoutResult:
    attempt_id: int
    session_id: str
    url: str


def _mark_uncertain(*, request, order_id, attempt_id, operation_id):
    """Persiste la incertidumbre y su auditoría una sola vez."""
    with transaction.atomic():
        changed = CheckoutRequest.objects.select_for_update().filter(
            pk=request.pk, state=CheckoutRequest.State.CALLING).update(
                state=CheckoutRequest.State.UNCERTAIN)
        if changed:
            OrderAuditEvent.objects.create(order_id=order_id, attempt_id=attempt_id,
                operation_id=uuid.uuid4(), subject='attempt', actor='system',
                action='checkout_uncertain', correlation_id=operation_id)


def _return_url(origin, path):
    parsed = urlsplit(origin)
    if parsed.scheme not in ('https', 'http') or not parsed.netloc or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise InvalidOrderOperation('Origen de retorno inválido.')
    if parsed.scheme == 'http' and parsed.hostname not in ('localhost', '127.0.0.1', 'testserver'):
        raise InvalidOrderOperation('El retorno externo requiere HTTPS.')
    return origin + path


def start_checkout(*, order_id, operation_id, request_idempotency_key,
                   provider, return_origin):
    """Reserva, consulta y vincula sin mantener bloqueos durante el proveedor."""
    from store.stripe_test_provider import StripeTestProvider, StripeProviderDataError
    real_test = type(provider) is StripeTestProvider
    if type(provider) is not SimulatedCheckoutProvider and not (
            real_test and settings.STRIPE_TEST_ADAPTER_ENABLED):
        raise InvalidOrderOperation('Proveedor de Checkout no autorizado.')
    if not isinstance(operation_id, uuid.UUID) or not isinstance(request_idempotency_key, uuid.UUID):
        raise InvalidOrderOperation('La operación requiere UUID.')
    if not return_origin or return_origin != settings.CHECKOUT_RETURN_ORIGIN:
        raise InvalidOrderOperation('El retorno debe usar el origen configurado.')
    if real_test and urlsplit(return_origin).scheme != 'https':
        raise InvalidOrderOperation('Stripe TEST requiere retornos HTTPS.')
    success_url = _return_url(return_origin, '/tienda/resultado/?estado=pendiente')
    cancel_url = _return_url(return_origin, '/tienda/resultado/?estado=cancelado')
    order = assert_order_checkout_ready(order_id)
    if order.state not in (Order.State.CREATED, Order.State.AWAITING_PAYMENT):
        raise InvalidOrderOperation('La orden no admite otra sesión.')
    if not order.stripe_price_id_snapshot or not order.stripe_product_id_snapshot:
        raise InvalidOrderOperation('Faltan las referencias comerciales del precio.')
    if provider.account_id.strip() == '' or provider.environment != order.environment:
        raise InvalidOrderOperation('Cuenta o entorno incompatible.')
    try:
        price = provider.get_price(order.stripe_price_id_snapshot)
    except ProviderUnavailable as exc:
        raise CheckoutPending('El precio no está disponible temporalmente; reintenta la misma intención.') from exc
    except (KeyError, StripeProviderDataError) as exc:
        raise InvalidOrderOperation('El Price ID es desconocido o incompatible.') from exc
    if (price.price_id != order.stripe_price_id_snapshot
            or price.product_id != order.stripe_product_id_snapshot
            or price.amount_minor != order.amount_minor or price.currency.upper() != 'MXN'
            or price.account_id != provider.account_id or price.environment != order.environment
            or not price.active or price.recurring):
        raise InvalidOrderOperation('El precio no coincide con la orden y la cuenta.')
    params = dict(mode='payment', price_id=price.price_id, quantity=1,
                  payment_method_types=('card',),
                  success_url=success_url, cancel_url=cancel_url,
                  client_reference_id=str(order.public_id), operation_id=operation_id)
    digest = hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()
    attempt = prepare_payment_attempt(order_id=order_id, operation_id=operation_id,
        provider_account_id=provider.account_id, request_idempotency_key=request_idempotency_key)
    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(pk=order_id)
        locked_attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        request, created = CheckoutRequest.objects.select_for_update().get_or_create(
            attempt=locked_attempt, defaults={'parameters_sha256': digest})
        if request.parameters_sha256 != digest:
            raise OrderConflict('La misma operación recibió parámetros diferentes.')
        bound_session_id = request.session_id if request.state == CheckoutRequest.State.BOUND else None
        if created:
            OrderAuditEvent.objects.create(order=locked_order, attempt=locked_attempt,
                operation_id=uuid.uuid4(), subject='attempt', actor='system',
                action='checkout_requested', correlation_id=operation_id)
    # Otro hilo puede seguir llamando al proveedor. La clave remota es estable.
    try:
        session = provider.get_session(idempotency_key=str(request_idempotency_key),
            session_id=bound_session_id, expected=params)
    except ProviderUnavailable as exc:
        if not bound_session_id:
            _mark_uncertain(request=request, order_id=order_id,
                attempt_id=attempt.pk, operation_id=operation_id)
        raise CheckoutPending('La consulta de la sesión no está disponible; requiere conciliación.') from exc
    if bound_session_id:
        if (session is None or session.session_id != bound_session_id
                or session.status != 'open' or session.expires_at <= timezone.now()):
            raise CheckoutPending('La sesión vinculada requiere conciliación.')
        return CheckoutResult(attempt.pk, session.session_id, session.url)
    if session is None:
        if not created:
            elapsed = timezone.now() - request.started_at
            if not real_test or (request.state == CheckoutRequest.State.CALLING
                    and elapsed < timedelta(seconds=30)):
                raise CheckoutPending('La operación anterior aún no tiene respuesta verificable.')
            if elapsed >= timedelta(hours=23):
                raise CheckoutPending('La ventana de reintento remoto terminó; requiere conciliación.')
            if request.state == CheckoutRequest.State.CALLING:
                _mark_uncertain(request=request, order_id=order_id,
                    attempt_id=attempt.pk, operation_id=operation_id)
        try:
            session = provider.create_session(idempotency_key=str(request_idempotency_key), **params)
        except ProviderUncertain as exc:
            _mark_uncertain(request=request, order_id=order_id,
                attempt_id=attempt.pk, operation_id=operation_id)
            raise CheckoutPending('La respuesta se perdió; se requiere conciliación.') from exc
        except Exception as exc:
            _mark_uncertain(request=request, order_id=order_id,
                attempt_id=attempt.pk, operation_id=operation_id)
            raise CheckoutPending('El resultado del proveedor es incierto.') from exc
    if (session.account_id != provider.account_id or session.environment != order.environment
            or session.status != 'open' or session.expires_at <= timezone.now()):
        raise CheckoutPending('La sesión requiere conciliación antes de continuar.')
    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(pk=order_id)
        locked_attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        request = CheckoutRequest.objects.select_for_update().get(pk=request.pk)
        if locked_order.state not in (Order.State.CREATED, Order.State.AWAITING_PAYMENT):
            raise InvalidOrderOperation('La orden cambió durante Checkout.')
        if request.state == CheckoutRequest.State.BOUND:
            if request.session_id != session.session_id:
                raise OrderConflict('La operación apunta a otra sesión.')
            return CheckoutResult(attempt.pk, session.session_id, session.url)
        request.state = CheckoutRequest.State.BOUND
        request.session_id = session.session_id
        request.session_expires_at = session.expires_at
        request.save(update_fields=['state', 'session_id', 'session_expires_at', 'updated_at'])
        if locked_attempt.state != PaymentAttempt.State.PREPARED:
            raise InvalidOrderOperation('El intento cambió durante Checkout.')
        _write_authorized_state(PaymentAttempt.objects.filter(pk=attempt.pk),
            state=PaymentAttempt.State.SESSION_OPEN, checkout_session_id=session.session_id,
            bound_at=timezone.now(), updated_at=timezone.now())
        _audit_on_sqlite(locked_order, subject='attempt', action='session_open',
            attempt=locked_attempt, from_state='prepared', to_state='session_open',
            correlation_id=operation_id)
        if locked_order.state == Order.State.CREATED:
            _write_authorized_state(Order.objects.filter(pk=order_id),
                state=Order.State.AWAITING_PAYMENT, updated_at=timezone.now())
            _audit_on_sqlite(locked_order, subject='order', action='awaiting_payment',
                from_state='created', to_state='awaiting_payment', correlation_id=operation_id)
    return CheckoutResult(attempt.pk, session.session_id, session.url)
