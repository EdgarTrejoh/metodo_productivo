import hashlib
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings

from store.file_versions import (FileVersionMismatch, FileVersionTransientError,
    FileVersionUnavailable, LocalVersionStorage, assert_order_checkout_ready, select_sellable_file_version)
from store.models import Order, ProductFileVersion, ProductFileSelectionEvent
from store.order_services import create_order
from store import file_versions
from store.test_orders import published_product


class FileVersionTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings_override = override_settings(PRIVATE_PRODUCT_ROOT=Path(self.temp.name))
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.product = published_product(slug=f'file-{uuid.uuid4().hex}')
        self.data = b'contenido sintetico para B03A'
        self.object_id = 'synthetic-object'
        self.revision = uuid.uuid4().hex
        self.path = Path(self.temp.name) / self.object_id / self.revision
        self.path.parent.mkdir()
        self.path.write_bytes(self.data)
        self.version = ProductFileVersion.objects.create(
            product=self.product, backend='local', object_identifier=self.object_id,
            version_id=self.revision, sha256=hashlib.sha256(self.data).hexdigest(),
            size_bytes=len(self.data),
        )

    def order(self):
        return create_order(product_id=self.product.pk, creation_key=uuid.uuid4(), environment='test')

    def test_verified_snapshot_and_old_order_gate(self):
        old = self.order()
        with self.assertRaises(FileVersionMismatch):
            assert_order_checkout_ready(old.pk)
        select_sellable_file_version(product_id=self.product.pk, version_id=self.version.pk)
        self.assertEqual(ProductFileSelectionEvent.objects.filter(product=self.product, selected_version=self.version).count(), 1)
        order = self.order()
        self.assertEqual((order.file_key_snapshot, order.file_revision_snapshot,
            order.file_sha256_snapshot, order.file_size_bytes_snapshot),
            (self.object_id, self.revision, self.version.sha256, len(self.data)))
        self.assertEqual(assert_order_checkout_ready(order.pk).pk, order.pk)
        self.product.price = '599.00'
        self.product.save()
        self.assertEqual(assert_order_checkout_ready(order.pk).amount_minor, 49900)
        order.file_sha256_snapshot = '0' * 64
        with self.assertRaises(ValidationError):
            order.save()

    def test_missing_mismatch_and_transient(self):
        self.path.unlink()
        with self.assertRaises(FileVersionUnavailable):
            select_sellable_file_version(product_id=self.product.pk, version_id=self.version.pk)
        self.path.write_bytes(self.data)
        select_sellable_file_version(product_id=self.product.pk, version_id=self.version.pk)
        order = self.order()
        self.path.write_bytes(b'changed')
        with self.assertRaises(FileVersionMismatch):
            assert_order_checkout_ready(order.pk)
        self.path.unlink()
        with self.assertRaises(FileVersionUnavailable):
            assert_order_checkout_ready(order.pk)
        with patch('store.file_versions.LocalVersionStorage.open_version', side_effect=OSError):
            with self.assertRaises(FileVersionTransientError):
                assert_order_checkout_ready(order.pk)

    def test_identity_immutable_and_wrong_product(self):
        self.version.size_bytes += 1
        with self.assertRaises(ValidationError):
            self.version.save()
        other = published_product(slug='other-file-product')
        other.sellable_file_version = self.version
        with self.assertRaises(ValidationError):
            other.save()

    def test_wrong_digest_size_and_incomplete_version(self):
        self.path.write_bytes(b'x' * len(self.data))
        with self.assertRaises(FileVersionMismatch):
            select_sellable_file_version(product_id=self.product.pk, version_id=self.version.pk)
        self.path.write_bytes(self.data + b'x')
        with self.assertRaises(FileVersionMismatch):
            select_sellable_file_version(product_id=self.product.pk, version_id=self.version.pk)
        self.path.write_bytes(self.data)
        self.version.version_id = ''
        with self.assertRaises(ValidationError):
            self.version.save()

    def test_local_identifier_and_symlink_cannot_escape_root(self):
        storage = LocalVersionStorage()
        for identifier in ('../private', '/absolute', 'C:\\private', 'nested/path', ''):
            with self.assertRaises(FileVersionMismatch):
                storage.open_version(identifier, self.revision)
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / 'private.bin'
            target.write_bytes(self.data)
            self.path.unlink()
            try:
                self.path.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest('El entorno no permite crear enlaces simbólicos de prueba.')
            with self.assertRaises(FileVersionMismatch):
                storage.open_version(self.object_id, self.revision)

    def test_postgresql_direct_update_guard(self):
        if connection.vendor != 'postgresql':
            self.skipTest('Los triggers de identidad requieren PostgreSQL.')
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('UPDATE store_productfileversion SET size_bytes = size_bytes + 1 WHERE id = %s', [self.version.pk])


class FileVersionConcurrencyTests(TransactionTestCase):
    def test_selection_and_order_share_product_lock(self):
        if connection.vendor != 'postgresql':
            self.skipTest('Requiere bloqueos de fila y dos conexiones PostgreSQL.')
        with tempfile.TemporaryDirectory() as root:
            with override_settings(PRIVATE_PRODUCT_ROOT=Path(root)):
                product = published_product(slug='concurrent-file-product')
                versions = []
                for number in (1, 2):
                    content = f'version-{number}'.encode()
                    object_id = f'object-{number}'
                    revision = uuid.uuid4().hex
                    path = Path(root) / object_id / revision
                    path.parent.mkdir()
                    path.write_bytes(content)
                    versions.append(ProductFileVersion.objects.create(
                        product=product, backend='local', object_identifier=object_id,
                        version_id=revision, sha256=hashlib.sha256(content).hexdigest(),
                        size_bytes=len(content),
                    ))
                select_sellable_file_version(product_id=product.pk, version_id=versions[0].pk)
                locked = threading.Event()
                release = threading.Event()
                original_verify = file_versions.verify_file_version

                def pause_selection(version):
                    if threading.current_thread().name == 'selector' and version.pk == versions[1].pk:
                        locked.set()
                        if not release.wait(10):
                            raise AssertionError('La prueba agotó el tiempo de espera.')
                    return original_verify(version)

                def select_new():
                    threading.current_thread().name = 'selector'
                    try:
                        return select_sellable_file_version(product_id=product.pk, version_id=versions[1].pk)
                    finally:
                        connections.close_all()

                def make_order():
                    try:
                        return create_order(product_id=product.pk, creation_key=uuid.uuid4(), environment='test')
                    finally:
                        connections.close_all()

                with patch('store.file_versions.verify_file_version', side_effect=pause_selection):
                    with ThreadPoolExecutor(max_workers=2) as pool:
                        selecting = pool.submit(select_new)
                        self.assertTrue(locked.wait(5))
                        ordering = pool.submit(make_order)
                        try:
                            self.assertFalse(ordering.done(), 'La compra debe esperar el bloqueo del producto.')
                        finally:
                            release.set()
                        selecting.result(timeout=10)
                        order = ordering.result(timeout=10)
                self.assertEqual((order.file_key_snapshot, order.file_revision_snapshot,
                                  order.file_sha256_snapshot, order.file_size_bytes_snapshot),
                                 (versions[1].object_identifier, versions[1].version_id,
                                  versions[1].sha256, versions[1].size_bytes))
                self.assertEqual(assert_order_checkout_ready(order.pk).pk, order.pk)
                select_sellable_file_version(product_id=product.pk, version_id=versions[0].pk)
                order.refresh_from_db()
                self.assertEqual(order.file_revision_snapshot, versions[1].version_id)
