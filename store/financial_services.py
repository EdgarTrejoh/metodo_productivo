"""Conciliación B-03D local con proveedor simulado y rol SQL separado."""

import uuid
from dataclasses import dataclass
from datetime import timedelta, timezone as dt_timezone

from django.db import connection, models
from django.utils import timezone

from store.file_versions import (FileVersionMismatch, FileVersionTransientError,
                                 FileVersionUnavailable, verify_file_version)
from store.financial_provider import SimulatedFinancialProvider, SimulatedProviderUnavailable
from store.models import (CheckoutRequest, DeliveryEntitlement, FinancialVerification, Order,
                          PaymentAttempt, PaymentProviderEvent, ProductFileVersion)


class FinancialConflict(ValueError):
    pass


@dataclass(frozen=True)
class ReconciliationResult:
    state: str
    verification_id: int | None = None
    entitlement_id: int | None = None
    reason: str = ''


def _same_datetime(value):
    return value is not None and timezone.is_aware(value)


def _provider_facts(order, attempt, request, provider):
    if provider.account_id != attempt.provider_account_id or provider.environment != 'test':
        raise FinancialConflict('provider_account_or_environment')
    session = provider.get_session(request.session_id)
    intent = provider.get_intent(session.payment_intent_id)
    lines = provider.get_all_lines(session.id)
    if (session.id != request.session_id or session.id != attempt.checkout_session_id
            or session.account_id != attempt.provider_account_id
            or session.environment != order.environment
            or session.client_reference_id != str(order.public_id)
            or session.mode != 'payment' or session.status != 'complete'
            or session.amount_total != order.amount_minor
            or session.currency.upper() != 'MXN'
            or session.amount_discount != 0 or session.amount_tax != 0
            or session.amount_shipping != 0
            or intent.id != session.payment_intent_id
            or intent.account_id != session.account_id
            or intent.environment != session.environment
            or intent.amount != order.amount_minor
            or intent.currency.upper() != 'MXN'
            or len(lines) != 1 or lines[0].quantity != 1
            or lines[0].price_id != order.stripe_price_id_snapshot
            or lines[0].product_id != order.stripe_product_id_snapshot
            or lines[0].amount_total != order.amount_minor
            or lines[0].currency.upper() != 'MXN'):
        raise FinancialConflict('provider_purchase_mismatch')
    if (session.payment_status == 'paid') != (intent.status == 'succeeded'):
        raise FinancialConflict('payment_status_mismatch')
    if session.payment_status != 'paid' or intent.status != 'succeeded':
        return session, intent, lines[0], None, 'payment_pending'
    if (intent.capture_method != 'automatic'
            or intent.amount_received != order.amount_minor):
        raise FinancialConflict('capture_or_received_mismatch')
    events = provider.find_success_events(intent.id)
    if len(events) > 1:
        raise FinancialConflict('multiple_success_events')
    if not events:
        return session, intent, lines[0], None, 'missing_success_event'
    event = events[0]
    if (not event.id or event.type != 'payment_intent.succeeded'
            or event.object_id != intent.id
            or event.account_id != attempt.provider_account_id
            or event.environment != order.environment
            or not _same_datetime(event.created)
            or event.created.microsecond != 0
            or not _same_datetime(session.created)
            or not _same_datetime(intent.created)
            or event.created < session.created
            or event.created < intent.created
            or event.created > timezone.now() + timedelta(minutes=5)):
        raise FinancialConflict('success_event_mismatch')
    return session, intent, lines[0], event, ''


def _file_status(order):
    version = ProductFileVersion.objects.filter(product_id=order.product_id,
        object_identifier=order.file_key_snapshot,
        version_id=order.file_revision_snapshot,
        sha256=order.file_sha256_snapshot,
        size_bytes=order.file_size_bytes_snapshot).first()
    if version is None:
        return 'review', 'file_identity_missing'
    try:
        verify_file_version(version)
    except (FileVersionUnavailable, FileVersionTransientError):
        return 'pending_delivery', 'file_temporarily_unavailable'
    except FileVersionMismatch:
        return 'review', 'file_identity_mismatch'
    return 'ready', ''


def _record_review(order, attempt, request, finance_connection, reason):
    """Conserva una contradicción saneada sin afirmar que el proveedor pagó."""
    source_key = uuid.uuid5(uuid.NAMESPACE_URL,
        f'b03d-review|{attempt.provider_account_id}|{order.environment}|'
        f'{request.session_id}|{attempt.operation_id}|{reason}')
    try:
        with finance_connection.cursor() as cursor:
            cursor.execute("""SELECT public.store_b03d_record(
                %s::uuid,%s::bigint,%s::bigint,NULL::bigint,%s,%s,%s,%s,%s,
                NULL::timestamptz,%s::bigint,%s,%s,%s,%s::integer,%s,%s)""",
                (str(source_key), order.pk, attempt.pk, attempt.provider_account_id,
                 order.environment, request.session_id, 'unverified', '',
                 order.amount_minor, order.currency, order.stripe_price_id_snapshot,
                 order.stripe_product_id_snapshot, 1, 'review', reason))
            verification_id = cursor.fetchone()[0]
        finance_connection.commit()
    except Exception:
        finance_connection.rollback()
        raise
    return ReconciliationResult('review', verification_id, reason=reason)


def reconcile_simulated_payment(*, order_id, provider, finance_connection, provider_event_id=None):
    """Consulta sin bloqueo de BD; la función SQL revalida y concede atómicamente.

    finance_connection es una conexión psycopg autenticada con un login distinto
    del usuario web y miembro solo de mp_b03d_executor_test.
    """
    if connection.vendor != 'postgresql' or type(provider) is not SimulatedFinancialProvider:
        raise FinancialConflict('postgresql_and_simulator_required')
    order = Order.objects.get(pk=order_id)
    if order.state == Order.State.PAID:
        entitlement = DeliveryEntitlement.objects.get(order=order)
        verification = FinancialVerification.objects.get(order=order, state='applied')
        with finance_connection.cursor() as cursor:
            cursor.execute('SELECT public.store_b03d_confirm(%s::bigint)', (verification.pk,))
            if cursor.fetchone()[0] != entitlement.pk:
                raise FinancialConflict('applied_entitlement_mismatch')
        finance_connection.commit()
        return ReconciliationResult('applied', verification.pk, entitlement.pk)
    attempt = PaymentAttempt.objects.get(order=order, state=PaymentAttempt.State.SESSION_OPEN)
    request = CheckoutRequest.objects.get(attempt=attempt, state=CheckoutRequest.State.BOUND)
    if order.environment != 'test' or order.state != Order.State.AWAITING_PAYMENT:
        raise FinancialConflict('order_not_open_in_test')
    if PaymentProviderEvent.objects.filter(state='contradiction',
            provider_account_id=attempt.provider_account_id, environment=order.environment).filter(
                models.Q(attempt=attempt) | models.Q(external_object_id=attempt.checkout_session_id)
                | models.Q(claimed_operation_id=attempt.operation_id)
                | models.Q(claimed_order_public_id=order.public_id)).exists():
        return _record_review(order, attempt, request, finance_connection,
                              'unresolved_contradiction')
    try:
        session, intent, line, success_event, issue = _provider_facts(order, attempt, request, provider)
    except FinancialConflict as exc:
        return _record_review(order, attempt, request, finance_connection, str(exc))
    except KeyError:
        return _record_review(order, attempt, request, finance_connection,
                              'provider_object_missing')
    except SimulatedProviderUnavailable:
        return ReconciliationResult('pending', reason='provider_unavailable')
    if issue == 'payment_pending':
        return ReconciliationResult('pending', reason=issue)
    event_row = None
    if provider_event_id is not None:
        event_row = PaymentProviderEvent.objects.get(pk=provider_event_id)
        if (event_row.external_object_id != session.id
                or event_row.provider_account_id != attempt.provider_account_id
                or event_row.environment != order.environment
                or event_row.state != PaymentProviderEvent.State.PENDING):
            return _record_review(order, attempt, request, finance_connection,
                                  'webhook_evidence_mismatch')
    paid_at = success_event.created.astimezone(dt_timezone.utc) if success_event else None
    state, reason = ('review', issue) if issue else _file_status(order)
    source_key = uuid.uuid5(uuid.NAMESPACE_URL,
        f'b03d|{provider.account_id}|test|{session.id}|{intent.id}|'
        f'{success_event.id if success_event else "missing_success_event"}|{state}|{reason}')
    try:
        with finance_connection.cursor() as cursor:
            cursor.execute("""SELECT public.store_b03d_record(
                %s::uuid,%s::bigint,%s::bigint,%s::bigint,%s,%s,%s,%s,%s,%s::timestamptz,
                %s::bigint,%s,%s,%s,%s::integer,%s,%s)""",
                (str(source_key), order.pk, attempt.pk, event_row.pk if event_row else None,
                 provider.account_id, order.environment, session.id, intent.id,
                 success_event.id if success_event else '', paid_at, order.amount_minor,
                 order.currency, line.price_id, line.product_id, line.quantity, state, reason))
            verification_id = cursor.fetchone()[0]
        finance_connection.commit()
    except Exception:
        finance_connection.rollback()
        applied = FinancialVerification.objects.filter(source_key=source_key, state='applied').first()
        if applied and applied.order_id == order.pk and applied.attempt_id == attempt.pk:
            entitlement = DeliveryEntitlement.objects.get(order_id=order.pk,
                source_attempt_id=attempt.pk, grant_correlation_id=source_key)
            return ReconciliationResult('applied', applied.pk, entitlement.pk)
        raise
    if state == 'review':
        return ReconciliationResult('review', verification_id, reason=reason)
    if reason:
        return ReconciliationResult('pending_delivery', verification_id, reason=reason)
    try:
        with finance_connection.cursor() as cursor:
            cursor.execute('SELECT public.store_b03d_confirm(%s::bigint)', (verification_id,))
            entitlement_id = cursor.fetchone()[0]
        finance_connection.commit()
    except Exception:
        finance_connection.rollback()
        raise
    return ReconciliationResult('applied', verification_id, entitlement_id)
