# B-02A — núcleo transaccional de órdenes

**Estado:** aceptada en alcance técnico local por el promotor el 10 de noviembre de 2026. No autoriza publicación ni pagos.

## Decisiones

Las decisiones siguientes fueron autorizadas para implementación en la instrucción del promotor del 10 de noviembre de 2026. B-02-D01 había sido aprobada expresamente el 9 de noviembre de 2026.

| ID | Decisión aplicada |
| --- | --- |
| B-02-D01 | Una orden contiene exactamente un producto, por FK obligatoria; la cantidad es siempre 1 y no existe carrito ni línea de orden. |
| B-02-D02 | Nombre, versión, importe en centavos, moneda, condiciones de entrega y referencias comerciales se fotografían al crear la orden. El servicio nunca recalcula el snapshot. |
| B-02-D03 | Se reserva referencia de revisión de archivo y hash SHA-256 en el snapshot. El catálogo actual solo ofrece una clave lógica mutable; en B-02A ambos campos verificables permanecen vacíos. No hay entrega comercial. |
| B-02-D04 | Los intentos de pago se registran por separado. Orden e intento tienen estados independientes; REVIEW identifica contradicciones y no concede acceso. |
| B-02-D05 | Solo MXN. La conversión Decimal × 100 exige centavos exactos y valor positivo, sin redondeo. |
| B-02-D06 | Una orden cerrada no admite nuevos intentos ni reactivación. La base impide más de un intento no terminal por orden. |

## Frontera implementada

`Order`, `PaymentAttempt` y `OrderAuditEvent` tienen restricciones de unicidad, moneda, entorno e importe. Los servicios internos crean órdenes idempotentes, preparan intentos, expiran reservas locales sin referencias externas y cierran órdenes creadas sin pago; cada cambio registra auditoría en la misma transacción. El orden de bloqueo es orden, luego intento. No se mantiene un bloqueo durante llamadas de red.

Los estados `PAID`, `SUCCEEDED`, `SESSION_OPEN` y `PROCESSING` existen para la evolución del modelo, pero B-02A no ofrece servicios que los activen. No existen Checkout Sessions, webhooks, derechos de entrega, magic links ni descargas comerciales. Los UUID públicos identifican órdenes, pero no autorizan acceso.

## Pendientes independientes

- B-03: integración de Checkout Sessions, verificación del proveedor, referencias externas definitivas y transición segura a pago confirmado.
- B-04/B-05: derechos y entrega privada, condicionados a una versión de archivo verificable. La clave lógica actual no prueba la identidad del contenido.
- B-06–B-08: correo, reemisión, soporte, conciliación, reembolsos y operación.
- Privacidad, retención de datos, términos comerciales, operación fiscal y controles de publicación siguen sujetos a sus decisiones y pruebas.

### R01 — protección de escrituras

En Django, `save()`, `QuerySet.update()` y `bulk_update()` rechazan cambios de snapshot, identidad transaccional y estados sensibles; `bulk_create()` se reserva para procesos auditados. Los servicios usan una ruta interna de transición bajo `transaction.atomic()` y bloqueo de filas. En SQLite, la creación mediante `save()` y las transiciones de servicio registran el evento dentro de la misma transacción.

En PostgreSQL, la migración `0004_b02a_r01_integrity_guards` instala triggers reversibles: impiden alterar el snapshot, crear órdenes o intentos en estados ajenos a B-02A, reactivar cierres, asignar estados de pago y editar o eliminar eventos. Una creación o transición permitida inserta su auditoría en la misma sentencia SQL. Si la inserción del evento falla, se revierte la operación. La inserción de intentos comprueba el estado, entorno e importe de la orden bajo bloqueo.

La protección SQL no cubre a administradores o dueños de la base capaces de deshabilitar triggers, alterar funciones o escribir auditoría falsa. SQLite no tiene estos triggers: SQL directo o APIs ORM de bajo nivel que deliberadamente eviten el QuerySet protegido pueden saltar los controles locales. Las referencias externas y campos operativos de intentos conservan capacidad de actualización para B-03; su vinculación confiable deberá diseñarse allí. B-03 también deberá evolucionar explícitamente los triggers antes de habilitar estados de Checkout o pago verificado. La concordancia entre orden e intento se comprueba en PostgreSQL al insertar; en SQLite se valida en modelo/servicio.

## Verificación local del 10 de noviembre de 2026

Pruebas focalizadas iniciales: 11/11 en PostgreSQL 16, incluidas dos carreras de escritura reales; SQLite: 9 aplicables correctas y dos omisiones explícitas. Suite completa inicial: 143/143 en PostgreSQL 16, sin omisiones; SQLite: 139 aplicables correctas y cuatro omisiones explícitas (dos previas de descargas, dos nuevas de B-02A). Django check y control de migraciones sin cambios pendientes. En ese corte, los resultados aún estaban pendientes de revisión del promotor.

R01: 21/21 pruebas focalizadas PostgreSQL 16, sin omisiones; 15 aplicables correctas en SQLite, con seis omisiones PostgreSQL específicas. Suite completa: 153/153 en PostgreSQL 16, sin omisiones; 145 aplicables correctas en SQLite, con ocho omisiones de concurrencia o guardas SQL PostgreSQL. Django check y control de migraciones correctos.

**Cierre técnico local (10-nov-2026):** el promotor autorizó la aceptación y publicación de PR para B-02A. En PostgreSQL 16 desechable se aplicaron las migraciones hasta `0004`, se comprobaron cinco triggers R01, se revirtió `0004` (cero triggers) y se reaplicó (cinco triggers). Se repitieron 21/21 pruebas focalizadas, 2/2 concurrentes y 153/153 de la suite completa, sin omisiones; Django check, control de migraciones y diff correctos. Una demostración separada con datos sintéticos confirmó snapshot, idempotencia, rechazo de cambios indebidos y auditoría. B-02A no incorpora pagos, correos ni entregas comerciales; B-02/B-03 y las condiciones de publicación permanecen abiertos.
