"""B-03D: test-only financial executor; ordinary SQL remains blocked.

Role membership is cluster-wide and deliberately survives migration reversal.
The schema objects and prior trigger bodies are reversible.
"""

import importlib
import re

from django.db import migrations


OWNER = 'mp_b03d_owner'
EXECUTOR = 'mp_b03d_executor_test'
AUTH = "current_user = 'mp_b03d_owner' AND pg_has_role(session_user, 'mp_b03d_executor_test', 'member')"


def _function(source, name):
    match = re.search(r'CREATE (?:OR REPLACE )?FUNCTION ' + name + r'\(\).*?END \$\$;', source, re.S)
    if not match:
        raise RuntimeError(f'Falta la función anterior {name}.')
    return (match.group().replace('CREATE FUNCTION', 'CREATE OR REPLACE FUNCTION', 1)
            .replace('%%ROWTYPE', '%ROWTYPE'))


def _replace(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError('Cambió la definición previa de una guarda B-03D.')
    return source.replace(old, new, 1)


def _install_roles(cursor):
    cursor.execute("""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mp_b03d_owner') THEN
            CREATE ROLE mp_b03d_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
          END IF;
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mp_b03d_executor_test') THEN
            CREATE ROLE mp_b03d_executor_test NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname IN ('mp_b03d_owner', 'mp_b03d_executor_test')
                     AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls)) THEN
            RAISE EXCEPTION 'B-03D requires restricted NOLOGIN roles';
          END IF;
        END $$;
        REVOKE CREATE ON SCHEMA public FROM PUBLIC;
        GRANT USAGE ON SCHEMA public TO mp_b03d_owner, mp_b03d_executor_test;
        GRANT CREATE ON SCHEMA public TO mp_b03d_owner;
        GRANT SELECT ON public.store_order, public.store_paymentattempt,
          public.store_checkoutrequest, public.store_paymentproviderevent,
          public.store_financialverification, public.store_deliveryentitlement,
          public.store_productfileversion TO mp_b03d_owner;
        GRANT UPDATE ON public.store_order, public.store_paymentattempt,
          public.store_checkoutrequest, public.store_paymentproviderevent,
          public.store_financialverification, public.store_deliveryentitlement TO mp_b03d_owner;
        GRANT INSERT ON public.store_financialverification, public.store_deliveryentitlement,
          public.store_orderauditevent TO mp_b03d_owner;
        GRANT USAGE, SELECT ON SEQUENCE public.store_financialverification_id_seq,
          public.store_deliveryentitlement_id_seq, public.store_orderauditevent_id_seq TO mp_b03d_owner;
    """)


def _extend_guards(cursor):
    previous = importlib.import_module('store.migrations.0012_b03b_checkout_guards').FORWARD
    order = _function(previous, 'store_r01_order_guard')
    order = _replace(order,
        "IF NEW.paid_at IS DISTINCT FROM OLD.paid_at THEN\n        RAISE EXCEPTION 'B-02A: payment confirmation is unavailable';\n    END IF;",
        """IF NEW.paid_at IS DISTINCT FROM OLD.paid_at AND NOT (
        """ + AUTH + """ AND OLD.state = 'awaiting_payment' AND NEW.state = 'paid'
        AND NEW.paid_at IS NOT NULL AND EXISTS (
          SELECT 1 FROM public.store_financialverification f
          JOIN public.store_paymentattempt a ON a.id = f.attempt_id
          WHERE f.order_id = OLD.id AND f.state = 'ready'
            AND f.paid_at = NEW.paid_at AND a.state = 'succeeded'
            AND a.payment_intent_id = f.payment_intent_id
        )) THEN
        RAISE EXCEPTION 'B-02A: payment confirmation is unavailable';
    END IF;""")
    order = _replace(order,
        "IF OLD.state = 'created' AND NEW.state = 'awaiting_payment' THEN",
        """IF OLD.state = 'awaiting_payment' AND NEW.state = 'paid' THEN
            IF NOT (""" + AUTH + """ AND NEW.paid_at IS NOT NULL
                AND OLD.closed_at IS NULL AND NEW.closed_at IS NULL
                AND NEW.closed_reason = '') THEN
                RAISE EXCEPTION 'B-03D: unauthorized paid order';
            END IF;
        ELSIF OLD.state = 'created' AND NEW.state = 'awaiting_payment' THEN""")
    cursor.execute(order)

    attempt = _function(previous, 'store_r01_attempt_guard')
    attempt = _replace(attempt,
        "IF OLD.state = 'prepared' AND NEW.state = 'session_open' THEN",
        """IF OLD.state = 'session_open' AND NEW.state = 'succeeded' THEN
            IF NOT (""" + AUTH + """ AND NEW.payment_intent_id <> ''
                AND NEW.completed_at IS NOT NULL AND NEW.result_code = 'provider_paid'
                AND EXISTS (SELECT 1 FROM public.store_financialverification f
                    WHERE f.attempt_id = OLD.id AND f.order_id = OLD.order_id
                      AND f.state = 'ready' AND f.paid_at = NEW.completed_at
                      AND f.payment_intent_id = NEW.payment_intent_id
                      AND f.session_id = OLD.checkout_session_id)
                AND EXISTS (SELECT 1 FROM public.store_order o
                    WHERE o.id = OLD.order_id AND o.state = 'awaiting_payment')) THEN
                RAISE EXCEPTION 'B-03D: unauthorized successful attempt';
            END IF;
        ELSIF OLD.state = 'prepared' AND NEW.state = 'session_open' THEN""")
    attempt = _replace(attempt,
        "OR NEW.checkout_session_id IS DISTINCT FROM OLD.checkout_session_id\n       OR NEW.bound_at IS DISTINCT FROM OLD.bound_at THEN",
        "OR NEW.checkout_session_id IS DISTINCT FROM OLD.checkout_session_id\n       OR NEW.payment_intent_id IS DISTINCT FROM OLD.payment_intent_id\n       OR NEW.bound_at IS DISTINCT FROM OLD.bound_at THEN")
    cursor.execute(attempt)

    order_audit = _function(previous, 'store_r01_order_audit')
    order_audit = _replace(order_audit,
        "CASE WHEN NEW.state = 'awaiting_payment' THEN 'awaiting_payment' ELSE 'closed_unpaid' END,",
        "CASE WHEN NEW.state = 'awaiting_payment' THEN 'awaiting_payment' WHEN NEW.state = 'paid' THEN 'paid' ELSE 'closed_unpaid' END,")
    order_audit = _replace(order_audit,
        "OLD.state, NEW.state, NEW.closed_reason, NULL, now());",
        """OLD.state, NEW.state, NEW.closed_reason,
            CASE WHEN NEW.state = 'paid' THEN
              (SELECT f.source_key FROM public.store_financialverification f
               WHERE f.order_id = NEW.id AND f.state = 'ready'
               ORDER BY f.checked_at DESC LIMIT 1)
            ELSE NULL END, now());""")
    cursor.execute(order_audit)
    attempt_audit = _function(previous, 'store_r01_attempt_audit')
    attempt_audit = _replace(attempt_audit,
        "CASE WHEN NEW.state = 'session_open' THEN 'session_open' ELSE 'expired' END,",
        "CASE WHEN NEW.state = 'session_open' THEN 'session_open' WHEN NEW.state = 'succeeded' THEN 'succeeded' ELSE 'expired' END,")
    attempt_audit = _replace(attempt_audit,
        "OLD.state, NEW.state, NEW.result_code, NEW.operation_id, now());",
        """OLD.state, NEW.state, NEW.result_code,
            CASE WHEN NEW.state = 'succeeded' THEN
              (SELECT f.source_key FROM public.store_financialverification f
               WHERE f.attempt_id = NEW.id AND f.state = 'ready'
               ORDER BY f.checked_at DESC LIMIT 1)
            ELSE NEW.operation_id END, now());""")
    cursor.execute(attempt_audit)

    entitlement = _function(importlib.import_module('store.migrations.0006_b02b_entitlement_guards').SQL,
                            'store_b02b_entitlement_guard')
    entitlement = _replace(entitlement, "    -- El orden de bloqueo coincide con B-02A: orden antes que intento.",
        "    IF NOT (" + AUTH + ") THEN RAISE EXCEPTION 'B-03D: restricted entitlement grant'; END IF;\n\n"
        "    -- El orden de bloqueo coincide con B-02A: orden antes que intento.")
    cursor.execute(entitlement)

    evidence = _function(importlib.import_module('store.migrations.0014_b03c_evidence_guards').SQL,
                         'store_b03c_evidence_guard')
    evidence = _replace(evidence,
        "IF NEW.processed_at IS NOT NULL OR NEW.state = 'applied'\n       OR (OLD.state = 'contradiction' AND NEW.state <> 'contradiction')",
        """IF (NEW.state = 'applied' OR NEW.processed_at IS NOT NULL) AND NOT (
        """ + AUTH + """ AND OLD.state = 'pending_reconciliation'
        AND NEW.state = 'applied' AND OLD.processed_at IS NULL
        AND NEW.processed_at IS NOT NULL AND EXISTS (
            SELECT 1 FROM public.store_financialverification f
            JOIN public.store_deliveryentitlement d ON d.order_id = f.order_id
            WHERE f.provider_event_id = OLD.id AND f.state = 'ready'
              AND d.source_attempt_id = f.attempt_id
        )) OR (OLD.state = 'contradiction' AND NEW.state <> 'contradiction')""")
    cursor.execute(evidence)


SQL = """
CREATE FUNCTION public.store_b03d_verification_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'B-03D: verification is durable'; END IF;
  IF NOT (current_user = 'mp_b03d_owner' AND
          pg_has_role(session_user, 'mp_b03d_executor_test', 'member')) THEN
    RAISE EXCEPTION 'B-03D: restricted verification';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.state NOT IN ('review', 'pending_delivery', 'ready') OR NEW.applied_at IS NOT NULL
       OR (NEW.state IN ('pending_delivery', 'ready') AND
           (NEW.paid_at IS NULL OR NEW.success_event_id = '')) THEN
      RAISE EXCEPTION 'B-03D: invalid initial verification';
    END IF;
  ELSIF ROW(NEW.source_key, NEW.order_id, NEW.attempt_id, NEW.provider_event_id,
             NEW.provider_account_id, NEW.environment, NEW.session_id,
             NEW.payment_intent_id, NEW.success_event_id, NEW.paid_at,
             NEW.paid_at_source,
             NEW.amount_minor, NEW.currency, NEW.price_id, NEW.product_id,
             NEW.quantity, NEW.reason_code, NEW.checked_at)
       IS DISTINCT FROM ROW(OLD.source_key, OLD.order_id, OLD.attempt_id,
             OLD.provider_event_id, OLD.provider_account_id, OLD.environment,
             OLD.session_id, OLD.payment_intent_id, OLD.success_event_id,
             OLD.paid_at, OLD.paid_at_source, OLD.amount_minor, OLD.currency, OLD.price_id,
             OLD.product_id, OLD.quantity, OLD.reason_code, OLD.checked_at)
       OR OLD.state <> 'ready' OR NEW.state <> 'applied'
       OR NEW.applied_at IS NULL OR OLD.applied_at IS NOT NULL
       OR NOT EXISTS (SELECT 1 FROM public.store_deliveryentitlement d
           WHERE d.order_id = NEW.order_id AND d.source_attempt_id = NEW.attempt_id) THEN
    RAISE EXCEPTION 'B-03D: verification is immutable';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER store_b03d_verification_guard_trg BEFORE INSERT OR UPDATE OR DELETE
ON public.store_financialverification FOR EACH ROW
EXECUTE FUNCTION public.store_b03d_verification_guard();

CREATE FUNCTION public.store_b03d_record(
  p_key uuid, p_order bigint, p_attempt bigint, p_event bigint,
  p_account text, p_environment text, p_session text, p_intent text,
  p_success_event text, p_paid_at timestamptz, p_amount bigint,
  p_currency text, p_price text, p_product text, p_quantity integer,
  p_state text, p_reason text
) RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE v_order public.store_order%ROWTYPE;
        v_attempt public.store_paymentattempt%ROWTYPE;
        v_request public.store_checkoutrequest%ROWTYPE;
        v_existing public.store_financialverification%ROWTYPE;
        v_id bigint;
BEGIN
  IF NOT pg_has_role(session_user, 'mp_b03d_executor_test', 'member')
     OR p_environment <> 'test' OR p_state NOT IN ('review','pending_delivery','ready')
     OR p_reason !~ '^[a-z0-9_]{0,80}$' THEN
    RAISE EXCEPTION 'B-03D: unauthorized verification';
  END IF;
  SELECT * INTO v_order FROM public.store_order WHERE id=p_order FOR UPDATE;
  SELECT * INTO v_attempt FROM public.store_paymentattempt WHERE id=p_attempt FOR UPDATE;
  SELECT * INTO v_request FROM public.store_checkoutrequest WHERE attempt_id=p_attempt FOR UPDATE;
  IF v_order.id IS NULL OR v_attempt.id IS NULL OR v_request.id IS NULL
     OR v_attempt.order_id <> v_order.id OR v_order.state <> 'awaiting_payment'
     OR v_attempt.state <> 'session_open' OR v_request.state <> 'bound'
     OR v_request.session_id <> p_session OR v_attempt.checkout_session_id <> p_session
     OR v_attempt.provider_account_id <> p_account
     OR v_attempt.environment <> p_environment OR v_order.environment <> p_environment
     OR v_attempt.amount_minor <> p_amount OR v_order.amount_minor <> p_amount
     OR v_attempt.currency <> p_currency OR v_order.currency <> p_currency
     OR v_order.stripe_price_id_snapshot <> p_price
     OR v_order.stripe_product_id_snapshot <> p_product OR p_quantity <> 1
     OR p_intent = '' OR p_session = ''
     OR (p_state IN ('pending_delivery','ready') AND (p_paid_at IS NULL OR p_success_event=''))
     OR (p_state='ready' AND p_reason <> '')
     OR (p_state IN ('review','pending_delivery') AND p_reason = '')
     OR (p_paid_at IS NOT NULL AND p_paid_at > now() + interval '5 minutes')
     OR (p_event IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM public.store_paymentproviderevent e
          WHERE e.id=p_event AND e.external_object_id=p_session
            AND e.provider_account_id=p_account AND e.environment=p_environment
            AND e.state='pending_reconciliation'
            AND (e.attempt_id IS NULL OR e.attempt_id=p_attempt))) THEN
    RAISE EXCEPTION 'B-03D: verification does not match checkout';
  END IF;
  SELECT * INTO v_existing FROM public.store_financialverification
    WHERE source_key=p_key FOR UPDATE;
  IF v_existing.id IS NOT NULL THEN
    IF v_existing.order_id <> p_order OR v_existing.attempt_id <> p_attempt
       OR v_existing.session_id <> p_session OR v_existing.payment_intent_id <> p_intent
       OR v_existing.success_event_id <> p_success_event
       OR v_existing.paid_at IS DISTINCT FROM p_paid_at
       OR v_existing.provider_event_id IS DISTINCT FROM p_event
       OR v_existing.state NOT IN ('review','pending_delivery','ready','applied') THEN
      RAISE EXCEPTION 'B-03D: conflicting verification key';
    END IF;
    RETURN v_existing.id;
  END IF;
  INSERT INTO public.store_financialverification
    (source_key, order_id, attempt_id, provider_event_id, provider_account_id,
     environment, session_id, payment_intent_id, success_event_id, paid_at,
     paid_at_source, amount_minor, currency, price_id, product_id, quantity, state,
     reason_code, checked_at)
  VALUES (p_key, p_order, p_attempt, p_event, p_account, p_environment,
     p_session, p_intent, p_success_event, p_paid_at,
     CASE WHEN p_paid_at IS NULL THEN '' ELSE 'stripe_pi_succeeded_event_created' END,
     p_amount, p_currency, p_price, p_product, p_quantity, p_state, p_reason, now()) RETURNING id INTO v_id;
  INSERT INTO public.store_orderauditevent
    (order_id, attempt_id, operation_id, subject, actor, actor_ref,
     action, from_state, to_state, reason, correlation_id, occurred_at)
  VALUES (p_order, p_attempt, gen_random_uuid(), 'attempt', 'system',
     'finance_test', 'financial_verification', '', p_state, p_reason, p_key, now());
  RETURN v_id;
END $$;

CREATE FUNCTION public.store_b03d_confirm(p_verification bigint) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE v_order public.store_order%ROWTYPE;
        v_attempt public.store_paymentattempt%ROWTYPE;
        v_request public.store_checkoutrequest%ROWTYPE;
        v_check public.store_financialverification%ROWTYPE;
        v_event public.store_paymentproviderevent%ROWTYPE;
        v_entitlement public.store_deliveryentitlement%ROWTYPE;
        v_order_id bigint;
BEGIN
  IF NOT pg_has_role(session_user, 'mp_b03d_executor_test', 'member') THEN
    RAISE EXCEPTION 'B-03D: unauthorized confirmation';
  END IF;
  SELECT order_id INTO v_order_id FROM public.store_financialverification
     WHERE id=p_verification;
  SELECT * INTO v_order FROM public.store_order WHERE id=v_order_id FOR UPDATE;
  SELECT * INTO v_attempt FROM public.store_paymentattempt
     WHERE id=(SELECT attempt_id FROM public.store_financialverification
               WHERE id=p_verification) FOR UPDATE;
  SELECT * INTO v_request FROM public.store_checkoutrequest
     WHERE attempt_id=v_attempt.id FOR UPDATE;
  SELECT * INTO v_check FROM public.store_financialverification
     WHERE id=p_verification FOR UPDATE;
  IF v_check.provider_event_id IS NOT NULL THEN
    SELECT * INTO v_event FROM public.store_paymentproviderevent
       WHERE id=v_check.provider_event_id FOR UPDATE;
  END IF;
  SELECT * INTO v_entitlement FROM public.store_deliveryentitlement
     WHERE order_id=v_order.id FOR UPDATE;
  IF v_check.state='applied' THEN
    IF v_order.state='paid' AND v_attempt.state='succeeded'
       AND v_entitlement.id IS NOT NULL
       AND v_entitlement.source_attempt_id=v_attempt.id
       AND v_entitlement.paid_at=v_check.paid_at
       AND v_attempt.payment_intent_id=v_check.payment_intent_id THEN
      RETURN v_entitlement.id;
    END IF;
    RAISE EXCEPTION 'B-03D: applied verification conflicts with purchase';
  END IF;
  IF v_check.state <> 'ready' OR v_check.reason_code <> '' OR v_check.paid_at IS NULL
     OR v_check.success_event_id='' OR v_entitlement.id IS NOT NULL
     OR v_order.state <> 'awaiting_payment' OR v_attempt.state <> 'session_open'
     OR v_attempt.order_id <> v_order.id OR v_check.order_id <> v_order.id
     OR v_check.attempt_id <> v_attempt.id OR v_request.state <> 'bound'
     OR v_request.session_id <> v_check.session_id
     OR v_attempt.checkout_session_id <> v_check.session_id
     OR v_attempt.payment_intent_id <> ''
     OR v_order.file_key_snapshot='' OR v_order.file_revision_snapshot=''
     OR v_order.file_sha256_snapshot='' OR v_order.file_size_bytes_snapshot IS NULL
     OR NOT EXISTS (SELECT 1 FROM public.store_productfileversion p
          WHERE p.product_id=v_order.product_id
            AND p.object_identifier=v_order.file_key_snapshot
            AND p.version_id=v_order.file_revision_snapshot
            AND p.sha256=v_order.file_sha256_snapshot
            AND p.size_bytes=v_order.file_size_bytes_snapshot)
     OR EXISTS (SELECT 1 FROM public.store_paymentproviderevent e
          WHERE e.state='contradiction' AND e.provider_account_id=v_check.provider_account_id
            AND e.environment=v_check.environment
            AND (e.attempt_id=v_attempt.id OR e.external_object_id=v_check.session_id
                 OR e.claimed_operation_id=v_attempt.operation_id
                 OR e.claimed_order_public_id=v_order.public_id))
     OR (v_check.provider_event_id IS NOT NULL AND
         (v_event.state <> 'pending_reconciliation'
          OR v_event.external_object_id <> v_check.session_id)) THEN
    RAISE EXCEPTION 'B-03D: confirmation requires reconciliation';
  END IF;
  UPDATE public.store_paymentattempt SET state='succeeded',
     payment_intent_id=v_check.payment_intent_id, completed_at=v_check.paid_at,
     result_code='provider_paid', updated_at=now() WHERE id=v_attempt.id;
  UPDATE public.store_order SET state='paid', paid_at=v_check.paid_at,
     updated_at=now() WHERE id=v_order.id;
  INSERT INTO public.store_deliveryentitlement
    (order_id, source_attempt_id, grant_correlation_id, environment, status,
     paid_at, expires_at, file_object_identifier, file_version_id,
     file_sha256, file_size_bytes, download_limit, successful_downloads,
     suspended_at, revoked_at, status_reason_code, created_at, updated_at)
  VALUES (v_order.id, v_attempt.id, v_check.source_key, v_order.environment,
     'active', v_check.paid_at, v_check.paid_at + interval '336 hours',
     v_order.file_key_snapshot, v_order.file_revision_snapshot,
     v_order.file_sha256_snapshot, v_order.file_size_bytes_snapshot,
     3, 0, NULL, NULL, '', now(), now()) RETURNING * INTO v_entitlement;
  INSERT INTO public.store_orderauditevent
    (order_id, attempt_id, operation_id, subject, actor, actor_ref,
     action, from_state, to_state, reason, correlation_id, occurred_at)
  VALUES (v_order.id, v_attempt.id, gen_random_uuid(), 'order', 'system',
     'finance_test', 'entitlement_granted', '', 'active', '',
     v_check.source_key, now());
  IF v_check.provider_event_id IS NOT NULL THEN
    UPDATE public.store_paymentproviderevent SET state='applied',
       processed_at=now() WHERE id=v_check.provider_event_id;
  END IF;
  UPDATE public.store_financialverification SET state='applied',
     applied_at=now() WHERE id=v_check.id;
  RETURN v_entitlement.id;
END $$;
"""


def install(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        _install_roles(cursor)
        _extend_guards(cursor)
        cursor.execute(SQL)
        cursor.execute("""
          ALTER FUNCTION public.store_b03d_record(uuid,bigint,bigint,bigint,text,text,text,text,text,timestamptz,bigint,text,text,text,integer,text,text)
            OWNER TO mp_b03d_owner;
          ALTER FUNCTION public.store_b03d_confirm(bigint) OWNER TO mp_b03d_owner;
          REVOKE ALL ON FUNCTION public.store_b03d_record(uuid,bigint,bigint,bigint,text,text,text,text,text,timestamptz,bigint,text,text,text,integer,text,text) FROM PUBLIC;
          REVOKE ALL ON FUNCTION public.store_b03d_confirm(bigint) FROM PUBLIC;
          GRANT EXECUTE ON FUNCTION public.store_b03d_record(uuid,bigint,bigint,bigint,text,text,text,text,text,timestamptz,bigint,text,text,text,integer,text,text) TO mp_b03d_executor_test;
          GRANT EXECUTE ON FUNCTION public.store_b03d_confirm(bigint) TO mp_b03d_executor_test;
        """)


def reverse(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
          DROP TRIGGER store_b03d_verification_guard_trg ON public.store_financialverification;
          DROP FUNCTION public.store_b03d_verification_guard();
          DROP FUNCTION public.store_b03d_confirm(bigint);
          DROP FUNCTION public.store_b03d_record(uuid,bigint,bigint,bigint,text,text,text,text,text,timestamptz,bigint,text,text,text,integer,text,text);
        """)
        sources = [
            (importlib.import_module('store.migrations.0012_b03b_checkout_guards').FORWARD,
             ('store_r01_order_guard', 'store_r01_attempt_guard',
              'store_r01_order_audit', 'store_r01_attempt_audit')),
            (importlib.import_module('store.migrations.0006_b02b_entitlement_guards').SQL,
             ('store_b02b_entitlement_guard',)),
            (importlib.import_module('store.migrations.0014_b03c_evidence_guards').SQL,
             ('store_b03c_evidence_guard',)),
        ]
        for source, names in sources:
            for name in names:
                cursor.execute(_function(source, name))
        # Los roles globales se conservan; no contienen datos y su eliminación
        # podría afectar a otras bases del mismo clúster.


class Migration(migrations.Migration):
    dependencies = [('store', '0015_b03d_financialverification')]
    operations = [migrations.RunPython(install, reverse)]
