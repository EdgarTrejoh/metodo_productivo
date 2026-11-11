import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, connection, connections, transaction
from django.db.models import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from content.models import PublicationStatus
from store.models import DeliveryEntitlement, DigitalProduct, Order, OrderAuditEvent, PaymentAttempt
from store.order_services import (
    InvalidOrderOperation, OrderConflict, close_unpaid_order, create_order,
    expire_prepared_attempt, get_order_by_creation_key, prepare_payment_attempt,
    validate_attempt_transition, validate_order_transition, _minor_units,
)


def published_product(*, slug='synthetic-product', price=Decimal('499.00')):
    return DigitalProduct.objects.create(
        name='Producto sintético', slug=slug, summary='Resumen sintético',
        description='Descripción sintética.', benefits='Beneficio sintético.',
        version='1.0', software_requirements='Hoja de cálculo.',
        contents='Libro de prueba.', delivery_terms='Términos sintéticos.',
        price=price, currency='MXN', stripe_environment='test',
        private_file_key='archivo-logico-sintetico',
        status=PublicationStatus.PUBLISHED,
    )


class OrderCoreTests(TestCase):
    def setUp(self):
        self.product = published_product()
        self.key = uuid.uuid4()

    def order(self, key=None):
        return create_order(product_id=self.product.pk, creation_key=key or self.key, environment='test')

    def attempt(self, order=None, operation=None):
        return prepare_payment_attempt(
            order_id=(order or self.order()).pk, operation_id=operation or uuid.uuid4(),
            provider_account_id='acct_synthetic', request_idempotency_key=uuid.uuid4(),
        )

    def test_one_product_and_quantity_one_in_schema(self):
        order = self.order()
        self.assertEqual(order.product, self.product)
        self.assertFalse(any(field.name == 'quantity' for field in Order._meta.fields))
        self.assertFalse(any(model.__name__ == 'OrderLine' for model in Order._meta.apps.get_models()))
        self.assertFalse(Order._meta.get_field('product').null)
        with self.assertRaises(ProtectedError):
            self.product.delete()

    def test_snapshot_survives_catalog_change_and_repetition(self):
        order = self.order()
        self.product.name = 'Nombre nuevo'
        self.product.version = '2.0'
        self.product.price = Decimal('750.00')
        self.product.delivery_terms = 'Términos nuevos.'
        self.product.private_file_key = 'otro-archivo'
        self.product.save()
        repeated = self.order()
        self.assertEqual(repeated.pk, order.pk)
        self.assertEqual(order.product_name_snapshot, 'Producto sintético')
        self.assertEqual(order.product_version_snapshot, '1.0')
        self.assertEqual(order.amount_minor, 49900)
        self.assertEqual(order.delivery_terms_snapshot, 'Términos sintéticos.')
        self.assertEqual(order.file_key_snapshot, 'archivo-logico-sintetico')
        self.assertEqual(order.file_revision_snapshot, '')
        self.assertEqual(order.file_sha256_snapshot, '')
        order.amount_minor = 75000
        with self.assertRaises(ValidationError):
            order.save()

    def test_creation_idempotency_and_new_purchase(self):
        first = self.order()
        self.assertEqual(self.order().pk, first.pk)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderAuditEvent.objects.filter(order=first, action='created').count(), 1)
        self.assertEqual(get_order_by_creation_key(
            creation_key=self.key, product_id=self.product.pk, environment='test').pk, first.pk)
        with self.assertRaises(OrderConflict):
            create_order(product_id=self.product.pk, creation_key=self.key, environment='live')
        second = self.order(uuid.uuid4())
        self.assertNotEqual(second.pk, first.pk)

    def test_mxn_exact_centavos_and_published_catalog(self):
        self.assertEqual(self.order().amount_minor, 49900)
        self.assertEqual(_minor_units(Decimal('1.01')), 101)
        for invalid in (Decimal('1.001'), Decimal('0'), Decimal('-1.00'), Decimal('NaN')):
            with self.assertRaises(InvalidOrderOperation):
                _minor_units(invalid)
        self.product.currency = 'USD'
        self.product.save()
        with self.assertRaises(InvalidOrderOperation):
            self.order(uuid.uuid4())
        self.product.currency = 'MXN'
        self.product.price = Decimal('1.00')
        self.product.status = PublicationStatus.DRAFT
        self.product.save()
        with self.assertRaises(InvalidOrderOperation):
            self.order(uuid.uuid4())

    def test_attempt_idempotency_active_limit_expiry_and_closed_order(self):
        order = self.order()
        operation = uuid.uuid4()
        key = uuid.uuid4()
        first = prepare_payment_attempt(
            order_id=order.pk, operation_id=operation, provider_account_id='acct_synthetic',
            request_idempotency_key=key)
        repeated = prepare_payment_attempt(
            order_id=order.pk, operation_id=operation, provider_account_id='acct_synthetic',
            request_idempotency_key=key)
        self.assertEqual(first.pk, repeated.pk)
        with self.assertRaises(OrderConflict):
            self.attempt(order)
        expire_prepared_attempt(attempt_id=first.pk)
        second = self.attempt(order)
        self.assertEqual(second.attempt_number, 2)
        with self.assertRaises(InvalidOrderOperation):
            close_unpaid_order(order_id=order.pk)
        expire_prepared_attempt(attempt_id=second.pk)
        close_unpaid_order(order_id=order.pk)
        with self.assertRaises(InvalidOrderOperation):
            self.attempt(order)
        self.assertEqual(OrderAuditEvent.objects.filter(order=order).count(), 6)

    def test_invalid_transitions_and_no_payment_authority(self):
        self.order()
        with self.assertRaises(InvalidOrderOperation):
            validate_order_transition(Order.State.CREATED, Order.State.PAID)
        with self.assertRaises(InvalidOrderOperation):
            validate_attempt_transition(PaymentAttempt.State.PREPARED, PaymentAttempt.State.SUCCEEDED)
        with self.assertRaises(InvalidOrderOperation):
            validate_order_transition(Order.State.CLOSED_UNPAID, Order.State.CREATED)
        self.assertEqual(Order.objects.filter(state=Order.State.PAID).count(), 0)
        self.assertEqual(PaymentAttempt.objects.filter(state=PaymentAttempt.State.SUCCEEDED).count(), 0)

    def test_unique_external_references_and_request_key(self):
        order = self.order()
        first = self.attempt(order)
        expire_prepared_attempt(attempt_id=first.pk)
        second = self.attempt(order)
        PaymentAttempt.objects.filter(pk=first.pk).update(checkout_session_id='cs_test_synthetic')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PaymentAttempt.objects.filter(pk=second.pk).update(checkout_session_id='cs_test_synthetic')
        with self.assertRaises(ValidationError):
            PaymentAttempt.objects.filter(pk=second.pk).update(request_idempotency_key=first.request_idempotency_key)

    def test_attempt_amount_and_environment_match_order(self):
        attempt = self.attempt()
        attempt.amount_minor += 1
        with self.assertRaises(ValidationError):
            attempt.save()
        attempt.refresh_from_db()
        attempt.environment = 'live'
        with self.assertRaises(ValidationError):
            attempt.save()

    def test_no_delivery_right_is_created(self):
        order = self.order()
        self.attempt(order)
        self.assertEqual(order.state, Order.State.CREATED)
        self.assertEqual(order.payment_attempts.count(), 1)
        self.assertFalse(DeliveryEntitlement.objects.filter(order=order).exists())


class OrderIntegrityR01Tests(TransactionTestCase):
    def setUp(self):
        self.product = published_product()
        self.order = create_order(
            product_id=self.product.pk, creation_key=uuid.uuid4(), environment='test')

    def test_snapshot_rejects_save_update_and_bulk_update(self):
        self.order.product_name_snapshot = 'Otro nombre'
        with self.assertRaises(ValidationError):
            self.order.save()
        with self.assertRaises(ValidationError):
            Order.objects.filter(pk=self.order.pk).update(product_name_snapshot='Otro nombre')
        with self.assertRaises(ValidationError):
            Order.objects.bulk_update([self.order], ['product_name_snapshot'])
        with self.assertRaises(ValidationError):
            Order.objects.bulk_create([self.order])
        self.order.refresh_from_db()
        self.assertEqual(self.order.product_name_snapshot, 'Producto sintético')

    def test_order_state_rejects_save_update_and_bulk_update(self):
        self.order.state = Order.State.PAID
        self.order.paid_at = timezone.now()
        with self.assertRaises(ValidationError):
            self.order.save()
        with self.assertRaises(ValidationError):
            Order.objects.filter(pk=self.order.pk).update(state=Order.State.PAID, paid_at=timezone.now())
        with self.assertRaises(ValidationError):
            Order.objects.bulk_update([self.order], ['state'])
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, Order.State.CREATED)
        self.assertFalse(OrderAuditEvent.objects.filter(order=self.order, to_state=Order.State.PAID).exists())

    def test_closed_order_cannot_reactivate_or_create_attempt(self):
        close_unpaid_order(order_id=self.order.pk, reason='local_timeout')
        self.order.refresh_from_db()
        self.order.state = Order.State.CREATED
        with self.assertRaises(ValidationError):
            self.order.save()
        with self.assertRaises(ValidationError):
            Order.objects.filter(pk=self.order.pk).update(state=Order.State.CREATED)
        with self.assertRaises(ValidationError):
            PaymentAttempt.objects.create(
                order=self.order, operation_id=uuid.uuid4(),
                request_idempotency_key=uuid.uuid4(), attempt_number=1,
                provider_account_id='acct_synthetic', environment='test',
                amount_minor=self.order.amount_minor, currency='MXN',
            )
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, Order.State.CLOSED_UNPAID)
        self.assertEqual(OrderAuditEvent.objects.filter(order=self.order, action='closed_unpaid').count(), 1)

    def test_attempt_state_rejects_save_update_bulk_update_and_regression(self):
        attempt = prepare_payment_attempt(
            order_id=self.order.pk, operation_id=uuid.uuid4(),
            provider_account_id='acct_synthetic', request_idempotency_key=uuid.uuid4())
        attempt.state = PaymentAttempt.State.SUCCEEDED
        with self.assertRaises(ValidationError):
            attempt.save()
        with self.assertRaises(ValidationError):
            PaymentAttempt.objects.filter(pk=attempt.pk).update(state=PaymentAttempt.State.SUCCEEDED)
        with self.assertRaises(ValidationError):
            PaymentAttempt.objects.bulk_update([attempt], ['state'])
        attempt.refresh_from_db()
        expire_prepared_attempt(attempt_id=attempt.pk, reason='local_timeout')
        attempt.refresh_from_db()
        attempt.state = PaymentAttempt.State.PREPARED
        with self.assertRaises(ValidationError):
            attempt.save()
        self.assertEqual(OrderAuditEvent.objects.filter(
            order=self.order, attempt=attempt, action='expired').count(), 1)
        self.assertFalse(OrderAuditEvent.objects.filter(
            order=self.order, attempt=attempt, to_state=PaymentAttempt.State.SUCCEEDED).exists())

    def test_audit_events_reject_ordinary_edit_and_delete(self):
        event = OrderAuditEvent.objects.get(order=self.order, action='created')
        event.reason = 'changed'
        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            event.delete()
        with self.assertRaises(ValidationError):
            OrderAuditEvent.objects.filter(pk=event.pk).update(reason='changed')
        with self.assertRaises(ValidationError):
            OrderAuditEvent.objects.filter(pk=event.pk).delete()

    def test_audit_failure_rolls_back_state(self):
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute(
                    "ALTER TABLE store_orderauditevent ADD CONSTRAINT store_r01_test_audit_failure "
                    "CHECK (action <> 'closed_unpaid')")
            try:
                with self.assertRaises(DatabaseError):
                    with transaction.atomic():
                        close_unpaid_order(order_id=self.order.pk)
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(
                        'ALTER TABLE store_orderauditevent DROP CONSTRAINT store_r01_test_audit_failure')
        else:
            with patch('store.order_services._audit', side_effect=RuntimeError('synthetic_audit_failure')):
                with self.assertRaises(RuntimeError):
                    close_unpaid_order(order_id=self.order.pk)
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, Order.State.CREATED)
        self.assertFalse(OrderAuditEvent.objects.filter(order=self.order, action='closed_unpaid').exists())


@skipUnless(connection.vendor == 'postgresql', 'Los triggers SQL R01 se verifican únicamente en PostgreSQL.')
class PostgresIntegrityR01Tests(TransactionTestCase):
    def setUp(self):
        self.product = published_product()
        self.order = create_order(
            product_id=self.product.pk, creation_key=uuid.uuid4(), environment='test')

    def sql_update(self, table, assignment, pk):
        with connection.cursor() as cursor:
            cursor.execute(f'UPDATE {table} SET {assignment} WHERE id = %s', [pk])

    def test_sql_rejects_snapshot_and_unverified_payment(self):
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                self.sql_update('store_order', "product_name_snapshot = 'changed'", self.order.pk)
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                self.sql_update('store_order', "state = 'paid', paid_at = now()", self.order.pk)
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, Order.State.CREATED)
        self.assertEqual(self.order.product_name_snapshot, 'Producto sintético')
        self.assertFalse(OrderAuditEvent.objects.filter(order=self.order, to_state=Order.State.PAID).exists())

    def test_sql_authorized_close_is_audited_and_cannot_reactivate(self):
        self.sql_update('store_order', "state = 'closed_unpaid', closed_at = now()", self.order.pk)
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, Order.State.CLOSED_UNPAID)
        self.assertEqual(OrderAuditEvent.objects.filter(order=self.order, action='closed_unpaid').count(), 1)
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                self.sql_update('store_order', "state = 'created'", self.order.pk)
        self.assertEqual(OrderAuditEvent.objects.filter(order=self.order).count(), 2)
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO store_paymentattempt
                        (order_id, operation_id, request_idempotency_key, attempt_number,
                         provider, provider_account_id, environment, state,
                         checkout_session_id, payment_intent_id, amount_minor, currency,
                         result_code, created_at, updated_at)
                        VALUES (%s, %s, %s, 1, 'stripe', 'acct_synthetic', 'test',
                                'prepared', '', '', %s, 'MXN', '', now(), now())""",
                        [self.order.pk, str(uuid.uuid4()), str(uuid.uuid4()),
                         self.order.amount_minor],
                    )
        self.assertFalse(PaymentAttempt.objects.filter(order=self.order).exists())

    def test_sql_rejects_succeeded_and_terminal_regression(self):
        attempt = prepare_payment_attempt(
            order_id=self.order.pk, operation_id=uuid.uuid4(),
            provider_account_id='acct_synthetic', request_idempotency_key=uuid.uuid4())
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                self.sql_update('store_paymentattempt', "state = 'succeeded', completed_at = now()", attempt.pk)
        self.sql_update('store_paymentattempt',
                        "state = 'expired', completed_at = now(), result_code = 'local_timeout'",
                        attempt.pk)
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                self.sql_update('store_paymentattempt', "state = 'prepared'", attempt.pk)
        self.assertEqual(OrderAuditEvent.objects.filter(
            order=self.order, attempt=attempt, action='expired').count(), 1)

    def test_sql_cannot_edit_or_delete_audit(self):
        event = OrderAuditEvent.objects.get(order=self.order, action='created')
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                self.sql_update('store_orderauditevent', "reason = 'changed'", event.pk)
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('DELETE FROM store_orderauditevent WHERE id = %s', [event.pk])

@skipUnless(connection.vendor == 'postgresql', 'Concurrencia de escritura obligatoria en PostgreSQL; SQLite no ofrece bloqueo de fila.')
class OrderConcurrencyTests(TransactionTestCase):
    def test_same_creation_key_produces_one_order(self):
        product = published_product()
        creation_key = uuid.uuid4()
        barrier = Barrier(2)

        def worker():
            connections.close_all()
            barrier.wait(timeout=10)
            try:
                return create_order(product_id=product.pk, creation_key=creation_key, environment='test').pk
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderAuditEvent.objects.count(), 1)

    def test_simultaneous_attempts_leave_one_active(self):
        product = published_product()
        order = create_order(product_id=product.pk, creation_key=uuid.uuid4(), environment='test')
        barrier = Barrier(2)

        def worker():
            connections.close_all()
            barrier.wait(timeout=10)
            try:
                return prepare_payment_attempt(
                    order_id=order.pk, operation_id=uuid.uuid4(),
                    provider_account_id='acct_synthetic', request_idempotency_key=uuid.uuid4()).pk
            except OrderConflict:
                return None
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(PaymentAttempt.objects.filter(order=order, state=PaymentAttempt.State.PREPARED).count(), 1)
