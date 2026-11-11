"""Extensión reversible de R01; los estados financieros siguen inaccesibles."""

import importlib
import re

from django.db import migrations


FORWARD = """
CREATE FUNCTION store_b03b_request_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent_state text; attempt_state text;
BEGIN
    SELECT o.state, a.state INTO parent_state, attempt_state
    FROM store_order o JOIN store_paymentattempt a ON a.order_id = o.id
    WHERE a.id = NEW.attempt_id FOR UPDATE OF o, a;
    IF parent_state IS NULL OR parent_state NOT IN ('created', 'awaiting_payment') THEN
        RAISE EXCEPTION 'B-03B: checkout requires an open order';
    END IF;
    IF TG_OP = 'INSERT' THEN
        IF attempt_state <> 'prepared' OR NEW.state <> 'calling'
           OR NEW.session_id <> '' OR NEW.session_expires_at IS NOT NULL THEN
            RAISE EXCEPTION 'B-03B: invalid initial checkout request';
        END IF;
    ELSIF NEW.attempt_id IS DISTINCT FROM OLD.attempt_id
       OR NEW.parameters_sha256 IS DISTINCT FROM OLD.parameters_sha256
       OR OLD.state = 'bound'
       OR (OLD.state = 'calling' AND NEW.state NOT IN ('uncertain','bound'))
       OR (OLD.state = 'uncertain' AND NEW.state <> 'bound')
       OR (NEW.state = 'bound' AND (NEW.session_id = '' OR NEW.session_expires_at IS NULL))
       OR (NEW.state <> 'bound' AND (NEW.session_id <> '' OR NEW.session_expires_at IS NOT NULL)) THEN
        RAISE EXCEPTION 'B-03B: invalid checkout request transition';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER store_b03b_request_guard_trg BEFORE INSERT OR UPDATE OR DELETE
ON store_checkoutrequest FOR EACH ROW EXECUTE FUNCTION store_b03b_request_guard();

CREATE OR REPLACE FUNCTION store_r01_order_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.state <> 'created' OR NEW.paid_at IS NOT NULL
           OR NEW.closed_at IS NOT NULL OR NEW.closed_reason <> '' THEN
            RAISE EXCEPTION 'B-02A: invalid initial order state';
        END IF;
        RETURN NEW;
    END IF;
    IF ROW(NEW.public_id, NEW.creation_key, NEW.product_id, NEW.environment,
           NEW.product_name_snapshot, NEW.product_version_snapshot,
           NEW.amount_minor, NEW.currency, NEW.delivery_terms_snapshot,
           NEW.stripe_product_id_snapshot, NEW.stripe_price_id_snapshot,
           NEW.file_key_snapshot, NEW.file_revision_snapshot, NEW.file_sha256_snapshot)
       IS DISTINCT FROM
       ROW(OLD.public_id, OLD.creation_key, OLD.product_id, OLD.environment,
           OLD.product_name_snapshot, OLD.product_version_snapshot,
           OLD.amount_minor, OLD.currency, OLD.delivery_terms_snapshot,
           OLD.stripe_product_id_snapshot, OLD.stripe_price_id_snapshot,
           OLD.file_key_snapshot, OLD.file_revision_snapshot, OLD.file_sha256_snapshot) THEN
        RAISE EXCEPTION 'B-02A: order snapshot is immutable';
    END IF;
    IF NEW.paid_at IS DISTINCT FROM OLD.paid_at THEN
        RAISE EXCEPTION 'B-02A: payment confirmation is unavailable';
    END IF;
    IF NEW.state IS DISTINCT FROM OLD.state THEN
        IF OLD.state = 'created' AND NEW.state = 'awaiting_payment' THEN
            IF NOT EXISTS (SELECT 1 FROM store_paymentattempt a WHERE a.order_id = OLD.id
                AND a.state = 'session_open' AND a.checkout_session_id <> '') THEN
                RAISE EXCEPTION 'B-03B: awaiting payment requires a bound session';
            END IF;
        ELSIF OLD.state = 'created' AND NEW.state = 'closed_unpaid' THEN
            IF NEW.closed_at IS NULL OR EXISTS (
                SELECT 1 FROM store_paymentattempt a WHERE a.order_id = OLD.id
                AND (a.state IN ('prepared','session_open','processing','review','succeeded')
                     OR a.checkout_session_id <> '' OR a.payment_intent_id <> '')
            ) THEN RAISE EXCEPTION 'B-02A: order transition is not authorized'; END IF;
        ELSE RAISE EXCEPTION 'B-02A: order transition is not authorized';
        END IF;
    ELSIF NEW.closed_at IS DISTINCT FROM OLD.closed_at
       OR NEW.closed_reason IS DISTINCT FROM OLD.closed_reason THEN
        RAISE EXCEPTION 'B-02A: closure fields require a transition';
    END IF;
    RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION store_r01_attempt_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent store_order%%ROWTYPE;
BEGIN
    IF TG_OP = 'INSERT' THEN
        SELECT * INTO parent FROM store_order WHERE id = NEW.order_id FOR UPDATE;
        IF parent.id IS NULL OR parent.state NOT IN ('created','awaiting_payment')
           OR NEW.environment <> parent.environment
           OR NEW.amount_minor <> parent.amount_minor OR NEW.currency <> parent.currency
           OR NEW.state <> 'prepared' OR NEW.completed_at IS NOT NULL
           OR NEW.result_code <> '' OR NEW.checkout_session_id <> ''
           OR NEW.payment_intent_id <> '' OR NEW.bound_at IS NOT NULL THEN
            RAISE EXCEPTION 'B-02A: invalid initial payment attempt';
        END IF;
        RETURN NEW;
    END IF;
    IF ROW(NEW.order_id, NEW.operation_id, NEW.request_idempotency_key,
           NEW.attempt_number, NEW.provider, NEW.provider_account_id,
           NEW.environment, NEW.amount_minor, NEW.currency)
       IS DISTINCT FROM
       ROW(OLD.order_id, OLD.operation_id, OLD.request_idempotency_key,
           OLD.attempt_number, OLD.provider, OLD.provider_account_id,
           OLD.environment, OLD.amount_minor, OLD.currency) THEN
        RAISE EXCEPTION 'B-02A: payment attempt identity is immutable';
    END IF;
    IF NEW.state IS DISTINCT FROM OLD.state THEN
        IF OLD.state = 'prepared' AND NEW.state = 'session_open' THEN
            IF NEW.checkout_session_id = '' OR NEW.bound_at IS NULL
               OR NEW.payment_intent_id <> '' OR NEW.completed_at IS NOT NULL
               OR NEW.result_code <> '' OR NOT EXISTS (
                   SELECT 1 FROM store_checkoutrequest r WHERE r.attempt_id = OLD.id
                   AND r.state = 'bound' AND r.session_id = NEW.checkout_session_id
               ) THEN RAISE EXCEPTION 'B-03B: session transition lacks bound request'; END IF;
        ELSIF OLD.state = 'prepared' AND NEW.state = 'expired' THEN
            IF OLD.checkout_session_id <> '' OR OLD.payment_intent_id <> ''
               OR NEW.completed_at IS NULL OR NEW.result_code = '' THEN
                RAISE EXCEPTION 'B-02A: attempt transition is not authorized';
            END IF;
        ELSE RAISE EXCEPTION 'B-02A: attempt transition is not authorized';
        END IF;
    ELSIF NEW.completed_at IS DISTINCT FROM OLD.completed_at
       OR NEW.result_code IS DISTINCT FROM OLD.result_code
       OR NEW.checkout_session_id IS DISTINCT FROM OLD.checkout_session_id
       OR NEW.bound_at IS DISTINCT FROM OLD.bound_at THEN
        RAISE EXCEPTION 'B-03B: session fields require a transition';
    END IF;
    RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION store_r01_order_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO store_orderauditevent (order_id, operation_id, subject, actor, actor_ref,
            action, from_state, to_state, reason, correlation_id, occurred_at)
        VALUES (NEW.id, gen_random_uuid(), 'order', 'system', '', 'created', '', NEW.state,
            '', NEW.creation_key, now());
    ELSIF NEW.state IS DISTINCT FROM OLD.state THEN
        INSERT INTO store_orderauditevent (order_id, operation_id, subject, actor, actor_ref,
            action, from_state, to_state, reason, correlation_id, occurred_at)
        VALUES (NEW.id, gen_random_uuid(), 'order', 'system', '',
            CASE WHEN NEW.state = 'awaiting_payment' THEN 'awaiting_payment' ELSE 'closed_unpaid' END,
            OLD.state, NEW.state, NEW.closed_reason, NULL, now());
    END IF;
    RETURN NULL;
END $$;

CREATE OR REPLACE FUNCTION store_r01_attempt_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO store_orderauditevent (order_id, attempt_id, operation_id, subject, actor,
            actor_ref, action, from_state, to_state, reason, correlation_id, occurred_at)
        VALUES (NEW.order_id, NEW.id, gen_random_uuid(), 'attempt', 'system', '',
            'prepared', '', NEW.state, '', NEW.operation_id, now());
    ELSIF NEW.state IS DISTINCT FROM OLD.state THEN
        INSERT INTO store_orderauditevent (order_id, attempt_id, operation_id, subject, actor,
            actor_ref, action, from_state, to_state, reason, correlation_id, occurred_at)
        VALUES (NEW.order_id, NEW.id, gen_random_uuid(), 'attempt', 'system', '',
            CASE WHEN NEW.state = 'session_open' THEN 'session_open' ELSE 'expired' END,
            OLD.state, NEW.state, NEW.result_code, NEW.operation_id, now());
    END IF;
    RETURN NULL;
END $$;
"""


def install(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(FORWARD)


def reverse(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute('DROP TRIGGER store_b03b_request_guard_trg ON store_checkoutrequest;')
    schema_editor.execute('DROP FUNCTION store_b03b_request_guard();')
    original = importlib.import_module('store.migrations.0004_b02a_r01_integrity_guards').SQL
    for name in ('store_r01_order_guard', 'store_r01_attempt_guard',
                 'store_r01_order_audit', 'store_r01_attempt_audit'):
        match = re.search(r'CREATE FUNCTION ' + name + r'\(\).*?END \$\$;', original, re.S)
        if match is None:
            raise RuntimeError('No se encontró la función R01 para reversión.')
        schema_editor.execute(match.group().replace('CREATE FUNCTION', 'CREATE OR REPLACE FUNCTION', 1))


class Migration(migrations.Migration):
    dependencies = [('store', '0011_checkoutrequest')]
    operations = [migrations.RunPython(install, reverse)]
