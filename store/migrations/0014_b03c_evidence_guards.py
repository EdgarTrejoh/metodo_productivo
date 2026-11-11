from django.db import migrations


SQL = """
CREATE FUNCTION store_b03c_evidence_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'B-03C: authenticated evidence cannot be deleted';
    END IF;
    IF TG_OP = 'INSERT' THEN
        IF NEW.state <> 'verified' OR NEW.order_id IS NOT NULL
           OR NEW.attempt_id IS NOT NULL OR NEW.processed_at IS NOT NULL
           OR NEW.conflict_count <> 0 OR NEW.retry_count <> 0 THEN
            RAISE EXCEPTION 'B-03C: invalid initial evidence';
        END IF;
        RETURN NEW;
    END IF;
    IF ROW(NEW.provider, NEW.provider_account_id, NEW.environment, NEW.external_event_id,
           NEW.event_type, NEW.external_object_id, NEW.raw_sha256,
           NEW.provider_created_at, NEW.verified_at, NEW.claimed_operation_id,
           NEW.claimed_order_public_id, NEW.claimed_payment_intent_id,
           NEW.claimed_amount_minor, NEW.claimed_currency, NEW.claimed_payment_status)
       IS DISTINCT FROM
       ROW(OLD.provider, OLD.provider_account_id, OLD.environment, OLD.external_event_id,
           OLD.event_type, OLD.external_object_id, OLD.raw_sha256,
           OLD.provider_created_at, OLD.verified_at, OLD.claimed_operation_id,
           OLD.claimed_order_public_id, OLD.claimed_payment_intent_id,
           OLD.claimed_amount_minor, OLD.claimed_currency, OLD.claimed_payment_status) THEN
        RAISE EXCEPTION 'B-03C: event identity is immutable';
    END IF;
    IF NEW.processed_at IS NOT NULL OR NEW.state = 'applied'
       OR (OLD.state = 'contradiction' AND NEW.state <> 'contradiction')
       OR (OLD.state = 'pending_reconciliation' AND NEW.state = 'verified') THEN
        RAISE EXCEPTION 'B-03C: financial application is unavailable';
    END IF;
    IF NEW.attempt_id IS NOT NULL AND (NEW.order_id IS NULL OR NOT EXISTS (
        SELECT 1 FROM store_paymentattempt a WHERE a.id = NEW.attempt_id
        AND a.order_id = NEW.order_id)) THEN
        RAISE EXCEPTION 'B-03C: attempt must belong to order';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER store_b03c_evidence_guard_trg
BEFORE INSERT OR UPDATE OR DELETE ON store_paymentproviderevent
FOR EACH ROW EXECUTE FUNCTION store_b03c_evidence_guard();
"""
REVERSE_SQL = """
DROP TRIGGER IF EXISTS store_b03c_evidence_guard_trg ON store_paymentproviderevent;
DROP FUNCTION IF EXISTS store_b03c_evidence_guard();
"""


def install(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(SQL)


def remove(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(REVERSE_SQL)


class Migration(migrations.Migration):
    dependencies = [('store', '0013_paymentproviderevent')]
    operations = [migrations.RunPython(install, remove)]
