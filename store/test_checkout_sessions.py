import hashlib
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from django.db import DatabaseError, IntegrityError, connection, connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings

from store.checkout_provider import PriceQuote, SimulatedCheckoutProvider
from store.checkout_services import CheckoutPending, start_checkout
from store.file_versions import select_sellable_file_version
from store.models import CheckoutRequest, DeliveryEntitlement, Order, OrderAuditEvent, PaymentAttempt, ProductFileVersion
from store.order_services import InvalidOrderOperation, OrderConflict, create_order
from store.test_orders import published_product


def checkout_fixture(root, slug):
    product = published_product(slug=slug)
    product.stripe_product_id = 'prod_synthetic'
    product.stripe_price_id = 'price_synthetic'
    product.save()
    content = b'synthetic checkout file'
    revision = uuid.uuid4().hex
    path = Path(root) / 'synthetic-object' / revision
    path.parent.mkdir()
    path.write_bytes(content)
    version = ProductFileVersion.objects.create(product=product, backend='local',
        object_identifier='synthetic-object', version_id=revision,
        sha256=hashlib.sha256(content).hexdigest(), size_bytes=len(content))
    select_sellable_file_version(product_id=product.pk, version_id=version.pk)
    order = create_order(product_id=product.pk, creation_key=uuid.uuid4(), environment='test')
    provider = SimulatedCheckoutProvider(prices={'price_synthetic': PriceQuote(
        'price_synthetic', 'prod_synthetic', 49900, 'MXN', 'acct_synthetic', 'test')},
        account_id='acct_synthetic', environment='test')
    return product, version, order, provider, path


class CheckoutServiceTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        context = override_settings(PRIVATE_PRODUCT_ROOT=Path(self.temp.name))
        context.enable()
        self.addCleanup(context.disable)
        self.product, self.version, self.order, self.provider, self.path = checkout_fixture(
            self.temp.name, f'checkout-{uuid.uuid4().hex}')
        self.operation = uuid.uuid4()
        self.key = uuid.uuid4()

    def start(self):
        return start_checkout(order_id=self.order.pk, operation_id=self.operation,
            request_idempotency_key=self.key, provider=self.provider,
            return_origin='https://example.invalid')

    def test_one_line_exact_price_and_repeated_intention(self):
        first = self.start()
        second = self.start()
        self.assertEqual(first, second)
        self.assertEqual(self.provider.create_calls, 1)
        self.assertEqual((self.provider.last_request['mode'], self.provider.last_request['quantity'],
                          self.provider.last_request['payment_method_types']), ('payment', 1, ('card',)))
        self.assertEqual(PaymentAttempt.objects.filter(order=self.order).count(), 1)
        self.assertEqual(CheckoutRequest.objects.filter(attempt_id=first.attempt_id, state='bound').count(), 1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, Order.State.AWAITING_PAYMENT)
        self.assertIsNone(self.order.paid_at)
        self.assertFalse(DeliveryEntitlement.objects.exists())
        self.assertEqual(OrderAuditEvent.objects.filter(order=self.order, action='session_open').count(), 1)
        self.assertEqual(OrderAuditEvent.objects.filter(order=self.order, action='awaiting_payment').count(), 1)
        with self.assertRaises(OrderConflict):
            start_checkout(order_id=self.order.pk, operation_id=uuid.uuid4(),
                request_idempotency_key=uuid.uuid4(), provider=self.provider,
                return_origin='https://example.invalid')

    def test_lost_response_recovers_same_session(self):
        self.provider.lost_response_once = True
        with self.assertRaises(CheckoutPending):
            self.start()
        self.assertEqual(PaymentAttempt.objects.get(order=self.order).state, 'prepared')
        self.assertEqual(CheckoutRequest.objects.get(attempt__order=self.order).state, 'uncertain')
        result = self.start()
        self.assertEqual(result.session_id, f'cs_test_{self.operation.hex}')
        self.assertEqual(self.provider.create_calls, 1)
        self.assertFalse(DeliveryEntitlement.objects.exists())

    def test_session_id_cannot_bind_to_second_order(self):
        first = self.start()
        second_order = create_order(product_id=self.product.pk,
            creation_key=uuid.uuid4(), environment='test')
        session = self.provider.get_session(idempotency_key=str(self.key))
        with patch.object(self.provider, 'create_session', return_value=session):
            with self.assertRaises(IntegrityError):
                start_checkout(order_id=second_order.pk, operation_id=uuid.uuid4(),
                    request_idempotency_key=uuid.uuid4(), provider=self.provider,
                    return_origin='https://example.invalid')
        self.assertEqual(PaymentAttempt.objects.filter(checkout_session_id=first.session_id).count(), 1)

    def test_rejects_price_account_file_and_origin(self):
        self.provider.prices['price_synthetic'] = PriceQuote(
            'price_synthetic', 'prod_synthetic', 49800, 'MXN', 'acct_synthetic', 'test')
        with self.assertRaises(InvalidOrderOperation):
            self.start()
        self.assertFalse(PaymentAttempt.objects.exists())
        self.provider.prices['price_synthetic'] = PriceQuote(
            'price_synthetic', 'prod_synthetic', 49900, 'MXN', 'acct_synthetic', 'test')
        self.path.unlink()
        with self.assertRaises(ValueError):
            self.start()
        self.path.write_bytes(b'synthetic checkout file')
        with self.assertRaises(InvalidOrderOperation):
            start_checkout(order_id=self.order.pk, operation_id=self.operation,
                request_idempotency_key=self.key, provider=self.provider,
                return_origin='https://external.invalid')
        self.provider.account_id = 'acct_other'
        with self.assertRaises(InvalidOrderOperation):
            self.start()

    def test_direct_sql_cannot_fabricate_payment(self):
        self.start()
        if connection.vendor != 'postgresql':
            self.skipTest('Las guardas SQL financieras requieren PostgreSQL.')
        attempt = PaymentAttempt.objects.get(order=self.order)
        for table, row_id in (('store_order', self.order.pk), ('store_paymentattempt', attempt.pk)):
            field = 'state'
            target = 'paid' if table == 'store_order' else 'succeeded'
            with self.assertRaises(DatabaseError):
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(f'UPDATE {table} SET {field} = %s WHERE id = %s', [target, row_id])

    def test_direct_sql_cannot_skip_session_binding(self):
        if connection.vendor != 'postgresql':
            self.skipTest('Las guardas SQL de Checkout requieren PostgreSQL.')
        attempt = PaymentAttempt.objects.create(order=self.order, operation_id=uuid.uuid4(),
            request_idempotency_key=uuid.uuid4(), attempt_number=1,
            provider_account_id='acct_synthetic', environment='test',
            amount_minor=49900, currency='MXN')
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE store_paymentattempt SET state = 'session_open', checkout_session_id = 'cs_test_fake', bound_at = now() WHERE id = %s", [attempt.pk])
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE store_order SET state = 'awaiting_payment' WHERE id = %s", [self.order.pk])


class CheckoutConcurrencyTests(TransactionTestCase):
    def test_two_operations_create_one_active_attempt(self):
        if connection.vendor != 'postgresql':
            self.skipTest('La concurrencia requiere PostgreSQL.')
        with tempfile.TemporaryDirectory() as root:
            with override_settings(PRIVATE_PRODUCT_ROOT=Path(root)):
                _, _, order, provider, _ = checkout_fixture(root, 'checkout-concurrent')

                def run():
                    try:
                        return start_checkout(order_id=order.pk, operation_id=uuid.uuid4(),
                            request_idempotency_key=uuid.uuid4(), provider=provider,
                            return_origin='https://example.invalid')
                    except OrderConflict:
                        return None
                    finally:
                        connections.close_all()

                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(lambda _: run(), range(2)))
                self.assertEqual(sum(result is not None for result in results), 1)
                self.assertEqual(PaymentAttempt.objects.filter(order=order).count(), 1)
                self.assertEqual(provider.create_calls, 1)
