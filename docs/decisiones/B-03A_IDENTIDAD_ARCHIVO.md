# B-03A — Identidad privada verificable

**Aceptado técnicamente en alcance local por el promotor el 11 de noviembre de 2026.** La aceptación no autoriza Checkout, infraestructura comercial ni publicación del portal.

`ProductFileVersion` identifica producto, backend, objeto, versión, SHA-256 y tamaño. La pareja objeto/versión es única entre backends porque el snapshot existente no conserva el backend. Una selección explícita vincula la versión comercializable al producto. `create_order()` copia la identidad completa al snapshot cuando existe versión seleccionada y verifica el contenido antes de crear la orden. Las órdenes anteriores conservan su snapshot incompleto y `assert_order_checkout_ready()` las rechaza. El producto que aún no tiene versión puede seguir creando órdenes internas históricas para preservar B-02A, pero esas órdenes nunca son aptas para Checkout.

El backend local lee `PRIVATE_PRODUCT_ROOT/<objeto>/<versión>` con identificadores restringidos, comprueba bytes y SHA-256, y distingue ausencia, inconsistencia y error temporal. La interfaz `open_version(object_identifier, version_id)` admite una futura implementación GCS que lea una generación explícita. No se implementó GCS ni se contactó Stripe. El backend local solo demuestra el contrato; no ofrece retención, alta disponibilidad ni protección contra borrado.

La identidad de `ProductFileVersion` es inmutable mediante `save()` y trigger PostgreSQL. Las órdenes mantienen las guardas R01 y B-02B. La selección de versión se serializa con la creación de orden mediante bloqueo del producto. Los cambios de precio o versión seleccionada del catálogo no alteran snapshots anteriores. `ProductFileSelectionEvent` registra cada cambio de selección en la misma transacción y es inmutable en PostgreSQL. El servicio actual es una operación interna automatizada: `system` identifica ese origen, no a una persona. Un futuro flujo administrativo autenticado deberá proporcionar identidad verificable del operador; no existe todavía.

## Decisiones arquitectónicas B-03 aprobadas el 11 de noviembre de 2026

| Decisión | Dirección aprobada | Condición aún pendiente |
|---|---|---|
| B-03-D01 | Precio fotografiado y total MXN verificado para Checkout. | Precisar contrato de Price ID, impuestos y descuentos antes de B-03B. |
| B-03-D02 | Archivo privado versionado con objeto, versión, digest y tamaño; Cloud Storage es el camino propuesto. | Configurar y aprobar GCS, IAM, retención, recuperación y costos en O-02/O-03. |
| B-03-D03 | Confirmar pago en servidor; contemplar métodos de confirmación diferida. | Definir cuáles métodos se ofrecerán inicialmente. |
| B-03-D04 | Vigencia desde el instante de éxito acreditado por Stripe, en UTC. | Especificar precedencia exacta de eventos y fuente de `paid_at` en B-03C. |
| B-03-D05 | No duplicar sesiones o cargos ante incertidumbre y conciliar reintentos. | Definir plazos y procedimiento operativo de recuperación en B-03B/C. |
| B-03-D06 | Proteger estados financieros y concesión mediante evidencia y permisos PostgreSQL diferenciados. | Diseñar roles y evolución precisa de triggers antes de B-03C. |

La aprobación de estas decisiones no configura infraestructura ni implementa Checkout, webhook o entrega. B-03A cubre únicamente la identidad y verificación local del archivo.

## Condiciones para continuar

B-03B deberá exigir `assert_order_checkout_ready()` antes de crear una Session y volver a comprobar la versión antes de confirmar una entrega. B-03C deberá verificar firma, importe y cuenta, evolucionar triggers para confirmación atómica y auditar concesión. B-04/B-05/B-06 permanecen independientes. La verificación previa al cobro no garantiza disponibilidad futura: se requieren retención, protección ante eliminación, monitoreo y recuperación.
