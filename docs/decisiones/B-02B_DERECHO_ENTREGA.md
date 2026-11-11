# B-02B — estructura del derecho de entrega digital

**Estado:** aceptada técnicamente en alcance local por el promotor el 10 de noviembre de 2026, con las salvedades siguientes; sin despliegue, publicación en producción ni concesión efectiva.

## Decisiones aprobadas

| ID | Decisión |
| --- | --- |
| B-02B-D01 | Un `DeliveryEntitlement` independiente por orden y por intento confirmado; no se crean todavía reservas, operaciones de descarga ni enlaces de acceso. |
| B-02B-D02 | El derecho conserva identificador del objeto privado, versión inmutable, SHA-256 y tamaño, concordantes con el snapshot de la orden. Antes de B-03 se necesita un mecanismo real que verifique y preserve esa versión. |
| B-02B-D03 | Estados administrativos `ACTIVE`, `SUSPENDED` y `REVOKED`; los dos últimos carecen aún de servicios de transición. |

## Frontera implementada

La relación uno a uno con orden e intento impone unicidad. Hay restricciones para entorno, estado, archivo no vacío, digest hexadecimal, tamaño positivo, límite fijo de tres y contador entre cero y tres. La aplicación exige pago confirmado, mismo intento/orden/entorno, identidad del archivo y vencimiento exacto 336 horas después del pago efectivo. Las condiciones de vencimiento y agotamiento se derivan al consultar; no son estados persistidos.

Se añade `Order.file_size_bytes_snapshot` como dato histórico nullable. Las órdenes previas, y las creadas por B-02A, carecen de versión, digest y tamaño verificables. No pueden originar un derecho. El valor queda protegido frente a `save()`, `QuerySet.update()`, `bulk_update()` y SQL ordinario en PostgreSQL. El resto de la fotografía comercial conserva las protecciones R01.

La migración `0006` añade guardas PostgreSQL que comprueban orden pagada, intento exitoso, mismo entorno, identidad del archivo, 336 horas y contador inicial cero; bloquean toda actualización y eliminación de derechos en esta fase. Las cinco guardas R01 no se cambian. No existe servicio de concesión. Dado que R01 todavía impide transiciones a `PAID` y `SUCCEEDED`, B-02B no puede producir una concesión positiva. Esa prueba corresponde a B-03, después de incorporar evidencia verificada del proveedor y evolucionar los triggers en una migración explícita.

La futura disponibilidad exige estado `ACTIVE`, `now < expires_at`, `successful_downloads < 3` y verificación de existencia y digest de la versión privada. Esta fase no consulta archivos, autoriza enlaces ni modifica el contador. Reemisiones futuras compartirán el mismo derecho y su saldo.

La aceptación local cubre únicamente la estructura del derecho. La versión privada verificable sigue pendiente; B-03 deberá exigir el snapshot completo antes de Checkout, verificar el pago y registrar concesión y auditoría en una misma transacción. B-04 conserva enlaces y correo; B-05, medición de descargas; B-06, soporte y cambios administrativos auditados. B-02 permanece abierto.

## Auditoría y dependencias

No se registran eventos de concesión ficticios. B-03 debe extender de forma coherente `OrderAuditEvent` para concesión, actor, motivo y correlación, y ejecutar pago confirmado, concesión y auditoría en la misma transacción. B-04 requiere correo y enlaces; B-05 define operaciones/reservas y evidencia de descarga exitosa; B-06 implementa suspensión, revocación y soporte auditado. La operación necesita almacenamiento privado versionado y permisos PostgreSQL que impidan a usuarios ordinarios desactivar triggers.

Los triggers no protegen contra un dueño o administrador de base con privilegios para deshabilitarlos. SQLite valida escrituras normales del modelo, pero SQL directo puede eludir las guardas PostgreSQL. El catálogo actual expone una clave lógica mutable y no tiene revisión ni digest verificable: B-03 debe resolver ese mecanismo antes de habilitar Checkout o concesión comercial. La existencia de este modelo no autoriza pagos ni entrega.

## Verificación local

PostgreSQL 16 aislado: 8/8 pruebas focalizadas B-02B; suite completa 161/161 sin omisiones; cuatro pruebas concurrentes existentes ejecutadas y correctas. SQLite: 8 pruebas focalizadas descubiertas, seis aplicables correctas y dos omisiones de guardas SQL; suite completa 161 descubiertas, 151 aplicables correctas y diez omisiones justificadas. `manage.py check`, `makemigrations --check --dry-run` y `git diff --check` correctos. En una base desechable se aplicó `0006` (cinco triggers R01 y dos B-02B), se revirtió solo `0006` (cinco R01) y se reaplicó (siete en total). Ningún objeto R01 fue modificado o eliminado.
