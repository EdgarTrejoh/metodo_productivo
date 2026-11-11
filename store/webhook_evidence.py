"""Recepción durable de eventos sintéticos compatibles con Stripe; sin pagos."""

import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone as dt_timezone

from django.db import DatabaseError, transaction
from django.db.models import F, Q
from django.http import HttpResponse
from django.utils import timezone

from store.models import CheckoutRequest, Order, PaymentAttempt, PaymentProviderEvent


SUPPORTED_TYPES = frozenset({
    'checkout.session.completed', 'checkout.session.async_payment_succeeded',
    'checkout.session.async_payment_failed', 'checkout.session.expired',
})
MAX_BODY_BYTES = 64 * 1024
MAX_AGE_SECONDS = 300


class InvalidWebhook(ValueError):
    pass


@dataclass(frozen=True)
class WebhookEndpointConfig:
    account_id: str
    environment: str
    signing_secret: str


def verify_signature(raw_body, signature_header, secret, *, now=None):
    """Stripe v1: HMAC-SHA256 de timestamp + punto + cuerpo original."""
    if not isinstance(raw_body, bytes) or not raw_body or len(raw_body) > MAX_BODY_BYTES:
        raise InvalidWebhook('invalid_body')
    if not signature_header or not secret:
        raise InvalidWebhook('missing_signature')
    parts = [part.strip().split('=', 1) for part in signature_header.split(',')]
    if any(len(part) != 2 for part in parts):
        raise InvalidWebhook('invalid_signature_header')
    timestamps = [value for key, value in parts if key == 't']
    signatures = [value for key, value in parts if key == 'v1']
    if len(timestamps) != 1 or not signatures:
        raise InvalidWebhook('invalid_signature_header')
    try:
        timestamp = int(timestamps[0])
    except ValueError as exc:
        raise InvalidWebhook('invalid_signature_header') from exc
    current = int((now or timezone.now()).timestamp())
    if abs(current - timestamp) > MAX_AGE_SECONDS:
        raise InvalidWebhook('signature_outside_tolerance')
    expected = hmac.new(secret.encode(), str(timestamp).encode() + b'.' + raw_body,
                        hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(value, expected) for value in signatures):
        raise InvalidWebhook('invalid_signature')


def _uuid(value):
    try:
        return uuid.UUID(str(value)) if value else None
    except (ValueError, TypeError, AttributeError):
        return None


def parse_event(raw_body, config):
    try:
        event = json.loads(raw_body)
        obj = event['data']['object']
        event_id = event['id']
        event_type = event['type']
        object_id = obj['id']
        created = event['created']
    except (ValueError, KeyError, TypeError) as exc:
        raise InvalidWebhook('malformed_event') from exc
    if (not isinstance(event, dict) or not isinstance(obj, dict)
            or not all(isinstance(value, str) and 0 < len(value) <= limit
                       for value, limit in ((event_id, 255), (event_type, 100), (object_id, 255)))
            or not isinstance(created, int) or isinstance(created, bool)
            or not isinstance(event.get('livemode'), bool)):
        raise InvalidWebhook('malformed_event')
    if config.environment not in ('test', 'live') or not config.account_id:
        raise InvalidWebhook('invalid_endpoint_config')
    if event['livemode'] != (config.environment == 'live'):
        raise InvalidWebhook('wrong_environment')
    if event.get('account') not in (None, config.account_id):
        raise InvalidWebhook('wrong_account')
    try:
        created_at = datetime.fromtimestamp(created, tz=dt_timezone.utc)
    except (ValueError, OverflowError, OSError) as exc:
        raise InvalidWebhook('invalid_event_time') from exc
    metadata = obj.get('metadata') or {}
    if not isinstance(metadata, dict):
        raise InvalidWebhook('malformed_event')
    amount = obj.get('amount_total')
    if amount is not None and (not isinstance(amount, int) or isinstance(amount, bool) or amount < 0):
        raise InvalidWebhook('malformed_event')
    if any(value is not None and not isinstance(value, str) for value in
           (obj.get('payment_intent'), obj.get('currency'), obj.get('payment_status'))):
        raise InvalidWebhook('malformed_event')
    return dict(provider='stripe', provider_account_id=config.account_id,
        environment=config.environment, external_event_id=event_id,
        event_type=event_type, external_object_id=object_id,
        raw_sha256=hashlib.sha256(raw_body).hexdigest(), provider_created_at=created_at,
        verified_at=timezone.now(), claimed_operation_id=_uuid(metadata.get('operation_id')),
        claimed_order_public_id=_uuid(obj.get('client_reference_id')),
        claimed_payment_intent_id=(obj.get('payment_intent') or '')[:255],
        claimed_amount_minor=amount, claimed_currency=(obj.get('currency') or '')[:3].upper(),
        claimed_payment_status=(obj.get('payment_status') or '')[:24])


def _classification(record):
    if record.event_type not in SUPPORTED_TYPES:
        return None, None, 'unsupported_event'
    session_attempt = PaymentAttempt.objects.filter(checkout_session_id=record.external_object_id).first()
    attempt = session_attempt
    if attempt is None and record.claimed_operation_id:
        attempt = PaymentAttempt.objects.filter(operation_id=record.claimed_operation_id).first()
    if attempt is None:
        return None, None, 'unknown_session'
    order = Order.objects.get(pk=attempt.order_id)
    if (attempt.provider_account_id != record.provider_account_id
            or attempt.environment != record.environment or order.environment != record.environment):
        return order, attempt, 'account_or_environment_mismatch'
    if record.claimed_order_public_id and record.claimed_order_public_id != order.public_id:
        return order, attempt, 'order_mismatch'
    if record.claimed_operation_id and record.claimed_operation_id != attempt.operation_id:
        return order, attempt, 'operation_mismatch'
    if record.claimed_amount_minor is not None and record.claimed_amount_minor != order.amount_minor:
        return order, attempt, 'amount_mismatch'
    if record.claimed_currency and record.claimed_currency != order.currency:
        return order, attempt, 'currency_mismatch'
    request = CheckoutRequest.objects.filter(attempt=attempt).first()
    if (attempt.checkout_session_id and attempt.checkout_session_id != record.external_object_id
            or request and request.session_id and request.session_id != record.external_object_id):
        return order, attempt, 'session_mismatch'
    if not request or request.state != CheckoutRequest.State.BOUND:
        return order, attempt, 'await_session_binding'
    if record.event_type == 'checkout.session.completed' and record.claimed_payment_status != 'paid':
        return order, attempt, 'payment_pending'
    return order, attempt, 'provider_requery_required'


CONTRADICTIONS = frozenset({'account_or_environment_mismatch', 'order_mismatch',
    'operation_mismatch', 'amount_mismatch', 'currency_mismatch', 'session_mismatch',
    'event_payload_conflict'})


def receive_authenticated_event(raw_body, signature_header, config):
    verify_signature(raw_body, signature_header, config.signing_secret)
    fields = parse_event(raw_body, config)
    with transaction.atomic():
        record, created = PaymentProviderEvent.objects.select_for_update().get_or_create(
            provider=fields['provider'], provider_account_id=fields['provider_account_id'],
            environment=fields['environment'], external_event_id=fields['external_event_id'],
            defaults=fields)
        if not created:
            if record.raw_sha256 != fields['raw_sha256']:
                PaymentProviderEvent.objects.filter(pk=record.pk).update(
                    state=PaymentProviderEvent.State.CONTRADICTION,
                    reason_code='event_payload_conflict', conflict_count=F('conflict_count') + 1)
                return record, 'conflict'
            return record, 'duplicate'
        order, attempt, reason = _classification(record)
        PaymentProviderEvent.objects.filter(pk=record.pk).update(
            order=order, attempt=attempt, reason_code=reason,
            state=(PaymentProviderEvent.State.CONTRADICTION if reason in CONTRADICTIONS
                   else PaymentProviderEvent.State.PENDING))
        record.refresh_from_db()
        return record, 'created'


def retry_pending_event(event_id):
    """Consulta filas durables tras un reinicio; no llama al proveedor ni confirma pagos."""
    with transaction.atomic():
        record = PaymentProviderEvent.objects.select_for_update().get(pk=event_id)
        if record.state != PaymentProviderEvent.State.PENDING:
            return record
        order, attempt, reason = _classification(record)
        PaymentProviderEvent.objects.filter(pk=record.pk).update(
            order=order, attempt=attempt, reason_code=reason,
            state=(PaymentProviderEvent.State.CONTRADICTION if reason in CONTRADICTIONS
                   else PaymentProviderEvent.State.PENDING),
            retry_count=F('retry_count') + 1, last_attempt_at=timezone.now())
        record.refresh_from_db()
        return record


def assert_no_unresolved_contradiction(attempt_id):
    """Condición futura de B-03D; no confirma ni concede nada."""
    attempt = PaymentAttempt.objects.get(pk=attempt_id)
    if PaymentProviderEvent.objects.filter(state=PaymentProviderEvent.State.CONTRADICTION,
            provider=attempt.provider).filter(
                Q(attempt=attempt) | Q(external_object_id=attempt.checkout_session_id)).exists():
        raise InvalidWebhook('unresolved_contradiction')


def receive_webhook_http(request, config):
    """Vista interna sin registro URL; solo confirma una inserción durable."""
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        _, result = receive_authenticated_event(request.body,
            request.headers.get('Stripe-Signature'), config)
    except InvalidWebhook:
        return HttpResponse(status=400)
    except DatabaseError:
        return HttpResponse(status=503)
    return HttpResponse(status=409 if result == 'conflict' else 200)
