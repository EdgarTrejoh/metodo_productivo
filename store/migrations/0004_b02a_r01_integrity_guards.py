from django.db import migrations


SQL = """
CREATE FUNCTION store_r01_order_guard() RETURNS trigger LANGUAGE plpgsql AS $$
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
        IF OLD.state <> 'created' OR NEW.state <> 'closed_unpaid'
           OR NEW.closed_at IS NULL
           OR EXISTS (
               SELECT 1 FROM store_paymentattempt a WHERE a.order_id = OLD.id
               AND (a.state IN ('prepared', 'session_open', 'processing', 'review', 'succeeded')
                    OR a.checkout_session_id <> '' OR a.payment_intent_id <> '')
           ) THEN
            RAISE EXCEPTION 'B-02A: order transition is not authorized';
        END IF;
    ELSIF NEW.closed_at IS DISTINCT FROM OLD.closed_at
          OR NEW.closed_reason IS DISTINCT FROM OLD.closed_reason THEN
        RAISE EXCEPTION 'B-02A: closure fields require a transition';
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER store_r01_order_guard_trg
BEFORE INSERT OR UPDATE ON store_order
FOR EACH ROW EXECUTE FUNCTION store_r01_order_guard();

CREATE FUNCTION store_r01_attempt_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    parent store_order%%ROWTYPE;
BEGIN
    IF TG_OP = 'INSERT' THEN
        SELECT * INTO parent FROM store_order WHERE id = NEW.order_id FOR UPDATE;
        IF parent.id IS NULL OR parent.state NOT IN ('created', 'awaiting_payment')
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
        IF OLD.state <> 'prepared' OR NEW.state <> 'expired'
           OR OLD.checkout_session_id <> '' OR OLD.payment_intent_id <> ''
           OR NEW.completed_at IS NULL OR NEW.result_code = '' THEN
            RAISE EXCEPTION 'B-02A: attempt transition is not authorized';
        END IF;
    ELSIF NEW.completed_at IS DISTINCT FROM OLD.completed_at
          OR NEW.result_code IS DISTINCT FROM OLD.result_code THEN
        RAISE EXCEPTION 'B-02A: result fields require a transition';
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER store_r01_attempt_guard_trg
BEFORE INSERT OR UPDATE ON store_paymentattempt
FOR EACH ROW EXECUTE FUNCTION store_r01_attempt_guard();

CREATE FUNCTION store_r01_order_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO store_orderauditevent
            (order_id, operation_id, subject, actor, actor_ref, action,
             from_state, to_state, reason, correlation_id, occurred_at)
        VALUES
            (NEW.id, gen_random_uuid(), 'order', 'system', '', 'created',
             '', NEW.state, '', NEW.creation_key, now());
    ELSIF NEW.state IS DISTINCT FROM OLD.state THEN
        INSERT INTO store_orderauditevent
            (order_id, operation_id, subject, actor, actor_ref, action,
             from_state, to_state, reason, correlation_id, occurred_at)
        VALUES
            (NEW.id, gen_random_uuid(), 'order', 'system', '', 'closed_unpaid',
             OLD.state, NEW.state, NEW.closed_reason, NULL, now());
    END IF;
    RETURN NULL;
END $$;

CREATE TRIGGER store_r01_order_audit_trg
AFTER INSERT OR UPDATE ON store_order
FOR EACH ROW EXECUTE FUNCTION store_r01_order_audit();

CREATE FUNCTION store_r01_attempt_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO store_orderauditevent
            (order_id, attempt_id, operation_id, subject, actor, actor_ref, action,
             from_state, to_state, reason, correlation_id, occurred_at)
        VALUES
            (NEW.order_id, NEW.id, gen_random_uuid(), 'attempt', 'system', '', 'prepared',
             '', NEW.state, '', NEW.operation_id, now());
    ELSIF NEW.state IS DISTINCT FROM OLD.state THEN
        INSERT INTO store_orderauditevent
            (order_id, attempt_id, operation_id, subject, actor, actor_ref, action,
             from_state, to_state, reason, correlation_id, occurred_at)
        VALUES
            (NEW.order_id, NEW.id, gen_random_uuid(), 'attempt', 'system', '', 'expired',
             OLD.state, NEW.state, NEW.result_code, NEW.operation_id, now());
    END IF;
    RETURN NULL;
END $$;

CREATE TRIGGER store_r01_attempt_audit_trg
AFTER INSERT OR UPDATE ON store_paymentattempt
FOR EACH ROW EXECUTE FUNCTION store_r01_attempt_audit();

CREATE FUNCTION store_r01_audit_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'B-02A: audit events are append-only';
END $$;

CREATE TRIGGER store_r01_audit_guard_trg
BEFORE UPDATE OR DELETE ON store_orderauditevent
FOR EACH ROW EXECUTE FUNCTION store_r01_audit_guard();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS store_r01_audit_guard_trg ON store_orderauditevent;
DROP TRIGGER IF EXISTS store_r01_attempt_audit_trg ON store_paymentattempt;
DROP TRIGGER IF EXISTS store_r01_order_audit_trg ON store_order;
DROP TRIGGER IF EXISTS store_r01_attempt_guard_trg ON store_paymentattempt;
DROP TRIGGER IF EXISTS store_r01_order_guard_trg ON store_order;
DROP FUNCTION IF EXISTS store_r01_audit_guard();
DROP FUNCTION IF EXISTS store_r01_attempt_audit();
DROP FUNCTION IF EXISTS store_r01_order_audit();
DROP FUNCTION IF EXISTS store_r01_attempt_guard();
DROP FUNCTION IF EXISTS store_r01_order_guard();
"""


def install_guards(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(SQL)


def remove_guards(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(REVERSE_SQL)


class Migration(migrations.Migration):
    dependencies = [('store', '0003_order_paymentattempt_orderauditevent_and_more')]
    operations = [migrations.RunPython(install_guards, remove_guards)]
