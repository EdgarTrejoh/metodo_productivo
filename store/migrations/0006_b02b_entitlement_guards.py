from django.db import migrations


SQL = """
CREATE FUNCTION store_b02b_order_file_size_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.file_size_bytes_snapshot IS DISTINCT FROM OLD.file_size_bytes_snapshot THEN
        RAISE EXCEPTION 'B-02B: order file size snapshot is immutable';
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER store_b02b_order_file_size_guard_trg
BEFORE UPDATE ON store_order
FOR EACH ROW EXECUTE FUNCTION store_b02b_order_file_size_guard();

CREATE FUNCTION store_b02b_entitlement_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    parent store_order%%ROWTYPE;
    payment store_paymentattempt%%ROWTYPE;
BEGIN
    IF TG_OP <> 'INSERT' THEN
        RAISE EXCEPTION 'B-02B: entitlement changes are unavailable';
    END IF;

    -- El orden de bloqueo coincide con B-02A: orden antes que intento.
    SELECT * INTO parent FROM store_order WHERE id = NEW.order_id FOR UPDATE;
    SELECT * INTO payment FROM store_paymentattempt WHERE id = NEW.source_attempt_id FOR UPDATE;
    IF parent.id IS NULL OR payment.id IS NULL
       OR parent.state <> 'paid' OR parent.paid_at IS NULL
       OR payment.state <> 'succeeded' OR payment.order_id <> parent.id
       OR NEW.environment <> parent.environment OR NEW.environment <> payment.environment
       OR NEW.paid_at IS DISTINCT FROM parent.paid_at
       OR NEW.expires_at IS DISTINCT FROM (NEW.paid_at + INTERVAL '336 hours')
       OR parent.file_key_snapshot = '' OR parent.file_revision_snapshot = ''
       OR parent.file_sha256_snapshot = '' OR parent.file_size_bytes_snapshot IS NULL
       OR NEW.file_object_identifier IS DISTINCT FROM parent.file_key_snapshot
       OR NEW.file_version_id IS DISTINCT FROM parent.file_revision_snapshot
       OR NEW.file_sha256 IS DISTINCT FROM parent.file_sha256_snapshot
       OR NEW.file_size_bytes IS DISTINCT FROM parent.file_size_bytes_snapshot
       OR NEW.status <> 'active' OR NEW.download_limit <> 3
       OR NEW.successful_downloads <> 0 OR NEW.suspended_at IS NOT NULL
       OR NEW.revoked_at IS NOT NULL OR NEW.status_reason_code <> '' THEN
        RAISE EXCEPTION 'B-02B: entitlement requires a verified paid order and matching file version';
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER store_b02b_entitlement_guard_trg
BEFORE INSERT OR UPDATE OR DELETE ON store_deliveryentitlement
FOR EACH ROW EXECUTE FUNCTION store_b02b_entitlement_guard();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS store_b02b_entitlement_guard_trg ON store_deliveryentitlement;
DROP TRIGGER IF EXISTS store_b02b_order_file_size_guard_trg ON store_order;
DROP FUNCTION IF EXISTS store_b02b_entitlement_guard();
DROP FUNCTION IF EXISTS store_b02b_order_file_size_guard();
"""


def install_guards(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(SQL)


def remove_guards(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(REVERSE_SQL)


class Migration(migrations.Migration):
    dependencies = [('store', '0005_deliveryentitlement_order_file_size_bytes_snapshot_and_more')]
    operations = [migrations.RunPython(install_guards, remove_guards)]
