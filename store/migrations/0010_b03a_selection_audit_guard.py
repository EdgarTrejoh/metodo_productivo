from django.db import migrations


SQL = """
CREATE FUNCTION store_b03a_selection_audit_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'B-03A: file selection audit is append-only';
END $$;
CREATE TRIGGER store_b03a_selection_audit_guard_trg
BEFORE UPDATE OR DELETE ON store_productfileselectionevent
FOR EACH ROW EXECUTE FUNCTION store_b03a_selection_audit_guard();
CREATE FUNCTION store_b03a_product_selection_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.sellable_file_version_id IS DISTINCT FROM OLD.sellable_file_version_id
       AND NEW.sellable_file_version_id IS NOT NULL THEN
        INSERT INTO store_productfileselectionevent
            (product_id, previous_version_id, selected_version_id, actor_ref, occurred_at)
        VALUES (NEW.id, OLD.sellable_file_version_id, NEW.sellable_file_version_id, 'system', now());
    END IF;
    RETURN NULL;
END $$;
CREATE TRIGGER store_b03a_product_selection_audit_trg
AFTER UPDATE ON store_digitalproduct
FOR EACH ROW EXECUTE FUNCTION store_b03a_product_selection_audit();
"""
REVERSE_SQL = """
DROP TRIGGER IF EXISTS store_b03a_product_selection_audit_trg ON store_digitalproduct;
DROP TRIGGER IF EXISTS store_b03a_selection_audit_guard_trg ON store_productfileselectionevent;
DROP FUNCTION IF EXISTS store_b03a_product_selection_audit();
DROP FUNCTION IF EXISTS store_b03a_selection_audit_guard();
"""


def install(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(SQL)


def remove(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(REVERSE_SQL)


class Migration(migrations.Migration):
    dependencies = [('store', '0009_productfileselectionevent')]
    operations = [migrations.RunPython(install, remove)]
