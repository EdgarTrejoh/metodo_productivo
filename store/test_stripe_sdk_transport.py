"""Contrato con stripe-python 17 real y transporte HTTP en memoria, sin sockets."""

import json
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import stripe
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone as django_timezone

from store.checkout_provider import ProviderUncertain
from store.financial_provider import ProviderUnavailable
from store.stripe_test_provider import StripeTestProvider
from store.checkout_services import CheckoutPending, start_checkout
from store.models import CheckoutRequest, Order, OrderAuditEvent, PaymentAttempt
from store.order_services import OrderConflict
from store.test_checkout_sessions import checkout_fixture


class MemoryStripeHTTP(stripe.HTTPClient):
    name = 'memory-stripe-test'

    def __init__(self):
        super().__init__()
        self.requests = []
        self.create_status = 200
        self.price_status = 200
        self.price_id = 'price_test'
        self.product_id = 'prod_test'
        self.process_then_500_once = False
        self.operation_id = uuid.uuid4()
        self.session = self._session()

    def _session(self):
        created = int(datetime.now(timezone.utc).timestamp())
        return dict(object='checkout.session', id='cs_test_memory', livemode=False,
            url='https://checkout.stripe.com/c/synthetic', status='open',
            expires_at=created + 3600, created=created, payment_status='unpaid',
            mode='payment', payment_intent=None, amount_total=49900,
            currency='mxn', client_reference_id='order-public',
            total_details={'amount_discount': 0, 'amount_tax': 0, 'amount_shipping': 0},
            automatic_tax={'enabled': False}, payment_method_types=['card'],
            allow_promotion_codes=False, adaptive_pricing={'enabled': False},
            success_url='https://example.invalid/success',
            cancel_url='https://example.invalid/cancel',
            metadata={'operation_id': str(self.operation_id)})

    def request(self, method, url, headers, post_data=None, *, _usage=None):
        self.requests.append((method, url, dict(headers or {}), post_data))
        path = urlsplit(url).path
        query = parse_qs(urlsplit(url).query)
        if path == '/v1/account':
            body, status = {'object': 'account', 'id': 'acct_memory', 'livemode': False}, 200
        elif path == '/v1/prices/' + self.price_id:
            body = dict(object='price', id=self.price_id, livemode=False, active=True,
                recurring=None, type='one_time', billing_scheme='per_unit',
                custom_unit_amount=None, transform_quantity=None, currency='mxn',
                product=self.product_id, unit_amount=49900)
            status = self.price_status
        elif path == '/v1/checkout/sessions' and method.lower() == 'post':
            body, status = self.session, self.create_status
            if self.process_then_500_once:
                self.process_then_500_once = False
                status = 500
        elif path == '/v1/checkout/sessions/cs_test_memory':
            body, status = self.session, 200
        elif path == '/v1/payment_intents/pi_test_memory':
            body, status = dict(object='payment_intent', id='pi_test_memory',
                livemode=False, created=self.session['created'], status='succeeded',
                capture_method='automatic', amount=49900, amount_received=49900,
                currency='mxn'), 200
        elif path == '/v1/checkout/sessions/cs_test_memory/line_items':
            first = not query.get('starting_after')
            data = [dict(object='item', id='li_1', price={'id': 'price_test',
                'product': 'prod_test'}, quantity=1, amount_total=49900,
                currency='mxn')] if first else []
            body, status = dict(object='list', data=data, has_more=first, url=path), 200
        elif path == '/v1/events':
            first = not query.get('starting_after')
            data = [dict(object='event', id='evt_1', livemode=False,
                type='payment_intent.succeeded', created=self.session['created'] + 1,
                data={'object': {'id': 'pi_test_memory'}})] if first else []
            body, status = dict(object='list', data=data, has_more=first, url=path), 200
        else:
            raise AssertionError(f'Unexpected SDK request: {method} {path}')
        if status >= 400:
            body = {'error': {'type': 'invalid_request_error' if status == 404 else 'api_error',
                              'message': 'synthetic HTTP failure'}}
        return json.dumps(body), status, {'Request-Id': 'req_synthetic'}


@override_settings(STRIPE_TEST_ADAPTER_ENABLED=True)
class StripeSDKTransportTests(SimpleTestCase):
    def setUp(self):
        self.http = MemoryStripeHTTP()
        self.client = stripe.StripeClient('rk_test_synthetic_transport_only',
            http_client=self.http, max_network_retries=0)
        self.provider = StripeTestProvider(client=self.client, account_id='acct_memory')

    def create(self):
        return self.provider.create_session(idempotency_key='synthetic-idempotency',
            price_id='price_test', quantity=1, mode='payment',
            success_url='https://example.invalid/success',
            cancel_url='https://example.invalid/cancel',
            client_reference_id='order-public', operation_id=self.http.operation_id,
            payment_method_types=('card',))

    def test_real_sdk_serializes_checkout_and_retrieves_objects(self):
        self.assertEqual(self.provider.get_price('price_test').amount_minor, 49900)
        self.assertEqual(self.create().session_id, 'cs_test_memory')
        self.assertEqual(self.provider.get_session('cs_test_memory').session_id, 'cs_test_memory')
        create = next(row for row in self.http.requests
                      if urlsplit(row[1]).path == '/v1/checkout/sessions')
        fields = parse_qs(create[3])
        self.assertEqual(fields['line_items[0][price]'], ['price_test'])
        self.assertEqual(fields['line_items[0][quantity]'], ['1'])
        self.assertEqual(fields['allowed_payment_method_types[0]'], ['card'])
        self.assertEqual(create[2]['Idempotency-Key'], 'synthetic-idempotency')
        self.http.session['status'] = 'complete'
        self.http.session['payment_status'] = 'paid'
        self.http.session['payment_intent'] = 'pi_test_memory'
        self.assertEqual(self.provider.get_intent('pi_test_memory').amount_received, 49900)
        self.assertEqual(len(self.provider.get_all_lines('cs_test_memory')), 1)
        events = self.provider.find_success_events('pi_test_memory')
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].created.tzinfo, timezone.utc)
        self.assertTrue(any('/v1/payment_intents/pi_test_memory' in row[1]
                            for row in self.http.requests))
        self.assertEqual(sum('/line_items' in row[1] for row in self.http.requests), 2)
        self.assertEqual(sum('/v1/events' in row[1] for row in self.http.requests), 2)

    def test_sdk_http_errors_preserve_uncertainty_and_price_retry(self):
        self.http.price_status = 500
        with self.assertRaises(ProviderUnavailable):
            self.provider.get_price('price_test')
        self.http.price_status = 200
        self.provider.get_price('price_test')
        self.http.create_status = 500
        for _ in range(2):
            with self.assertRaises(ProviderUncertain):
                self.create()
        creates = [row for row in self.http.requests
                   if urlsplit(row[1]).path == '/v1/checkout/sessions']
        self.assertEqual(len(creates), 2)
        self.assertEqual(creates[0][3], creates[1][3])
        self.assertEqual(creates[0][2]['Idempotency-Key'],
                         creates[1][2]['Idempotency-Key'])

    def test_sdk_not_found_price_is_incompatible_not_transient(self):
        from store.stripe_test_provider import StripeProviderDataError
        self.http.price_status = 404
        with self.assertRaises(StripeProviderDataError):
            self.provider.get_price('price_test')

    def test_sdk_response_with_invalid_time_is_rejected(self):
        from store.stripe_test_provider import StripeProviderDataError
        self.http.session['created'] = 'not-a-timestamp'
        with self.assertRaises(StripeProviderDataError):
            self.provider.get_session('cs_test_memory')


@override_settings(STRIPE_TEST_ADAPTER_ENABLED=True)
class StripeSDKRecoveryTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        context = override_settings(PRIVATE_PRODUCT_ROOT=Path(self.temp.name))
        context.enable()
        self.addCleanup(context.disable)
        _, _, self.order, _, _ = checkout_fixture(self.temp.name,
            f'sdk-recovery-{uuid.uuid4().hex}')
        self.operation = uuid.uuid4()
        self.key = uuid.uuid4()
        self.http = MemoryStripeHTTP()
        self.http.price_id = 'price_synthetic'
        self.http.product_id = 'prod_synthetic'
        self.http.operation_id = self.operation
        self.http.session = self.http._session()
        self.http.session['client_reference_id'] = str(self.order.public_id)
        self.http.session['success_url'] = 'https://example.invalid/tienda/resultado/?estado=pendiente'
        self.http.session['cancel_url'] = 'https://example.invalid/tienda/resultado/?estado=cancelado'
        self.provider = self.new_provider()

    def new_provider(self):
        client = stripe.StripeClient('rk_test_synthetic_transport_only',
            http_client=self.http, max_network_retries=0)
        return StripeTestProvider(client=client, account_id='acct_memory')

    def start(self, provider=None, operation=None, key=None):
        return start_checkout(order_id=self.order.pk,
            operation_id=operation or self.operation,
            request_idempotency_key=key or self.key,
            provider=provider or self.provider, return_origin='https://example.invalid')

    def creations(self):
        return [row for row in self.http.requests
                if urlsplit(row[1]).path == '/v1/checkout/sessions']

    def test_processed_response_lost_then_restart_recovers_same_operation(self):
        self.http.process_then_500_once = True
        with self.assertRaises(CheckoutPending):
            self.start()
        self.assertEqual(CheckoutRequest.objects.get().state, 'uncertain')
        with self.assertRaises(OrderConflict):
            self.start(operation=uuid.uuid4(), key=uuid.uuid4())
        result = self.start(provider=self.new_provider())
        self.assertEqual(result.session_id, 'cs_test_memory')
        self.assertEqual(len(self.creations()), 2)
        self.assertEqual(self.creations()[0][3], self.creations()[1][3])
        self.assertEqual(self.creations()[0][2]['Idempotency-Key'],
                         self.creations()[1][2]['Idempotency-Key'])
        self.assertEqual(PaymentAttempt.objects.filter(order=self.order).count(), 1)
        self.assertEqual(OrderAuditEvent.objects.filter(
            order=self.order, action='checkout_uncertain').count(), 1)

    def test_persistent_http_errors_never_open_different_operation(self):
        self.http.create_status = 500
        for _ in range(2):
            with self.assertRaises(CheckoutPending):
                self.start(provider=self.new_provider())
        self.assertEqual(CheckoutRequest.objects.get().state, 'uncertain')
        with self.assertRaises(OrderConflict):
            self.start(operation=uuid.uuid4(), key=uuid.uuid4())
        future = django_timezone.now() + timedelta(hours=24)
        with patch('store.checkout_services.timezone', now=lambda: future):
            with self.assertRaises(CheckoutPending):
                self.start(provider=self.new_provider())
        self.assertEqual(len(self.creations()), 2)
        self.assertEqual({row[2]['Idempotency-Key'] for row in self.creations()},
                         {str(self.key)})
        self.assertEqual(PaymentAttempt.objects.filter(order=self.order).count(), 1)
        self.assertEqual(OrderAuditEvent.objects.filter(
            order=self.order, action='checkout_uncertain').count(), 1)

    def test_price_http_failure_is_recoverable_without_local_writes(self):
        self.http.price_status = 500
        with self.assertRaises(CheckoutPending):
            self.start()
        self.assertFalse(PaymentAttempt.objects.exists())
        self.assertFalse(CheckoutRequest.objects.exists())
        self.assertFalse(self.creations())
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, Order.State.CREATED)
        self.http.price_status = 200
        self.assertEqual(self.start().session_id, 'cs_test_memory')

    def test_restart_after_remote_creation_before_uncertain_record(self):
        self.http.process_then_500_once = True
        with patch('store.checkout_services._mark_uncertain',
                   side_effect=RuntimeError('synthetic process termination')):
            with self.assertRaises(RuntimeError):
                self.start()
        self.assertEqual(CheckoutRequest.objects.get().state, 'calling')
        with self.assertRaises(OrderConflict):
            self.start(operation=uuid.uuid4(), key=uuid.uuid4())
        future = django_timezone.now() + timedelta(seconds=31)
        with patch('store.checkout_services.timezone', now=lambda: future):
            result = self.start(provider=self.new_provider())
        self.assertEqual(result.session_id, 'cs_test_memory')
        self.assertEqual(len(self.creations()), 2)
        self.assertEqual({row[2]['Idempotency-Key'] for row in self.creations()},
                         {str(self.key)})
        self.assertEqual(PaymentAttempt.objects.filter(order=self.order).count(), 1)
        self.assertEqual(OrderAuditEvent.objects.filter(
            order=self.order, action='checkout_uncertain').count(), 1)
