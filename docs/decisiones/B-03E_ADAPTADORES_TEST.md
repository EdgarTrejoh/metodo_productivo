# B-03E1 — Adaptadores Stripe TEST

**Estado:** implementación local pendiente de revisión del promotor. No habilita Checkout público, webhook público ni pagos TEST.

## Contrato y límites

B-03E1 conecta los contratos internos B-03B y B-03D con `stripe-python==17.0.0` y `StripeClient` por instancia. Los proveedores simulados permanecen. Las rutas existentes no crean Checkout Sessions. El adaptador real exige `STRIPE_TEST_ADAPTER_ENABLED=1`, cuenta configurada y clave restringida TEST; por defecto no puede llamar a Stripe. Nunca admite LIVE ni una clave LIVE.

La cuenta configurada y la clave pertenecen a la frontera operativa de confianza. El adaptador consulta `accounts.retrieve_current` y contrasta el ID configurado antes de otras llamadas. Los objetos Price, Session, PaymentIntent, línea y Event se normalizan solo si son TEST y tienen los campos completos y congruentes. Esta verificación de cuenta solo se ha probado con el SDK simulado, no con una cuenta Stripe real.

La orden mantiene un producto, cantidad uno, MXN, Price ID y archivo versionado. El adaptador no usa `price_data`, cupones, impuestos automáticos, envío ni métodos diferidos. Envía `allowed_payment_method_types=['card']` y exige que la respuesta anuncie solo tarjeta. No envía `payment_method_types` al SDK. Una respuesta incompatible no entrega la URL. Cuenta y permisos de la clave son condiciones de conexión TEST aún no acreditadas.

## Checkout e idempotencia

`start_checkout()` conserva su clave local y la pasa como idempotency key a Stripe. Primero consulta un Price activo, de pago único, MXN y de importe exacto. La creación usa una línea y cantidad uno, con destinos de retorno configurados. Una Session vinculada se recupera por ID. Stripe no ofrece GET por idempotency key; ante `UNCERTAIN` sin ID solo se permite repetir exactamente la creación con la misma clave y parámetros dentro de una ventana conservadora menor que las 24 horas de retención mínima. Fuera de ella se exige conciliación manual; nunca se crea una operación nueva por inferencia. Las llamadas ocurren fuera de bloqueos PostgreSQL. Un error de red o respuesta incompleta deja la solicitud incierta.

## Conciliación

El adaptador financiero consulta Session, PaymentIntent, todas las páginas de líneas y eventos `payment_intent.succeeded` en TEST. La fuente de `paid_at` sigue siendo `Event.created`, validada por B-03D contra el PI, Session y orden; el retorno del navegador y el webhook por sí solos no confirman. Eventos ausentes, múltiples o fuera del plazo consultable no producen concesión. La consulta de eventos tiene límite operativo de 1,000 filas y el plazo de disponibilidad de Stripe; al agotarse queda pendiente de revisión. `FinancialVerification`, roles y funciones PostgreSQL de B-03D conservan la única transición financiera autorizada. No se modifican triggers ni migraciones.

## Criterios de aceptación local

1. Sin activación ni credenciales, ninguna llamada al SDK alcanza la red.
2. El proveedor simulado y las pruebas anteriores mantienen su comportamiento.
3. Price ID, producto, moneda, importe, cuenta configurada, entorno, recurrencia y vigencia se validan antes de exponer una Session.
4. Se crea una Session de pago único, una línea, cantidad uno y clave idempotente estable; una Session de respuesta inválida no se vincula.
5. Doble solicitud y respuesta perdida no producen dos operaciones locales; el reintento remoto conserva clave y parámetros, y se bloquea después de la ventana segura.
6. La consulta financiera pagina todas las líneas y eventos, rechaza campos incompletos, LIVE, descuentos, impuestos, envío, contradicciones y resultados temporales incompatibles.
7. Un fallo de red queda como resultado incierto o pendiente recuperable; no confirma `PAID`, `SUCCEEDED` ni concede derecho por sí solo.
8. Las pruebas usan cliente SDK inyectado o transporte falso y prohíben tráfico real; se ejecutan además Django check, migraciones y suite PostgreSQL 16.

## Conexión TEST posterior

Configurar `STRIPE_TEST_RESTRICTED_KEY` en un gestor de secretos y `STRIPE_TEST_ACCOUNT_ID` por separado, con permisos mínimos para cuenta, Price, Checkout Session, PaymentIntent, líneas y Event. Mantener `STRIPE_TEST_ADAPTER_ENABLED=0` hasta la autorización operativa. Verificar titularidad de clave, versión API de la cuenta, respuesta de tarjeta exclusivamente, destinos HTTPS y archivo privado retenido; comprobar la conectividad en un ambiente TEST aislado. La confirmación debe usar el rol conciliador de B-03D, distinto del rol web. Autorizar expresamente una prueba de humo de bajo volumen antes de habilitar el adaptador. Este incremento no crea Session remota, cargo, webhook público, correo ni descarga.

## Evidencia local del 12-nov-2026

SDK instalado en una imagen local aislada. Pruebas del adaptador: 14/14 en PostgreSQL 16, incluida una carrera de dos conexiones; confirmación sintética de $499 MXN mediante el rol conciliador: 1/1, con reejecución idempotente y un derecho. Suite completa: 210/210 en PostgreSQL 16 sin omisiones; SQLite: 210 descubiertas, 180 aplicables correctas y 30 omisiones justificadas por pruebas exclusivas de PostgreSQL. `manage.py check`, `makemigrations --check --dry-run` y `git diff --check` correctos. No se usaron claves reales ni se llamó a la API de Stripe. La compatibilidad con respuestas reales, permisos efectivos de una clave restringida, vigencia de eventos y disponibilidad operativa del archivo requieren una prueba TEST autorizada posterior.

## Correcciones de auditoría H-01 a H-03 — 12-nov-2026

- **H-01:** `UNCERTAIN` reintenta exclusivamente con la misma clave y parámetros antes de 23 horas desde la reserva. Un `CALLING` que sobreviva a una terminación del proceso puede pasar a `UNCERTAIN` después de 30 segundos y repetir esa misma llamada; antes queda pendiente. A partir de 23 horas no se reintenta por API sin conciliación. El intento activo de la orden impide abrir una operación distinta. Los errores HTTP de creación, incluidos 500 persistentes, no se interpretan como ausencia de sesión o cargo. La transición a incertidumbre y su auditoría se registran una sola vez.
- **H-02:** la indisponibilidad temporal del Price produce `CheckoutPending` antes de crear `PaymentAttempt` o `CheckoutRequest`; un 404 o una respuesta comercial incompatible produce `InvalidOrderOperation`. Una consulta posterior puede continuar la misma intención sin estado financiero previo.
- **H-03:** las pruebas incorporan `stripe-python==17.0.0` real con `StripeClient` y un `HTTPClient` en memoria. Se observaron la codificación de la Session, el encabezado `Idempotency-Key`, las rutas de cuenta, Price, Session, PaymentIntent, líneas y eventos, la paginación de las dos últimas, campos opcionales, tiempos UTC y excepciones HTTP 500/404. El contenedor se ejecutó sin red. Los cuerpos simulados ejercen la deserialización del SDK; aún deben contrastarse contra respuestas auténticas de una cuenta TEST, especialmente permisos de la clave restringida, campos opcionales y disponibilidad histórica de eventos.

Verificación posterior: 23/23 pruebas focalizadas PostgreSQL 16 y 218/218 en suite completa PostgreSQL 16, sin omisiones. Se conservan roles, triggers y operación financiera restringida de B-03D. No se creó una sesión real.

**Salvedad pendiente de B-03E2:** definir y probar la conciliación operativa de una Checkout Session cuyo `POST` recibió errores HTTP 500 persistentes. Stripe puede repetir el mismo error para una clave idempotente aunque haya comenzado la ejecución. B-03E1 conserva la orden y su intento sin abrir otra operación y bloquea el reintento por API después de la ventana segura; no recupera automáticamente la identidad de una Session sin respuesta. Antes de habilitar cobros TEST se requiere un procedimiento autorizado de investigación con Stripe, vinculación verificable o resolución manual, sin generar un segundo cargo.
