# B-03D — Confirmación financiera local y concesión atómica

**Estado:** implementación local del 11/11/2026, pendiente de revisión y aceptación técnica del promotor. No constituye activación comercial. B-03 continúa abierto.

## Alcance verificable

`financial_provider.py` contiene exclusivamente un proveedor determinista en memoria, sin cliente HTTP, claves ni conexión a Stripe. `financial_services.py` consulta Session, PaymentIntent, todas las líneas y el evento `payment_intent.succeeded` simulado; valida cuenta TEST, orden, importe de 49,900 centavos en la demostración, MXN, Price ID, Product ID, cantidad 1, captura automática e identidad del archivo. `Event.created` en UTC se fotografía en `FinancialVerification.paid_at` junto con `success_event_id` y `paid_at_source=stripe_pi_succeeded_event_created`. Si falta ese evento, no se concede el derecho.

`FinancialVerification` conserva hechos normalizados y códigos saneados, sin payload completo ni datos de tarjeta. `REVIEW` registra evidencia temporal insuficiente, una respuesta incompatible, contradicción o archivo incoherente; cuando la consulta falla antes de obtener datos fiables, sus referencias comerciales son las **esperadas localmente**, no hechos verificados del proveedor. `PENDING_DELIVERY` registra un cobro externo observado con archivo temporalmente no disponible, sin facultad para conceder. Tras recuperar y verificar de nuevo el archivo se crea una verificación distinta `READY`; solo esta puede originar la concesión. La operación PostgreSQL restringida confirma intento y orden, crea el único derecho de 336 horas y tres descargas, audita, marca la verificación y, si existe, el evento B-03C causal, en una transacción. Ningún retorno de navegador confirma pago.

## Roles y guardas

La migración `0016` crea `mp_b03d_owner` y `mp_b03d_executor_test` como roles `NOLOGIN` y sin privilegios administrativos. Solo `mp_b03d_executor_test` recibe `EXECUTE` en `store_b03d_record()` y `store_b03d_confirm()`. Los logins de trabajador se aprovisionan por separado y son miembros únicamente de ese rol. La función es `SECURITY DEFINER`, pertenece a `mp_b03d_owner` y fija `search_path=pg_catalog,public,pg_temp`; `CREATE` en `public` se revoca a `PUBLIC`. Los triggers R01 usan referencias no cualificadas, por eso `public` permanece en la ruta protegida. El rol web debe ser dueño de ninguna tabla, no tener membresía financiera, `CREATE` en `public`, `TRIGGER` ni permiso de ejecutar esas funciones. `session_user` y `current_user` se comprueban junto con estados e identidades persistidas; ninguna variable de sesión sirve como autorización.

Los tests usan dos **logins PostgreSQL reales con contraseñas aleatorias solo en memoria**, uno financiero y uno web. Comprueban que el web no puede ejecutar la función ni escribir estados financieros, y que los modelos financieros no están registrados en Django Admin. El rol de migración de CI es privilegiado para crear bases y roles; esa credencial no debe usarse en el proceso web. La aplicación no define aún credenciales de trabajador para TEST externo ni LIVE. La preparación de roles de producción, secretos, rotación y separación de bases queda pendiente de infraestructura. La migración revierte funciones y definiciones de triggers, pero conserva los roles globales vacíos para no afectar otras bases del clúster.

## Recuperación e idempotencia

La consulta al proveedor y la lectura del archivo ocurren fuera de los bloqueos. El registro de `FinancialVerification` permanece si la concesión falla, de modo que el trabajador puede reintentar sin crear una Session ni otro cargo. Una versión ausente o un fallo temporal mantiene orden `AWAITING_PAYMENT`, intento `SESSION_OPEN` y verificación `PENDING_DELIVERY`; la restauración de la misma versión permite una nueva verificación `READY` y la concesión. Una identidad distinta exige revisión. La clave de verificación deriva determinísticamente de cuenta, entorno, Session, PaymentIntent, evento de éxito y resultado de archivo. La unicidad del derecho por orden e intento, los bloqueos y la función restringida impiden una segunda concesión. Un reintento ya aplicado devuelve el mismo derecho.

La conciliación sin webhook usa la misma consulta y función, con `provider_event_id=NULL`; no fabrica una fila que aparente recepción firmada. En esta fase se invoca manualmente desde el servicio interno, **no existe programador ni adaptador Stripe real**. Una solicitud B-03B `UNCERTAIN` sin Session ID aún requiere recuperación de identidad del proveedor antes de B-03D operativo. Una contradicción B-03C correlacionada bloquea la concesión. Las respuestas incompletas o inconsistentes no producen confirmación parcial.

## Validación manual del promotor: compra sintética de $499 MXN

El promotor verificó de forma independiente dos órdenes en un laboratorio PostgreSQL 16 desechable, con archivos, cuenta, credenciales y proveedor de pago exclusivamente sintéticos. Las consultas SQL se hicieron fuera del servicio Django. No se contactó Stripe ni se realizó una compra comercial.

- **Orden 1 — confirmación:** `Order=PAID`, `PaymentAttempt=SUCCEEDED`, una `FinancialVerification`, un `DeliveryEntitlement` activo y tres eventos financieros auditados (`paid`, `succeeded`, `entitlement_granted`). El evento del proveedor quedó aplicado.
- **Reejecución de la misma confirmación:** devolvió `RESULT applied`, conservó los identificadores y los recuentos `1,1,3` de verificaciones, derechos y eventos financieros auditados, respectivamente. No se creó otro derecho ni otra transición financiera.
- **Orden 2 — fallo inyectado:** `synthetic grant failure` interrumpió la concesión. Persistieron `Order=awaiting_payment`, `PaymentAttempt=session_open`, verificación `ready` y webhook `pending_reconciliation`, con cero derechos y cero transiciones financieras. La verificación previa permanece como evidencia recuperable; la transacción financiera sí se revirtió íntegramente.
- **Rol web:** un intento de actualización SQL directa fue rechazado y la orden permaneció intacta. La comprobación de permisos mostró `web_can_update=t` y `web_can_confirm=f`. No se conservó el mensaje específico de error de ese intento SQL, por lo que la evidencia no permite atribuir el rechazo a un texto concreto de la guarda.

El procedimiento reproducible debe ejecutarse únicamente contra una base desechable y con credenciales sintéticas aportadas en el laboratorio; esta documentación no conserva contraseñas ni identificadores privados. El laboratorio del promotor permanece disponible para revisión y no debe eliminarse sin su confirmación. La prueba automatizada `store.test_financial_confirmation.FinancialConfirmationTests.test_paid_purchase_without_webhook_and_idempotent_retry` cubre adicionalmente la compra simulada y el reintento idempotente.

## Límites antes de Stripe TEST y publicación

- Solo funciona el proveedor simulado y el rol financiero TEST; no se implementó cliente Stripe ni se contactó su API. El webhook sigue sin ruta pública y Checkout público no está habilitado.
- La API de eventos de Stripe permite consultar eventos durante 30 días; si no se recupera `payment_intent.succeeded`, se registra revisión, sin fecha inventada ni concesión automática.
- El adaptador local verifica bytes y SHA-256 antes de llamar a la función. PostgreSQL comprueba la identidad registrada, pero no puede volver a leer los bytes dentro de la transacción. Retención y disponibilidad GCS siguen pendientes.
- La función de base confía en que el trabajador financiero haya consultado al proveedor auténtico. El rol trabajador y su credencial Stripe serán parte de la frontera de confianza; un superusuario o dueño de base sigue pudiendo alterar la instalación.
- Faltan orquestación de reintentos, alertas operativas, flujo público, correo, entrega y políticas de reembolso/contracargo. No habilitar pagos TEST externos ni LIVE con este incremento aislado.
