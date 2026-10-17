# D-05 — Primer lead magnet de Fase A

**Estado:** APROBADA por el promotor del proyecto  
**Fecha de propuesta:** 17 de octubre de 2026  
**Fecha de aprobación:** 17 de octubre de 2026  
**Responsable de la decisión:** promotor del proyecto  
**Evidencia:** autorización expresa del promotor durante la revisión documental del proyecto, incluido el ajuste final del correo transaccional

## Decisión aprobada

Se aprueba como primer lead magnet de Fase A una **plantilla Excel gratuita de flujo de efectivo de 13 semanas**, ya planteada como opción en la propuesta visual v0.2. Es un recurso gratuito obtenido mediante el recorrido J4: el correo entrega el enlace de acceso y el archivo se entrega tras la confirmación de descarga. Esta decisión define la identificación del recurso y su política de acceso; A-03 permanece pendiente de implementación y verificación.

La plantilla se presenta como apoyo para revisar el flujo de efectivo semanal. **El archivo Excel definitivo será elaborado y proporcionado externamente durante A-03 para integrarlo al flujo de descarga.** D-05 no diseña hojas, fórmulas ni formatos, ni desarrolla el Excel. El archivo es un recurso digital para entregar, no una funcionalidad que deba programarse dentro del portal.

### Separación de alcances

| Entregable | Alcance |
| --- | --- |
| Demostrador web de punto de equilibrio, D-04 | Herramienta gratuita sin registro ni archivo descargable; su aprobación no depende de D-05. |
| Lead magnet, D-05 | Plantilla gratuita con captura y consentimiento propios, entrega por correo y acceso de propósito específico en Fase A. |
| Herramientas Excel de pago, B-01 | Catálogo, funciones, precios, términos y entrega por definir en Fase B; esta plantilla no anticipa ni aprueba esos productos. |

La calculadora web puede enlazar al lead magnet cuando este se implemente. El enlace lleva al formulario J4; usar la calculadora no registra a la persona ni concede acceso automático al archivo.

### Captura, entrega y acceso aprobados

1. La página `/recursos/{lead-magnet}/` describe el contenido y solicita **nombre y correo** como datos mínimos del recorrido J4. El consentimiento necesario para entregar el recurso se presenta separado del consentimiento comercial opcional; las redacciones finales corresponden a D-06.
2. Un correo normalizado corresponde a un único lead, conforme a RN-015. Cada solicitud y consentimiento se registra sin crear un segundo lead para el mismo correo. La solicitud no implica suscripción comercial.
3. Tras el envío válido, la página de gracias indica que se revise el correo y sugiere el Check PyME. El correo transaccional contiene un enlace de acceso exclusivo para este recurso. Si el envío falla, se registra el estado y se ofrece un mensaje y un reintento apropiados, sin declarar entregado el recurso.
4. El enlace abre una página intermedia por `GET` sin consumir acceso. La persona confirma expresamente la descarga mediante `POST`; el archivo permanece en almacenamiento privado y se entrega mediante acceso controlado. La apertura del enlace no descarga automáticamente el archivo.
5. **Política aprobada:** vigencia de **3 días** desde la emisión y hasta **3 accesos autorizados por enlace**. Un acceso se consume cuando el servidor autoriza correctamente la entrega del archivo después del `POST`; esto no demuestra que el archivo haya quedado guardado, abierto o leído en el dispositivo. Un `GET`, un `POST` rechazado o un fallo detectado antes de autorizar la entrega no consumen accesos. La autorización no permite verificar de forma independiente fallos posteriores en el dispositivo.
6. Un doble clic o reenvío accidental de la misma operación debe ser idempotente: no consume dos accesos ni duplica el registro de entrega. La verificación del límite y la actualización del contador deben ser atómicas para impedir que solicitudes concurrentes autoricen más de tres accesos.
7. Si se pierde el enlace, la persona puede volver a solicitar el recurso con el mismo correo sin duplicar el lead. La emisión de un nuevo enlace para ese correo y recurso invalida el anterior; el enlace nuevo tiene su propia vigencia y contador. Se aplicarán límites razonables de frecuencia a solicitudes y reenvíos; sus umbrales se definirán técnicamente durante A-03, sin fijarlos en D-05. Estas reglas son independientes de las compras de Fase B, que conservan 14 días y tres descargas exitosas por derecho de entrega.

### Medición de la entrega

La **solicitud** del recurso, el **envío del correo transaccional** y la **autorización de entrega del archivo** son hechos distintos. `LEADMAGNET_DELIVERED` representa una entrega del archivo autorizada correctamente por el servidor tras la confirmación mediante `POST`. Se registra una sola vez por operación de acceso autorizada; no acredita que el archivo se haya guardado en el dispositivo.

No registrar `LEADMAGNET_DELIVERED` por capturar nombre y correo, crear o recuperar un lead, enviar el correo, abrir el enlace ni mostrar la página intermedia. `LEAD_CREATED` corresponde únicamente al alta de un lead nuevo y `EMAIL_FAILED` al fallo de correo; los controles de frecuencia, idempotencia y concurrencia son operativos y no crean eventos de negocio adicionales.

### Correo de entrega aprobado en su alcance funcional

**Asunto:** Tu plantilla gratuita de flujo de efectivo de 13 semanas

**Cuerpo funcional:** «Hola, {nombre}. Gracias por solicitar la plantilla de flujo de efectivo de 13 semanas de Método Productivo. Para acceder al archivo, abre este enlace: {enlace}. El enlace estará disponible durante 3 días y permite hasta tres accesos autorizados. Si no solicitaste el recurso, puedes ignorar este mensaje.»

El correo se limita a la entrega del recurso, vigencia, condiciones de acceso e información transaccional necesaria. No incorpora una invitación al Check PyME, publicidad ni presupone consentimiento comercial. El CTA al Check PyME permanece en la página de agradecimiento. Los textos finales, identificación del remitente, aviso de privacidad y preferencias se revisan en D-06 antes de publicar.

### Medición y criterios de aceptación para A-03

- El archivo Excel definitivo proporcionado externamente se integra al flujo de entrega sin desarrollar su contenido dentro del portal.
- El formulario y el correo cumplen J4: `PAGE_VIEW`, `LEAD_CREATED` solo al crear un lead y `EMAIL_FAILED` cuando corresponda. Solicitar el recurso y enviar el correo no generan `LEADMAGNET_DELIVERED`.
- `LEADMAGNET_DELIVERED` se registra solo cuando el servidor autoriza correctamente la entrega tras el `POST`; no al capturar datos, crear o recuperar el lead, enviar el correo, abrir el enlace o mostrar la página intermedia. Su registro es idempotente por operación.
- El mismo correo puede volver a solicitar el recurso sin duplicar el lead. Consentimientos e interacciones conservan su propio registro y finalidad; emitir el enlace nuevo invalida el anterior para ese correo y recurso.
- `GET` no consume accesos. Se prueban confirmación explícita por `POST`, vencimiento de 3 días, máximo de 3 accesos autorizados por enlace, intentos fallidos, doble clic, reenvío accidental y solicitudes concurrentes con contador atómico.
- Se prueban los límites razonables de frecuencia para solicitudes y reenvíos conforme a los umbrales definidos durante A-03, sin bloquear la reemisión legítima.
- El archivo no queda en una ruta pública permanente. El enlace de este recurso no permite consultar el Check ni archivos de pago.
- La entrega no depende de aceptar comunicaciones comerciales. La baja comercial no impide el correo transaccional solicitado.
- Las páginas del recorrido y el correo se revisan en móvil y escritorio; las páginas permiten operar con teclado y lectores de pantalla.

## Fundamento y dependencias

- BRD v0.6, RF-A03, RF-A09, RF-A11 y RN-015: datos mínimos, consentimiento por finalidad, entrega por correo y lead único por correo.
- Concepto y alcance v0.8: recurso o enlace enviado por correo, sin cuentas públicas y con acceso por propósito.
- Sitemap y journeys v0.2, J4: formulario, página de gracias, correo, acceso explícito, reenvío al mismo correo y eventos.
- Propuesta visual v0.2: plantilla de flujo de efectivo de 13 semanas como propuesta de lead magnet, seleccionada y aprobada en D-05.
- Arquitectura v0.5: almacenamiento privado, magic link de propósito específico, `GET` sin consumo y valores de trabajo de 3 días/tres confirmaciones. D-05 aprueba que cada confirmación consume un acceso solo si el servidor autoriza correctamente la entrega.
- D-04 aprobada: el demostrador web gratuito y la futura herramienta Excel de pago conservan alcances separados.

**Estado de implementación:** D-05 quedó aprobada el 17 de octubre de 2026; A-03 sigue pendiente de implementar y verificar. D-06 cerrará los textos de consentimiento y privacidad. Durante A-03 se definirán los umbrales técnicos de frecuencia y se integrará el Excel definitivo proporcionado externamente. La aprobación documental de D-05 no acredita la implementación ni la verificación de A-03.
