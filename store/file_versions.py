"""Verificación de versiones privadas antes de preparar una compra."""

import hashlib
from pathlib import Path

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from store.models import Order, ProductFileVersion


class FileVersionError(ValueError):
    pass


class FileVersionUnavailable(FileVersionError):
    pass


class FileVersionTransientError(FileVersionError):
    pass


class FileVersionMismatch(FileVersionError):
    pass


class LocalVersionStorage:
    """Cada versión ocupa una ruta distinta; no se aceptan rutas suministradas por el visitante."""

    def open_version(self, object_identifier, version_id):
        root = Path(settings.PRIVATE_PRODUCT_ROOT).resolve()
        if not object_identifier.isascii() or not version_id.isascii():
            raise FileVersionMismatch('Identificador de archivo inválido.')
        for part in (object_identifier, version_id):
            if not part or not all(c.isalnum() or c in '-_' for c in part):
                raise FileVersionMismatch('Identificador de archivo inválido.')
        path = root / object_identifier / version_id
        try:
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(root) or not resolved.is_file():
                raise FileVersionMismatch('Ruta privada inválida.')
            return resolved.open('rb')
        except FileNotFoundError as exc:
            raise FileVersionUnavailable('La versión privada no existe.') from exc
        except OSError as exc:
            raise FileVersionTransientError('No pudo consultarse el almacenamiento privado.') from exc


def verify_file_version(version):
    if version.backend != ProductFileVersion.Backend.LOCAL:
        raise FileVersionTransientError('El adaptador de almacenamiento aún no está configurado.')
    digest = hashlib.sha256()
    size = 0
    try:
        with LocalVersionStorage().open_version(version.object_identifier, version.version_id) as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
                size += len(chunk)
    except OSError as exc:
        raise FileVersionTransientError('Falló la lectura del archivo privado.') from exc
    if size != version.size_bytes or digest.hexdigest() != version.sha256:
        raise FileVersionMismatch('El contenido no coincide con la versión registrada.')
    return size, digest.hexdigest()


def assert_order_checkout_ready(order_id):
    """Solo valida; no contacta Stripe ni concede derechos."""
    order = Order.objects.select_related('product').get(pk=order_id)
    version = ProductFileVersion.objects.filter(product_id=order.product_id,
        object_identifier=order.file_key_snapshot,
        version_id=order.file_revision_snapshot,
        sha256=order.file_sha256_snapshot,
        size_bytes=order.file_size_bytes_snapshot).first()
    if (not version or not version.available_for_sale
            or version.object_identifier != order.file_key_snapshot
            or version.version_id != order.file_revision_snapshot
            or version.sha256 != order.file_sha256_snapshot
            or version.size_bytes != order.file_size_bytes_snapshot):
        raise FileVersionMismatch('La orden no conserva una versión comercial verificable.')
    verify_file_version(version)
    return order


def select_sellable_file_version(*, product_id, version_id):
    """Cambio administrativo explícito; la identidad de órdenes anteriores permanece fija."""
    from store.models import DigitalProduct, ProductFileSelectionEvent

    with transaction.atomic():
        product = DigitalProduct.objects.select_for_update().get(pk=product_id)
        version = ProductFileVersion.objects.select_for_update().get(pk=version_id, product=product)
        verify_file_version(version)
        version.last_verified_at = timezone.now()
        version.last_verification_result = 'verified'
        version.available_for_sale = True
        version.save(update_fields=['last_verified_at', 'last_verification_result', 'available_for_sale'])
        previous_id = product.sellable_file_version_id
        product.sellable_file_version = version
        product.save(update_fields=['sellable_file_version', 'updated_at'])
        if previous_id != version.pk and connection.vendor != 'postgresql':
            ProductFileSelectionEvent.objects.create(
                product=product, previous_version_id=previous_id, selected_version=version,
            )
        return version
