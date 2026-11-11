from django.db import migrations


SQL = """
CREATE FUNCTION store_b03a_file_version_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'B-03A: file version deletion is unavailable';
    END IF;
    IF TG_OP = 'UPDATE' AND ROW(NEW.product_id, NEW.backend, NEW.object_identifier,
        NEW.version_id, NEW.sha256, NEW.size_bytes) IS DISTINCT FROM
        ROW(OLD.product_id, OLD.backend, OLD.object_identifier,
        OLD.version_id, OLD.sha256, OLD.size_bytes) THEN
        RAISE EXCEPTION 'B-03A: file version identity is immutable';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER store_b03a_file_version_guard_trg
BEFORE UPDATE OR DELETE ON store_productfileversion
FOR EACH ROW EXECUTE FUNCTION store_b03a_file_version_guard();

CREATE FUNCTION store_b03a_product_version_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.sellable_file_version_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM store_productfileversion v
        WHERE v.id = NEW.sellable_file_version_id AND v.product_id = NEW.id
    ) THEN
        RAISE EXCEPTION 'B-03A: file version belongs to another product';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER store_b03a_product_version_guard_trg
BEFORE INSERT OR UPDATE ON store_digitalproduct
FOR EACH ROW EXECUTE FUNCTION store_b03a_product_version_guard();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS store_b03a_product_version_guard_trg ON store_digitalproduct;
DROP TRIGGER IF EXISTS store_b03a_file_version_guard_trg ON store_productfileversion;
DROP FUNCTION IF EXISTS store_b03a_product_version_guard();
DROP FUNCTION IF EXISTS store_b03a_file_version_guard();
"""


def install(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(SQL)


def remove(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(REVERSE_SQL)


class Migration(migrations.Migration):
    dependencies = [('store', '0007_productfileversion_and_more')]
    operations = [migrations.RunPython(install, remove)]
