"""B-03D: pruebas con Stripe simulado y sesiones PostgreSQL de roles distintos."""

import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from threading import Barrier

import psycopg
from psycopg import sql
from django.contrib import admin
from django.db import connection, connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from store.checkout_services import start_checkout
from store.financial_provider import (ProviderEvent, ProviderIntent, ProviderLine,
                                      ProviderSession, SimulatedFinancialProvider)
from store.financial_services import reconcile_simulated_payment
from store.models import (DeliveryEntitlement, FinancialVerification, Order, OrderAuditEvent,
                          PaymentAttempt, PaymentProviderEvent)
from store.test_checkout_sessions import checkout_fixture
from store.test_webhook_evidence import CONFIG, event_body, signed
from store.webhook_evidence import receive_authenticated_event


class FinancialConfirmationTests(TransactionTestCase):
    databases = {'default'}
    role_passwords = {}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if connection.vendor != 'postgresql':
            return
        cls.role_passwords = {
            'mp_b03d_test_finance': uuid.uuid4().hex,
            'mp_b03d_test_web': uuid.uuid4().hex,
        }
        with connection.cursor() as cursor:
            cursor.execute("""
              DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='mp_b03d_test_finance') THEN
                  CREATE ROLE mp_b03d_test_finance LOGIN;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='mp_b03d_test_web') THEN
                  CREATE ROLE mp_b03d_test_web LOGIN;
                END IF;
              END $$;
              GRANT mp_b03d_executor_test TO mp_b03d_test_finance;
              GRANT USAGE ON SCHEMA public TO mp_b03d_test_web;
              GRANT SELECT, UPDATE ON public.store_order, public.store_paymentattempt,
                public.store_paymentproviderevent TO mp_b03d_test_web;
              GRANT INSERT ON public.store_deliveryentitlement TO mp_b03d_test_web;
            """)
            for role, password in cls.role_passwords.items():
                cursor.execute(sql.SQL('ALTER ROLE {} LOGIN PASSWORD {}').format(
                    sql.Identifier(role), sql.Literal(password)))

    def setUp(self):
        if connection.vendor != 'postgresql':
            self.skipTest('La frontera de roles y concurrencia requiere PostgreSQL.')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings_context = override_settings(PRIVATE_PRODUCT_ROOT=Path(self.temp.name))
        self.settings_context.enable()
        self.addCleanup(self.settings_context.disable)
        self.product, self.version, self.order, checkout_provider, self.file = checkout_fixture(
            self.temp.name, f'finance-{uuid.uuid4().hex}')
        self.operation = uuid.uuid4()
        self.key = uuid.uuid4()
        result = start_checkout(order_id=self.order.pk, operation_id=self.operation,
            request_idempotency_key=self.key, provider=checkout_provider,
            return_origin='https://example.invalid')
        self.attempt_id = result.attempt_id
        self.session_id = result.session_id
        self.intent_id = f'pi_test_{uuid.uuid4().hex}'
        now = timezone.now().replace(microsecond=0)
        self.success_time = now - timedelta(seconds=5)
        self.provider = SimulatedFinancialProvider(account_id='acct_synthetic', environment='test',
            sessions={self.session_id: ProviderSession(self.session_id, 'acct_synthetic', 'test',
                now - timedelta(minutes=1), 'complete', 'paid', 'payment', self.intent_id,
                49900, 'MXN', str(self.order.public_id))},
            intents={self.intent_id: ProviderIntent(self.intent_id, 'acct_synthetic', 'test',
                now - timedelta(minutes=1), 'succeeded', 'automatic', 49900, 49900, 'MXN')},
            lines={self.session_id: (ProviderLine('price_synthetic', 'prod_synthetic', 1, 49900, 'MXN'),)},
            events={'evt_success': ProviderEvent('evt_success', 'acct_synthetic', 'test',
                'payment_intent.succeeded', self.intent_id, self.success_time)})

    def role_connection(self, role):
        config = connection.settings_dict
        conn = psycopg.connect(host=config['HOST'], port=config['PORT'], dbname=config['NAME'],
            user=role, password=self.role_passwords[role], autocommit=True)
        self.addCleanup(conn.close)
        return conn

    def reconcile(self, *, provider_event_id=None, finance=None):
        finance = finance or self.role_connection('mp_b03d_test_finance')
        return reconcile_simulated_payment(order_id=self.order.pk, provider=self.provider,
            finance_connection=finance, provider_event_id=provider_event_id)

    def test_paid_purchase_without_webhook_and_idempotent_retry(self):
        first = self.reconcile()
        self.assertEqual(first.state, 'applied')
        self.order.refresh_from_db()
        attempt = PaymentAttempt.objects.get(pk=self.attempt_id)
        entitlement = DeliveryEntitlement.objects.get(order=self.order)
        self.assertEqual((self.order.state, attempt.state), ('paid', 'succeeded'))
        self.assertEqual(self.order.paid_at, self.success_time)
        self.assertEqual(FinancialVerification.objects.get(state='applied').paid_at_source,
                         'stripe_pi_succeeded_event_created')
        self.assertEqual(entitlement.expires_at, self.success_time + timedelta(hours=336))
        self.assertEqual(entitlement.file_sha256, self.version.sha256)
        self.assertEqual(self.reconcile().entitlement_id, first.entitlement_id)
        self.assertEqual(FinancialVerification.objects.filter(order=self.order).count(), 1)
        self.assertEqual(DeliveryEntitlement.objects.filter(order=self.order).count(), 1)
        self.assertEqual(OrderAuditEvent.objects.filter(order=self.order, action='entitlement_granted').count(), 1)
        self.assertEqual(set(OrderAuditEvent.objects.filter(order=self.order,
            action__in=['paid', 'succeeded', 'entitlement_granted']).values_list(
                'correlation_id', flat=True)), {entitlement.grant_correlation_id})

    def test_signed_session_event_is_applied_only_with_provider_success(self):
        body = event_body(session_id=self.session_id, operation_id=self.operation,
            order_id=self.order.public_id)
        event, _ = receive_authenticated_event(body, signed(body), CONFIG)
        self.assertEqual(event.state, PaymentProviderEvent.State.PENDING)
        result = self.reconcile(provider_event_id=event.pk)
        event.refresh_from_db()
        self.assertEqual(result.state, 'applied')
        self.assertEqual(event.state, PaymentProviderEvent.State.APPLIED)
        self.assertIsNotNone(event.processed_at)

    def test_missing_success_time_and_unavailable_file_do_not_partially_confirm(self):
        self.provider.events.clear()
        result = self.reconcile()
        self.assertEqual((result.state, result.reason), ('review', 'missing_success_event'))
        self.assertEqual(FinancialVerification.objects.get(state='review').paid_at_source, '')
        self.assertFalse(DeliveryEntitlement.objects.exists())
        self.provider.events['evt_success'] = ProviderEvent('evt_success', 'acct_synthetic',
            'test', 'payment_intent.succeeded', self.intent_id, self.success_time)
        self.file.unlink()
        pending = self.reconcile()
        self.assertEqual(pending.state, 'pending_delivery')
        with self.role_connection('mp_b03d_test_finance').cursor() as cursor:
            with self.assertRaises(psycopg.Error):
                cursor.execute('SELECT public.store_b03d_confirm(%s)', (pending.verification_id,))
        self.assertIsNone(self.order.__class__.objects.get(pk=self.order.pk).paid_at)
        self.assertEqual(PaymentAttempt.objects.get(pk=self.attempt_id).state, 'session_open')
        self.file.write_bytes(b'synthetic checkout file')
        self.assertEqual(self.reconcile().state, 'applied')
        self.assertEqual(DeliveryEntitlement.objects.count(), 1)

    def test_web_role_admin_and_sql_cannot_confirm(self):
        self.assertNotIn(Order, admin.site._registry)
        self.assertNotIn(PaymentAttempt, admin.site._registry)
        self.assertNotIn(DeliveryEntitlement, admin.site._registry)
        self.assertNotIn(FinancialVerification, admin.site._registry)
        web = self.role_connection('mp_b03d_test_web')
        with web.cursor() as cursor:
            with self.assertRaises(psycopg.Error):
                cursor.execute('SELECT public.store_b03d_confirm(%s)', (1,))
            with self.assertRaises(psycopg.Error):
                cursor.execute("UPDATE public.store_order SET state='paid', paid_at=now() WHERE id=%s",
                               (self.order.pk,))
            with self.assertRaises(psycopg.Error):
                cursor.execute("UPDATE public.store_paymentattempt SET state='succeeded' WHERE id=%s",
                               (self.attempt_id,))
            with self.assertRaises(psycopg.Error):
                cursor.execute('INSERT INTO public.store_deliveryentitlement(order_id) VALUES (%s)',
                               (self.order.pk,))
        order = Order.objects.get(pk=self.order.pk)
        order.state = Order.State.PAID
        order.paid_at = timezone.now()
        with self.assertRaises(Exception):
            order.save()
        self.assertFalse(DeliveryEntitlement.objects.exists())

    def test_entitlement_insert_failure_rolls_back_every_financial_state(self):
        with connection.cursor() as cursor:
            cursor.execute("""
              CREATE FUNCTION public.b03d_test_entitlement_failure() RETURNS trigger
              LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'synthetic grant failure'; END $$;
              CREATE TRIGGER b03d_test_entitlement_failure_trg BEFORE INSERT
                ON public.store_deliveryentitlement FOR EACH ROW
                EXECUTE FUNCTION public.b03d_test_entitlement_failure();
            """)
        try:
            with self.assertRaises(psycopg.Error):
                self.reconcile()
            self.assertEqual(Order.objects.get(pk=self.order.pk).state, 'awaiting_payment')
            self.assertEqual(PaymentAttempt.objects.get(pk=self.attempt_id).state, 'session_open')
            self.assertFalse(DeliveryEntitlement.objects.exists())
            self.assertEqual(FinancialVerification.objects.get(order=self.order).state, 'ready')
        finally:
            with connection.cursor() as cursor:
                cursor.execute('DROP TRIGGER b03d_test_entitlement_failure_trg ON public.store_deliveryentitlement')
                cursor.execute('DROP FUNCTION public.b03d_test_entitlement_failure()')
        self.assertEqual(self.reconcile().state, 'applied')

    def test_event_application_failure_rolls_back_entitlement(self):
        body = event_body(session_id=self.session_id, operation_id=self.operation,
            order_id=self.order.public_id)
        event, _ = receive_authenticated_event(body, signed(body), CONFIG)
        with connection.cursor() as cursor:
            cursor.execute("""
              CREATE FUNCTION public.b03d_test_event_failure() RETURNS trigger
              LANGUAGE plpgsql AS $$ BEGIN
                IF NEW.state='applied' THEN RAISE EXCEPTION 'synthetic event failure'; END IF;
                RETURN NEW;
              END $$;
              CREATE TRIGGER b03d_test_event_failure_trg BEFORE UPDATE
                ON public.store_paymentproviderevent FOR EACH ROW
                EXECUTE FUNCTION public.b03d_test_event_failure();
            """)
        try:
            with self.assertRaises(psycopg.Error):
                self.reconcile(provider_event_id=event.pk)
            self.assertEqual(Order.objects.get(pk=self.order.pk).state, 'awaiting_payment')
            self.assertEqual(PaymentAttempt.objects.get(pk=self.attempt_id).state, 'session_open')
            self.assertFalse(DeliveryEntitlement.objects.exists())
            event.refresh_from_db()
            self.assertEqual(event.state, 'pending_reconciliation')
        finally:
            with connection.cursor() as cursor:
                cursor.execute('DROP TRIGGER b03d_test_event_failure_trg ON public.store_paymentproviderevent')
                cursor.execute('DROP FUNCTION public.b03d_test_event_failure()')
        self.assertEqual(self.reconcile(provider_event_id=event.pk).state, 'applied')

    def test_contradictory_signed_event_blocks_grant(self):
        body = event_body(event_id='evt_conflict', session_id=self.session_id,
            operation_id=self.operation, order_id=self.order.public_id)
        receive_authenticated_event(body, signed(body), CONFIG)
        changed = event_body(event_id='evt_conflict', session_id=self.session_id,
            operation_id=self.operation, order_id=self.order.public_id, amount=49800)
        receive_authenticated_event(changed, signed(changed), CONFIG)
        self.assertEqual(self.reconcile().reason, 'unresolved_contradiction')
        self.assertEqual(FinancialVerification.objects.get(state='review').reason_code,
                         'unresolved_contradiction')
        self.assertFalse(DeliveryEntitlement.objects.exists())

    def test_provider_commercial_mismatch_and_pending_do_not_grant(self):
        original = self.provider.lines[self.session_id]
        self.provider.lines[self.session_id] = (replace(original[0], quantity=2),)
        self.assertEqual(self.reconcile().reason, 'provider_purchase_mismatch')
        self.provider.lines[self.session_id] = original
        old = self.provider.intents[self.intent_id]
        self.provider.intents[self.intent_id] = replace(old, amount_received=49800)
        self.assertEqual(self.reconcile().reason, 'capture_or_received_mismatch')
        self.assertEqual(FinancialVerification.objects.filter(state='review').count(), 2)
        self.provider.intents[self.intent_id] = replace(old, status='processing')
        self.provider.sessions[self.session_id] = replace(
            self.provider.sessions[self.session_id], payment_status='unpaid')
        self.assertEqual(self.reconcile().state, 'pending')
        self.assertFalse(DeliveryEntitlement.objects.exists())

    def test_provider_outage_and_inconsistent_success_time(self):
        self.provider.fail_next = True
        self.assertEqual(self.reconcile().reason, 'provider_unavailable')
        self.assertFalse(FinancialVerification.objects.exists())
        self.provider.events['evt_success'] = replace(self.provider.events['evt_success'],
            created=timezone.now() + timedelta(hours=1))
        self.assertEqual(self.reconcile().reason, 'success_event_mismatch')
        self.assertEqual(FinancialVerification.objects.get().state, 'review')
        self.assertFalse(DeliveryEntitlement.objects.exists())

    def test_audit_failure_rolls_back_financial_transition(self):
        with connection.cursor() as cursor:
            cursor.execute("""
              CREATE FUNCTION public.b03d_test_audit_failure() RETURNS trigger
              LANGUAGE plpgsql AS $$ BEGIN
                IF NEW.action='entitlement_granted' THEN
                  RAISE EXCEPTION 'synthetic audit failure';
                END IF;
                RETURN NEW;
              END $$;
              CREATE TRIGGER b03d_test_audit_failure_trg BEFORE INSERT
                ON public.store_orderauditevent FOR EACH ROW
                EXECUTE FUNCTION public.b03d_test_audit_failure();
            """)
        try:
            with self.assertRaises(psycopg.Error):
                self.reconcile()
            self.assertEqual(Order.objects.get(pk=self.order.pk).state, 'awaiting_payment')
            self.assertEqual(PaymentAttempt.objects.get(pk=self.attempt_id).state, 'session_open')
            self.assertFalse(DeliveryEntitlement.objects.exists())
            self.assertEqual(FinancialVerification.objects.get(order=self.order).state, 'ready')
        finally:
            with connection.cursor() as cursor:
                cursor.execute('DROP TRIGGER b03d_test_audit_failure_trg ON public.store_orderauditevent')
                cursor.execute('DROP FUNCTION public.b03d_test_audit_failure()')
        self.assertEqual(self.reconcile().state, 'applied')

    def test_two_finance_connections_grant_only_once(self):
        finance = [self.role_connection('mp_b03d_test_finance') for _ in range(2)]
        barrier = Barrier(2)

        def worker(finance_connection):
            barrier.wait(timeout=5)
            try:
                return reconcile_simulated_payment(order_id=self.order.pk, provider=self.provider,
                    finance_connection=finance_connection)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, finance))
        self.assertEqual([result.state for result in results], ['applied', 'applied'])
        self.assertEqual(len({result.entitlement_id for result in results}), 1)
        self.assertEqual(DeliveryEntitlement.objects.filter(order=self.order).count(), 1)
        self.assertEqual(OrderAuditEvent.objects.filter(order=self.order, action='entitlement_granted').count(), 1)
