import uuid
from datetime import timedelta
from unittest import skipUnless

from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, models, transaction
from django.test import TestCase
from django.utils import timezone

from store.models import DeliveryEntitlement, Order, OrderAuditEvent
from store.order_services import create_order, prepare_payment_attempt
from store.test_orders import published_product


class EntitlementFixture:
    def setUp(self):
        self.product = published_product()
        self.order = create_order(product_id=self.product.pk, creation_key=uuid.uuid4(), environment='test')
        self.attempt = prepare_payment_attempt(
            order_id=self.order.pk, operation_id=uuid.uuid4(),
            provider_account_id='acct_synthetic', request_idempotency_key=uuid.uuid4(),
        )

    def candidate(self, **changes):
        paid_at = timezone.now()
        values = dict(
            order=self.order, source_attempt=self.attempt,
            grant_correlation_id=uuid.uuid4(), environment='test',
            paid_at=paid_at, expires_at=paid_at + timedelta(hours=336),
            file_object_identifier=self.order.file_key_snapshot,
            file_version_id='immutable-test-version', file_sha256='a' * 64,
            file_size_bytes=100, download_limit=3, successful_downloads=0,
        )
        values.update(changes)
        return DeliveryEntitlement(**values)


class EntitlementStructureTests(EntitlementFixture, TestCase):
    def test_one_right_per_order_and_attempt_in_schema(self):
        self.assertIsInstance(DeliveryEntitlement._meta.get_field('order'), models.OneToOneField)
        self.assertIsInstance(DeliveryEntitlement._meta.get_field('source_attempt'), models.OneToOneField)
        self.assertEqual(DeliveryEntitlement._meta.get_field('order').remote_field.on_delete.__name__, 'PROTECT')
        self.assertEqual(DeliveryEntitlement._meta.get_field('source_attempt').remote_field.on_delete.__name__, 'PROTECT')

    def test_unpaid_order_and_unconfirmed_attempt_cannot_grant(self):
        before = OrderAuditEvent.objects.count()
        with self.assertRaises(ValidationError):
            self.candidate().save()
        self.assertFalse(DeliveryEntitlement.objects.exists())
        self.assertEqual(OrderAuditEvent.objects.count(), before)

    def test_identity_term_environment_and_limits_are_validated(self):
        for changes, field in (
            ({'environment': 'live'}, 'environment'),
            ({'expires_at': timezone.now()}, 'expires_at'),
            ({'file_object_identifier': ''}, 'file_object_identifier'),
            ({'file_version_id': ''}, 'file_version_id'),
            ({'file_sha256': 'wrong'}, 'file_sha256'),
            ({'file_size_bytes': 0}, 'file_size_bytes'),
            ({'download_limit': 4}, 'download_limit'),
            ({'successful_downloads': 4}, 'successful_downloads'),
            ({'status': 'other'}, 'status'),
        ):
            with self.subTest(field=field), self.assertRaises(ValidationError) as context:
                self.candidate(**changes).full_clean()
            self.assertTrue(
                field in context.exception.message_dict or '__all__' in context.exception.message_dict,
            )

    def test_paid_at_is_order_payment_time_not_webhook_arrival(self):
        right = self.candidate()
        self.assertEqual(right.expires_at - right.paid_at, timedelta(hours=336))
        self.assertIsNone(self.order.paid_at)

    def test_order_file_size_snapshot_is_immutable_in_ordinary_writes(self):
        self.order.file_size_bytes_snapshot = 100
        with self.assertRaises(ValidationError):
            self.order.save()
        with self.assertRaises(ValidationError):
            Order.objects.filter(pk=self.order.pk).update(file_size_bytes_snapshot=100)
        with self.assertRaises(ValidationError):
            Order.objects.bulk_update([self.order], ['file_size_bytes_snapshot'])
        self.order.refresh_from_db()
        self.assertIsNone(self.order.file_size_bytes_snapshot)

    def test_no_bulk_grant_or_ordinary_mutation(self):
        with self.assertRaises(ValidationError):
            DeliveryEntitlement.objects.bulk_create([self.candidate()])
        with self.assertRaises(ValidationError):
            DeliveryEntitlement.objects.all().update(status='revoked')
        with self.assertRaises(ValidationError):
            DeliveryEntitlement.objects.bulk_update([self.candidate()], ['status'])
        self.assertFalse(DeliveryEntitlement.objects.exists())


@skipUnless(connection.vendor == 'postgresql', 'La guarda SQL requiere PostgreSQL.')
class PostgreSQLEntitlementGuardTests(EntitlementFixture, TestCase):
    def test_direct_sql_cannot_change_order_snapshot(self):
        with self.assertRaises(DatabaseError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    'UPDATE store_order SET file_size_bytes_snapshot = 100 WHERE id = %s',
                    [self.order.pk],
                )
        self.order.refresh_from_db()
        self.assertIsNone(self.order.file_size_bytes_snapshot)

    def test_direct_sql_cannot_grant_unpaid_order(self):
        right = self.candidate()
        with self.assertRaises(DatabaseError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    '''INSERT INTO store_deliveryentitlement
                       (order_id, source_attempt_id, grant_correlation_id, environment,
                        status, paid_at, expires_at, file_object_identifier,
                        file_version_id, file_sha256, file_size_bytes,
                        download_limit, successful_downloads, status_reason_code,
                        created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                               %s, %s, %s, %s, %s, %s, %s, %s)''',
                    [self.order.pk, self.attempt.pk, str(right.grant_correlation_id),
                     right.environment, right.status, right.paid_at, right.expires_at,
                     right.file_object_identifier, right.file_version_id, right.file_sha256,
                     right.file_size_bytes, 3, 0, '', timezone.now(), timezone.now()],
                )
        self.assertFalse(DeliveryEntitlement.objects.exists())
