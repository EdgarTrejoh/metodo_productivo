import hashlib
import hmac
import importlib
import json
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.db import DatabaseError, connection, connections, transaction
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from store.checkout_services import start_checkout
from store import webhook_evidence
from store.models import DeliveryEntitlement, Order, PaymentAttempt, PaymentProviderEvent
from store.test_checkout_sessions import checkout_fixture
from store.webhook_evidence import (InvalidWebhook, WebhookEndpointConfig,
    assert_no_unresolved_contradiction, receive_authenticated_event, receive_webhook_http, retry_pending_event,
    verify_signature)


SECRET = 'whsec_synthetic_test_only'
CONFIG = WebhookEndpointConfig('acct_synthetic', 'test', SECRET)


def signed(body, *, timestamp=None, secret=SECRET):
    timestamp = timestamp or int(timezone.now().timestamp())
    signature = hmac.new(secret.encode(), str(timestamp).encode() + b'.' + body,
                         hashlib.sha256).hexdigest()
    return f't={timestamp},v1={signature}'


def event_body(*, event_id=None, session_id='cs_test_unknown', event_type='checkout.session.completed',
               operation_id=None, order_id=None, amount=49900, currency='mxn', payment_status='paid',
               environment=False, account='acct_synthetic'):
    data = {'id': event_id or f'evt_{uuid.uuid4().hex}', 'type': event_type,
            'created': int(timezone.now().timestamp()), 'livemode': environment,
            'account': account, 'data': {'object': {'id': session_id,
            'amount_total': amount, 'currency': currency,
            'payment_status': payment_status,
            'client_reference_id': str(order_id) if order_id else None,
            'metadata': {'operation_id': str(operation_id) if operation_id else ''}}}}
    return json.dumps(data, sort_keys=True).encode()


class WebhookEvidenceTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def receive(self, body, *, signature=None):
        return receive_webhook_http(self.factory.post('/internal-webhook/', body,
            content_type='application/json', HTTP_STRIPE_SIGNATURE=signature or signed(body)), CONFIG)

    def test_valid_duplicate_and_changed_body(self):
        body = event_body(event_id='evt_same')
        self.assertEqual(self.receive(body).status_code, 200)
        self.assertEqual(self.receive(body).status_code, 200)
        self.assertEqual(PaymentProviderEvent.objects.count(), 1)
        changed = event_body(event_id='evt_same', amount=50000)
        self.assertEqual(self.receive(changed).status_code, 409)
        record = PaymentProviderEvent.objects.get()
        self.assertEqual(record.state, PaymentProviderEvent.State.CONTRADICTION)
        self.assertEqual(record.raw_sha256, hashlib.sha256(body).hexdigest())
        self.assertEqual(record.conflict_count, 1)

    def test_signature_missing_changed_expired_and_malformed(self):
        body = event_body()
        with self.assertRaises(InvalidWebhook):
            verify_signature(body, None, SECRET)
        with self.assertRaises(InvalidWebhook):
            verify_signature(body + b' ', signed(body), SECRET)
        with self.assertRaises(InvalidWebhook):
            verify_signature(body, signed(body, timestamp=int(timezone.now().timestamp()) - 400), SECRET)
        with self.assertRaises(InvalidWebhook):
            verify_signature(body, signed(body, secret='wrong_secret'), SECRET)
        with self.assertRaises(InvalidWebhook):
            verify_signature(body, 't=123,broken', SECRET)
        self.assertEqual(self.receive(b'{', signature=signed(b'{')).status_code, 400)
        self.assertFalse(PaymentProviderEvent.objects.exists())

    def test_wrong_endpoint_scope_and_persistence_failure(self):
        wrong = event_body(environment=True)
        self.assertEqual(self.receive(wrong).status_code, 400)
        wrong_account = event_body(account='acct_other')
        self.assertEqual(self.receive(wrong_account).status_code, 400)
        body = event_body()
        with patch('store.webhook_evidence.PaymentProviderEvent.objects') as manager:
            manager.select_for_update.return_value.get_or_create.side_effect = DatabaseError('synthetic outage')
            self.assertEqual(self.receive(body).status_code, 503)
        self.assertFalse(PaymentProviderEvent.objects.exists())

    def test_unknown_out_of_order_and_no_financial_transition(self):
        body = event_body(event_type='checkout.session.async_payment_succeeded')
        record, result = receive_authenticated_event(body, signed(body), CONFIG)
        self.assertEqual((result, record.reason_code), ('created', 'unknown_session'))
        self.assertEqual(record.state, PaymentProviderEvent.State.PENDING)
        self.assertIsNone(record.processed_at)
        self.assertFalse(DeliveryEntitlement.objects.exists())
        self.assertFalse(Order.objects.filter(state=Order.State.PAID).exists())
        self.assertFalse(PaymentAttempt.objects.filter(state=PaymentAttempt.State.SUCCEEDED).exists())
        again = importlib.reload(webhook_evidence).retry_pending_event(record.pk)
        self.assertEqual((again.retry_count, again.reason_code), (1, 'unknown_session'))

    def test_sensitive_payload_not_persisted(self):
        data = json.loads(event_body())
        data['data']['object']['customer_email'] = 'private@example.invalid'
        data['data']['object']['client_secret'] = 'secret_synthetic'
        body = json.dumps(data).encode()
        self.receive(body)
        record = PaymentProviderEvent.objects.get()
        self.assertFalse(any('private@example.invalid' in str(getattr(record, field.name))
            or 'secret_synthetic' in str(getattr(record, field.name)) for field in record._meta.fields))

    def test_bound_session_pending_payment_and_wrong_amount(self):
        with tempfile.TemporaryDirectory() as root:
            with override_settings(PRIVATE_PRODUCT_ROOT=Path(root)):
                _, _, order, provider, _ = checkout_fixture(root, 'webhook-test-product')
                operation = uuid.uuid4()
                checkout = start_checkout(order_id=order.pk, operation_id=operation,
                    request_idempotency_key=uuid.uuid4(), provider=provider,
                    return_origin='https://example.invalid')
                pending = event_body(session_id=checkout.session_id, operation_id=operation,
                    order_id=order.public_id, payment_status='unpaid')
                record, _ = receive_authenticated_event(pending, signed(pending), CONFIG)
                self.assertEqual(record.reason_code, 'payment_pending')
                wrong = event_body(session_id=checkout.session_id, operation_id=operation,
                    order_id=order.public_id, amount=1)
                record, _ = receive_authenticated_event(wrong, signed(wrong), CONFIG)
                self.assertEqual((record.state, record.reason_code),
                    (PaymentProviderEvent.State.CONTRADICTION, 'amount_mismatch'))
                bad_currency = event_body(session_id=checkout.session_id, operation_id=operation,
                    order_id=order.public_id, currency='usd')
                currency_record, _ = receive_authenticated_event(bad_currency, signed(bad_currency), CONFIG)
                self.assertEqual(currency_record.reason_code, 'currency_mismatch')
                with self.assertRaises(InvalidWebhook):
                    assert_no_unresolved_contradiction(PaymentAttempt.objects.get(order=order).pk)
                expired = event_body(session_id=checkout.session_id, operation_id=operation,
                    order_id=order.public_id, event_type='checkout.session.expired')
                late, _ = receive_authenticated_event(expired, signed(expired), CONFIG)
                self.assertEqual(late.reason_code, 'provider_requery_required')
                self.assertIsNone(Order.objects.get(pk=order.pk).paid_at)

    def test_event_before_session_binding_can_be_retried(self):
        with tempfile.TemporaryDirectory() as root:
            with override_settings(PRIVATE_PRODUCT_ROOT=Path(root)):
                _, _, order, provider, _ = checkout_fixture(root, 'webhook-early-product')
                operation, key = uuid.uuid4(), uuid.uuid4()
                provider.lost_response_once = True
                from store.checkout_services import CheckoutPending
                with self.assertRaises(CheckoutPending):
                    start_checkout(order_id=order.pk, operation_id=operation,
                        request_idempotency_key=key, provider=provider,
                        return_origin='https://example.invalid')
                session = provider.get_session(idempotency_key=str(key))
                body = event_body(session_id=session.session_id, operation_id=operation,
                    order_id=order.public_id)
                record, _ = receive_authenticated_event(body, signed(body), CONFIG)
                self.assertEqual(record.reason_code, 'await_session_binding')
                start_checkout(order_id=order.pk, operation_id=operation,
                    request_idempotency_key=key, provider=provider,
                    return_origin='https://example.invalid')
                record = retry_pending_event(record.pk)
                self.assertEqual(record.reason_code, 'provider_requery_required')
                self.assertEqual(record.retry_count, 1)

    def test_postgresql_cannot_mark_event_applied_or_change_hash(self):
        if connection.vendor != 'postgresql':
            self.skipTest('La guarda de evidencia requiere PostgreSQL.')
        body = event_body()
        record, _ = receive_authenticated_event(body, signed(body), CONFIG)
        for field, value in [('state', 'applied'), ('raw_sha256', '0' * 64)]:
            with self.assertRaises(DatabaseError):
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(f'UPDATE store_paymentproviderevent SET {field} = %s WHERE id = %s', [value, record.pk])


class WebhookConcurrencyTests(TransactionTestCase):
    def test_same_signed_event_from_two_connections(self):
        if connection.vendor != 'postgresql':
            self.skipTest('La concurrencia requiere PostgreSQL.')
        body = event_body(event_id='evt_concurrent')
        signature = signed(body)

        def receive():
            try:
                return receive_authenticated_event(body, signature, CONFIG)[1]
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: receive(), range(2)))
        self.assertEqual(sorted(results), ['created', 'duplicate'])
        self.assertEqual(PaymentProviderEvent.objects.count(), 1)
