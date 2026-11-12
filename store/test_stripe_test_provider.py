"""Contratos del SDK con respuestas sintéticas; ningún test abre sockets."""

import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

import stripe
from django.db import connection, connections
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.utils import timezone as django_timezone

from store.checkout_provider import ProviderUncertain
from store.financial_provider import ProviderUnavailable
from store.stripe_test_provider import StripeProviderDataError, StripeTestProvider
from store.checkout_services import CheckoutPending, start_checkout
from store.models import CheckoutRequest, DeliveryEntitlement, PaymentAttempt
from store.test_checkout_sessions import checkout_fixture
from store.order_services import OrderConflict


class Page:
    def __init__(self, rows):
        self.rows = rows

    def auto_paging_iter(self):
        yield from self.rows


def sdk_client():
    client = Mock()
    client.v1.accounts.retrieve_current.return_value = {'id': 'acct_test', 'livemode': False}
    client.v1.prices.retrieve.return_value = dict(id='price_test', active=True,
        livemode=False, recurring=None, type='one_time', billing_scheme='per_unit',
        custom_unit_amount=None, transform_quantity=None, currency='mxn',
        product='prod_test', unit_amount=49900)
    return client


def session(operation_id):
    return dict(id='cs_test_synthetic', livemode=False, url='https://checkout.stripe.com/c/test',
        status='open', expires_at=1790003600, created=1790000000,
        payment_status='unpaid', mode='payment', payment_intent=None,
        amount_total=49900, currency='mxn', client_reference_id='order-public',
        total_details={'amount_discount': 0, 'amount_tax': 0, 'amount_shipping': 0},
        automatic_tax={'enabled': False}, payment_method_types=['card'],
        allow_promotion_codes=False, adaptive_pricing={'enabled': False},
        success_url='https://example.invalid/success',
        cancel_url='https://example.invalid/cancel',
        metadata={'operation_id': str(operation_id)})


@override_settings(STRIPE_TEST_ADAPTER_ENABLED=True)
class StripeTestProviderTests(SimpleTestCase):
    def setUp(self):
        self.client = sdk_client()
        self.provider = StripeTestProvider(client=self.client, account_id='acct_test')
        self.operation_id = uuid.uuid4()

    def test_price_and_checkout_request_are_exact_and_idempotent(self):
        price = self.provider.get_price('price_test')
        self.assertEqual((price.amount_minor, price.currency, price.product_id),
                         (49900, 'MXN', 'prod_test'))
        self.client.v1.checkout.sessions.create.return_value = session(self.operation_id)
        result = self.provider.create_session(idempotency_key='synthetic-key',
            price_id='price_test', quantity=1, mode='payment',
            success_url='https://example.invalid/success',
            cancel_url='https://example.invalid/cancel',
            client_reference_id='order-public', operation_id=self.operation_id,
            payment_method_types=('card',))
        self.assertEqual(result.session_id, 'cs_test_synthetic')
        args, kwargs = self.client.v1.checkout.sessions.create.call_args
        self.assertEqual(args[0]['line_items'], [{'price': 'price_test', 'quantity': 1}])
        self.assertEqual(args[0]['allowed_payment_method_types'], ['card'])
        self.assertNotIn('payment_method_types', args[0])
        self.assertEqual(kwargs['options'], {'idempotency_key': 'synthetic-key'})

    def test_wrong_account_and_live_price_are_rejected(self):
        self.client.v1.accounts.retrieve_current.return_value['id'] = 'acct_other'
        with self.assertRaises(StripeProviderDataError):
            self.provider.get_price('price_test')
        self.client.v1.accounts.retrieve_current.return_value['id'] = 'acct_test'
        self.client.v1.prices.retrieve.return_value['livemode'] = True
        with self.assertRaises(StripeProviderDataError):
            self.provider.get_price('price_test')

    def test_bad_session_is_uncertain_and_never_returns_url(self):
        self.provider.get_price('price_test')
        bad = session(self.operation_id)
        bad['amount_total'] = 1
        self.client.v1.checkout.sessions.create.return_value = bad
        with self.assertRaises(ProviderUncertain):
            self.provider.create_session(idempotency_key='synthetic-key',
                price_id='price_test', quantity=1, mode='payment',
                success_url='https://example.invalid/success',
                cancel_url='https://example.invalid/cancel',
                client_reference_id='order-public', operation_id=self.operation_id,
                payment_method_types=('card',))

    def test_session_retrieval_requires_identity(self):
        self.assertIsNone(self.provider.get_session(idempotency_key='synthetic-key'))
        self.client.v1.checkout.sessions.retrieve.return_value = session(self.operation_id)
        retrieved = self.provider.get_session('cs_test_synthetic')
        self.assertEqual(retrieved.session_id, 'cs_test_synthetic')

    def test_financial_objects_and_paginated_lines(self):
        self.client.v1.payment_intents.retrieve.return_value = dict(id='pi_test',
            livemode=False, created=1790000000, status='succeeded',
            capture_method='automatic', amount=49900, amount_received=49900,
            currency='mxn')
        self.client.v1.checkout.sessions.line_items.list.return_value = Page([
            {'price': {'id': 'price_test', 'product': 'prod_test'},
             'quantity': 1, 'amount_total': 49900, 'currency': 'mxn'}])
        self.client.v1.events.list.return_value = Page([dict(id='evt_test',
            livemode=False, type='payment_intent.succeeded', created=1790000010,
            account=None, data={'object': {'id': 'pi_test'}})])
        self.assertEqual(self.provider.get_intent('pi_test').amount_received, 49900)
        self.assertEqual(self.provider.get_all_lines('cs_test_synthetic')[0].quantity, 1)
        self.assertEqual(self.provider.find_success_events('pi_test')[0].object_id, 'pi_test')

    def test_unbounded_line_result_is_rejected(self):
        self.client.v1.checkout.sessions.line_items.list.return_value = []
        with self.assertRaises(StripeProviderDataError):
            self.provider.get_all_lines('cs_test_synthetic')

    def test_network_failure_is_recoverable_and_creation_is_uncertain(self):
        self.client.v1.prices.retrieve.side_effect = stripe.APIConnectionError('synthetic')
        with self.assertRaises(ProviderUnavailable):
            self.provider.get_price('price_test')
        self.client.v1.prices.retrieve.side_effect = None
        self.provider.get_price('price_test')
        self.client.v1.checkout.sessions.create.side_effect = stripe.APIConnectionError('synthetic')
        with self.assertRaises(ProviderUncertain):
            self.provider.create_session(idempotency_key='synthetic-key',
                price_id='price_test', quantity=1, mode='payment',
                success_url='https://example.invalid/success',
                cancel_url='https://example.invalid/cancel',
                client_reference_id='order-public', operation_id=self.operation_id,
                payment_method_types=('card',))

    def test_multiple_success_events_are_returned_for_financial_rejection(self):
        self.client.v1.payment_intents.retrieve.return_value = dict(id='pi_test',
            livemode=False, created=1790000000, status='succeeded',
            capture_method='automatic', amount=49900, amount_received=49900,
            currency='mxn')
        self.provider.get_intent('pi_test')
        events = [dict(id=f'evt_{n}', livemode=False,
            type='payment_intent.succeeded', created=1790000010 + n,
            data={'object': {'id': 'pi_test'}}) for n in range(2)]
        self.client.v1.events.list.return_value = Page(events)
        self.assertEqual(len(self.provider.find_success_events('pi_test')), 2)


class StripeTestProviderDisabledTests(SimpleTestCase):
    @override_settings(STRIPE_TEST_ADAPTER_ENABLED=False)
    def test_disabled_before_any_sdk_call(self):
        client = sdk_client()
        provider = StripeTestProvider(client=client, account_id='acct_test')
        with self.assertRaises(StripeProviderDataError):
            provider.get_price('price_test')
        client.v1.accounts.retrieve_current.assert_not_called()

    @override_settings(STRIPE_TEST_ADAPTER_ENABLED=True)
    def test_factory_rejects_live_or_missing_key_without_client(self):
        with patch.dict('os.environ', {'STRIPE_TEST_RESTRICTED_KEY': 'sk_live_synthetic',
                                      'STRIPE_TEST_ACCOUNT_ID': 'acct_test'}):
            with patch('stripe.StripeClient') as constructor:
                with self.assertRaises(StripeProviderDataError):
                    StripeTestProvider.from_environment()
                constructor.assert_not_called()


@override_settings(STRIPE_TEST_ADAPTER_ENABLED=True)
class StripeCheckoutContractTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        context = override_settings(PRIVATE_PRODUCT_ROOT=Path(self.temp.name))
        context.enable()
        self.addCleanup(context.disable)
        _, _, self.order, _, _ = checkout_fixture(self.temp.name,
            f'stripe-contract-{uuid.uuid4().hex}')
        self.operation = uuid.uuid4()
        self.key = uuid.uuid4()
        self.client = sdk_client()
        self.client.v1.prices.retrieve.return_value['id'] = 'price_synthetic'
        self.client.v1.prices.retrieve.return_value['product'] = 'prod_synthetic'
        self.client.v1.accounts.retrieve_current.return_value['id'] = 'acct_synthetic'
        self.provider = StripeTestProvider(client=self.client, account_id='acct_synthetic')
        self.remote_session = None
        self.creation_calls = 0

        def create(params, options):
            self.creation_calls += 1
            if self.remote_session is None:
                raw = session(self.operation)
                raw['id'] = 'cs_test_contract'
                raw['client_reference_id'] = str(self.order.public_id)
                raw['success_url'] = params['success_url']
                raw['cancel_url'] = params['cancel_url']
                raw['created'] = int(django_timezone.now().timestamp())
                raw['expires_at'] = raw['created'] + 3600
                self.remote_session = raw
            return self.remote_session

        self.client.v1.checkout.sessions.create.side_effect = create
        self.client.v1.checkout.sessions.retrieve.side_effect = lambda _: self.remote_session

    def start(self):
        return start_checkout(order_id=self.order.pk, operation_id=self.operation,
            request_idempotency_key=self.key, provider=self.provider,
            return_origin='https://example.invalid')

    def test_repeated_intention_reuses_bound_session_without_second_creation(self):
        first = self.start()
        second = self.start()
        self.assertEqual(first, second)
        self.assertEqual(self.creation_calls, 1)
        self.assertEqual(PaymentAttempt.objects.filter(order=self.order).count(), 1)
        self.assertEqual(CheckoutRequest.objects.filter(state='bound').count(), 1)
        self.assertFalse(DeliveryEntitlement.objects.exists())

    def test_lost_response_replays_same_key_and_parameters(self):
        original = self.provider._session
        calls = 0

        def lose_once(raw, *, expected=None):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise StripeProviderDataError('synthetic_lost_response')
            return original(raw, expected=expected)

        with patch.object(self.provider, '_session', side_effect=lose_once):
            with self.assertRaises(CheckoutPending):
                self.start()
            result = self.start()
        self.assertEqual(result.session_id, 'cs_test_contract')
        self.assertEqual(self.creation_calls, 2)
        options = [call.kwargs['options']['idempotency_key']
                   for call in self.client.v1.checkout.sessions.create.call_args_list]
        self.assertEqual(options, [str(self.key), str(self.key)])
        self.assertEqual(PaymentAttempt.objects.filter(order=self.order).count(), 1)

    def test_uncertain_operation_cannot_replay_after_safe_window(self):
        with patch.object(self.provider, '_session', side_effect=StripeProviderDataError('lost')):
            with self.assertRaises(CheckoutPending):
                self.start()
        from datetime import timedelta
        future = django_timezone.now() + timedelta(hours=24)
        with patch('store.checkout_services.timezone', now=lambda: future):
            with self.assertRaises(CheckoutPending):
                self.start()
        self.assertEqual(self.creation_calls, 1)


@override_settings(STRIPE_TEST_ADAPTER_ENABLED=True)
class StripeCheckoutConcurrencyTests(TransactionTestCase):
    def test_competing_operations_keep_one_active_attempt(self):
        if connection.vendor != 'postgresql':
            self.skipTest('La concurrencia real requiere PostgreSQL.')
        with tempfile.TemporaryDirectory() as root:
            with override_settings(PRIVATE_PRODUCT_ROOT=Path(root)):
                _, _, order, _, _ = checkout_fixture(root,
                    f'stripe-concurrent-{uuid.uuid4().hex}')
                client = sdk_client()
                client.v1.prices.retrieve.return_value['id'] = 'price_synthetic'
                client.v1.prices.retrieve.return_value['product'] = 'prod_synthetic'
                client.v1.accounts.retrieve_current.return_value['id'] = 'acct_synthetic'

                def create(params, options):
                    operation = uuid.UUID(params['metadata']['operation_id'])
                    raw = session(operation)
                    raw['id'] = 'cs_test_' + operation.hex
                    raw['client_reference_id'] = str(order.public_id)
                    raw['success_url'] = params['success_url']
                    raw['cancel_url'] = params['cancel_url']
                    raw['created'] = int(django_timezone.now().timestamp())
                    raw['expires_at'] = raw['created'] + 3600
                    return raw

                client.v1.checkout.sessions.create.side_effect = create
                provider = StripeTestProvider(client=client, account_id='acct_synthetic')

                def run(_):
                    try:
                        return start_checkout(order_id=order.pk,
                            operation_id=uuid.uuid4(), request_idempotency_key=uuid.uuid4(),
                            provider=provider, return_origin='https://example.invalid')
                    except OrderConflict:
                        return None
                    finally:
                        connections.close_all()

                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(run, range(2)))
                self.assertEqual(sum(item is not None for item in results), 1)
                self.assertEqual(PaymentAttempt.objects.filter(order=order).count(), 1)
                self.assertEqual(client.v1.checkout.sessions.create.call_count, 1)
