"""Operaciones internas de B-02A. Ninguna confirma pagos ni concede entregas."""

import uuid
import re
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, connection, transaction
from django.db.models import Max, QuerySet
from django.utils import timezone

from content.models import PublicationStatus
from store.models import DigitalProduct, Order, OrderAuditEvent, PaymentAttempt, ProductFileVersion
from store.file_versions import verify_file_version, FileVersionError


class OrderConflict(ValueError):
    pass


class InvalidOrderOperation(ValueError):
    pass


def _reason_code(reason):
    if not isinstance(reason, str) or not re.fullmatch(r'[a-z0-9_]{0,80}', reason):
        raise InvalidOrderOperation('Usa un código de motivo saneado de hasta 80 caracteres.')
    return reason


def _minor_units(price):
    try:
        value = Decimal(price)
        minor = value * 100
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise InvalidOrderOperation('Precio inválido.') from exc
    if not value.is_finite() or minor <= 0 or minor != minor.to_integral_value():
        raise InvalidOrderOperation('El precio debe ser positivo y expresarse en centavos exactos.')
    return int(minor)


def _audit(order, *, subject, action, from_state='', to_state='', attempt=None,
           correlation_id=None, reason=''):
    return OrderAuditEvent.objects.create(
        order=order, attempt=attempt, operation_id=uuid.uuid4(), subject=subject,
        actor=OrderAuditEvent.Actor.SYSTEM, action=action, from_state=from_state,
        to_state=to_state, correlation_id=correlation_id, reason=reason,
    )


def _write_authorized_state(queryset, **fields):
    """Única salida ORM del bloqueo de QuerySet; se usa bajo atomic y bloqueo de fila."""
    if QuerySet.update(queryset, **fields) != 1:
        raise InvalidOrderOperation('La fila cambió durante la transición.')


def _audit_on_sqlite(order, **event):
    # En PostgreSQL el trigger inserta el evento en la misma sentencia de escritura.
    if connection.vendor != 'postgresql':
        _audit(order, **event)


def _same_intention(order, product_id, environment):
    if order.product_id != product_id or order.environment != environment:
        raise OrderConflict('La clave de creación ya corresponde a otra intención de compra.')
    return order


def get_order_by_creation_key(*, creation_key, product_id, environment):
    order = Order.objects.get(creation_key=creation_key)
    return _same_intention(order, product_id, environment)


def create_order(*, product_id, creation_key, environment):
    """Crea una orden por intención; repeticiones recuperan su snapshot original."""
    if environment not in DigitalProduct.StripeEnvironment.values:
        raise InvalidOrderOperation('Entorno inválido.')
    if not isinstance(creation_key, uuid.UUID):
        raise InvalidOrderOperation('La clave de creación debe ser UUID.')
    try:
        with transaction.atomic():
            existing = Order.objects.filter(creation_key=creation_key).first()
            if existing:
                return _same_intention(existing, product_id, environment)
            product = DigitalProduct.objects.select_for_update().get(pk=product_id)
            if (product.status != PublicationStatus.PUBLISHED
                    or not product.published_at or product.published_at > timezone.now()):
                raise InvalidOrderOperation('El producto no está publicado.')
            if product.currency != 'MXN' or product.stripe_environment != environment:
                raise InvalidOrderOperation('Moneda o entorno del producto incompatibles.')
            amount_minor = _minor_units(product.price)
            version = ProductFileVersion.objects.select_for_update().filter(
                pk=product.sellable_file_version_id, product=product, available_for_sale=True,
            ).first()
            if product.sellable_file_version_id and version is None:
                raise InvalidOrderOperation('La versión privada seleccionada no está apta para venta.')
            if version:
                try:
                    verify_file_version(version)
                except FileVersionError as exc:
                    raise InvalidOrderOperation(str(exc)) from exc
            order = Order.objects.create(
                creation_key=creation_key, product=product, environment=environment,
                product_name_snapshot=product.name, product_version_snapshot=product.version,
                amount_minor=amount_minor, currency='MXN',
                delivery_terms_snapshot=product.delivery_terms,
                stripe_product_id_snapshot=product.stripe_product_id,
                stripe_price_id_snapshot=product.stripe_price_id,
                file_key_snapshot=version.object_identifier if version else product.private_file_key,
                file_revision_snapshot=version.version_id if version else '',
                file_sha256_snapshot=version.sha256 if version else '',
                file_size_bytes_snapshot=version.size_bytes if version else None,
            )
            return order
    except IntegrityError:
        # La unicidad en DB decide la carrera entre conexiones concurrentes.
        existing = Order.objects.filter(creation_key=creation_key).first()
        if existing:
            return _same_intention(existing, product_id, environment)
        raise


def validate_order_transition(current, target):
    allowed = {
        Order.State.CREATED: {Order.State.AWAITING_PAYMENT, Order.State.CLOSED_UNPAID, Order.State.REVIEW},
        Order.State.AWAITING_PAYMENT: {Order.State.REVIEW},
        Order.State.PAID: {Order.State.REVIEW},
        Order.State.CLOSED_UNPAID: {Order.State.REVIEW},
        Order.State.REVIEW: set(),
    }
    if target not in allowed.get(current, set()):
        raise InvalidOrderOperation('Transición de orden no autorizada en B-02A.')


def validate_attempt_transition(current, target):
    allowed = {
        PaymentAttempt.State.PREPARED: {PaymentAttempt.State.EXPIRED, PaymentAttempt.State.REVIEW},
        PaymentAttempt.State.SESSION_OPEN: {PaymentAttempt.State.REVIEW},
        PaymentAttempt.State.PROCESSING: {PaymentAttempt.State.REVIEW},
        PaymentAttempt.State.SUCCEEDED: {PaymentAttempt.State.REVIEW},
        PaymentAttempt.State.FAILED: {PaymentAttempt.State.REVIEW},
        PaymentAttempt.State.EXPIRED: {PaymentAttempt.State.REVIEW},
        PaymentAttempt.State.REVIEW: set(),
    }
    if target not in allowed.get(current, set()):
        raise InvalidOrderOperation('Transición de intento no autorizada en B-02A.')


def prepare_payment_attempt(*, order_id, operation_id, provider_account_id,
                            request_idempotency_key):
    """Reserva un intento local sin crear Checkout Session ni contactar Stripe."""
    if not isinstance(operation_id, uuid.UUID) or not isinstance(request_idempotency_key, uuid.UUID):
        raise InvalidOrderOperation('Los identificadores de operación deben ser UUID.')
    if not provider_account_id or not provider_account_id.strip():
        raise InvalidOrderOperation('Se requiere la cuenta del proveedor.')
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        existing = PaymentAttempt.objects.filter(operation_id=operation_id).first()
        if existing:
            if (existing.order_id != order_id or existing.provider_account_id != provider_account_id
                    or existing.request_idempotency_key != request_idempotency_key):
                raise OrderConflict('La operación ya corresponde a otro intento.')
            return existing
        if order.state not in (Order.State.CREATED, Order.State.AWAITING_PAYMENT):
            raise InvalidOrderOperation('Solo se admiten intentos en órdenes abiertas.')
        if PaymentAttempt.objects.filter(order=order, state__in=PaymentAttempt.ACTIVE_STATES).exists():
            raise OrderConflict('La orden ya tiene un intento no terminal.')
        if PaymentAttempt.objects.filter(order=order, state=PaymentAttempt.State.REVIEW).exists():
            raise OrderConflict('Un intento requiere revisión antes de continuar.')
        if PaymentAttempt.objects.filter(order=order, state=PaymentAttempt.State.SUCCEEDED).exists():
            raise OrderConflict('La orden ya registra un intento exitoso.')
        number = (PaymentAttempt.objects.filter(order=order).aggregate(Max('attempt_number'))['attempt_number__max'] or 0) + 1
        attempt = PaymentAttempt.objects.create(
            order=order, operation_id=operation_id,
            request_idempotency_key=request_idempotency_key,
            attempt_number=number, provider_account_id=provider_account_id,
            environment=order.environment, amount_minor=order.amount_minor,
            currency=order.currency,
        )
        return attempt


def expire_prepared_attempt(*, attempt_id, reason=''):
    """Expira solo reservas locales sin sesión ni referencia de proveedor."""
    reason = _reason_code(reason)
    with transaction.atomic():
        order_id = PaymentAttempt.objects.values_list('order_id', flat=True).get(pk=attempt_id)
        order = Order.objects.select_for_update().get(pk=order_id)
        attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt_id)
        if attempt.state == PaymentAttempt.State.EXPIRED:
            return attempt
        if attempt.state != PaymentAttempt.State.PREPARED or attempt.checkout_session_id or attempt.payment_intent_id:
            raise InvalidOrderOperation('Solo puede expirar un intento local sin sesión.')
        validate_attempt_transition(attempt.state, PaymentAttempt.State.EXPIRED)
        prior = attempt.state
        attempt.state = PaymentAttempt.State.EXPIRED
        attempt.completed_at = timezone.now()
        attempt.result_code = reason or 'local_expired'
        _write_authorized_state(PaymentAttempt.objects.filter(pk=attempt.pk),
                                state=attempt.state, completed_at=attempt.completed_at,
                                result_code=attempt.result_code, updated_at=timezone.now())
        _audit_on_sqlite(order, subject=OrderAuditEvent.Subject.ATTEMPT, action='expired',
                         attempt=attempt, from_state=prior, to_state=attempt.state,
                         reason=attempt.result_code)
        return attempt


def close_unpaid_order(*, order_id, reason=''):
    """Cierra únicamente una orden sin sesión externa ni intento activo."""
    reason = _reason_code(reason)
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.state == Order.State.CLOSED_UNPAID:
            return order
        validate_order_transition(order.state, Order.State.CLOSED_UNPAID)
        if PaymentAttempt.objects.filter(order=order, state__in=PaymentAttempt.ACTIVE_STATES).exists():
            raise InvalidOrderOperation('Existe un intento no terminal.')
        if PaymentAttempt.objects.filter(order=order, state__in=[PaymentAttempt.State.REVIEW, PaymentAttempt.State.SUCCEEDED]).exists():
            raise InvalidOrderOperation('Existe un intento que impide cerrar sin pago.')
        if PaymentAttempt.objects.filter(order=order).exclude(checkout_session_id='').exists():
            raise InvalidOrderOperation('Existe una sesión externa.')
        if PaymentAttempt.objects.filter(order=order).exclude(payment_intent_id='').exists():
            raise InvalidOrderOperation('Existe una referencia de pago externa.')
        order.state = Order.State.CLOSED_UNPAID
        order.closed_at = timezone.now()
        order.closed_reason = reason
        _write_authorized_state(Order.objects.filter(pk=order.pk),
                                state=order.state, closed_at=order.closed_at,
                                closed_reason=order.closed_reason, updated_at=timezone.now())
        _audit_on_sqlite(order, subject=OrderAuditEvent.Subject.ORDER, action='closed_unpaid',
                         from_state=Order.State.CREATED, to_state=order.state, reason=reason)
        return order
