# Bloque inicial B0 - 16 oct 2026

Fuente: Concepto v0.8, BRD v0.6, arquitectura v0.5, Check v1.3 y catálogo v0.1.
Implementación local de desarrollo. No equivale a Fase A terminada ni autorizada para producción.
Las secciones de B0 conservan el estado técnico al 16 de octubre; las decisiones tomadas el 17 se registran más abajo y no equivalen a implementación.

## Implementado
- Django SSR; configuración PostgreSQL y SQLite para prueba local sin infraestructura.
- Cuestionario de ocho preguntas, sin respuestas implícitas; validación servidor.
- Captura nombre/correo/empresa; WhatsApp opcional; consentimiento comercial separado.
- Resultado solo tras persistencia; selección determinista, versión y snapshot inmutable de informe/contacto.
- PDF generado desde el snapshot, orientación idempotente, lead único y registro de eventos críticos.
- Admin con requisito OTP; sin credenciales predeterminadas.
- Acceso por sesión y ejecución, sin IDs como credenciales ni recuperación por correo.
- Caducidad provisional de 30 minutos desde inicio, configurable SOLO para desarrollo. Al corte B0 del 16 de octubre aún no existía una decisión de negocio aprobada; ver D-02 en la actualización del 17 de octubre.
- Salida explícita o visita a otra ruta del portal invalida contexto. Cabeceras no-store.

## Límites y siguiente bloque
- RF-A17 NO cerrado: recarga conserva contexto; cerrar pestaña/navegar fuera no se detecta de forma infalible. No afirmar invalidación inmediata. Implementar las reglas aprobadas en D-02 y ejecutar sus pruebas de aceptación antes de producción.
- Retención: fecha de 12 meses calculada; faltan borrado/anonimización, tratamiento de leads compartidos, backups y verificación legal.
- Avisos legales son textos de prueba; correo exclusivamente en memoria. Orientación registra solicitud, no envía notificaciones.
- PDF funcional provisional: no reproduce todavía la maqueta editorial ni incluye todas las respuestas textuales. Aceptación PDF/pantalla pendiente.
- Falta rate limiting compartido, CAPTCHA, recuperación de errores operativos y revisión integral de accesibilidad y diseño. El 17 oct se verificó el flujo en Chrome escritorio y Edge con viewport móvil; no equivale a QA visual exhaustivo.
- PostgreSQL/concurrencia se configuraron pero NO se verificaron en servidor real; SQLite no prueba locks de PostgreSQL.
- Sin calculadora, blog, lead magnet, métricas de sesiones calificadas, recursos pagados ni infraestructura GCP.
- No registrar PDF_DOWNLOADED por generar una respuesta: no prueba recepción completa.
- Compras de Fase B conservan 14 días y hasta tres descargas exitosas; no se implementaron ni alteraron.

## Actualización de decisiones — 17 de octubre de 2026

**D-02 — APROBADA.** El promotor aprobó 30 minutos de inactividad renovables mediante peticiones válidas y un límite absoluto de 2 horas desde el inicio del cuestionario. También aprobó las reglas de revocación, navegación y acceso entre pestañas de la misma sesión, con la limitación técnica para detectar el cierre externo de una pestaña y sin recuperación pública del diagnóstico. [Decisión D-02](decisiones/D-02_CONTEXTO_ACTIVO_CHECK.md). La implementación B0 conserva una caducidad provisional de 30 minutos desde el inicio; todavía no cumple íntegramente D-02 ni cuenta con sus pruebas de aceptación.

**D-03 — APROBADA.** El promotor aprobó `PDF_DOWNLOADED` como entrega reportada por el cliente y registrada tras un acuse válido asociado al intento. Generar el PDF o enviar la respuesta HTTP no basta para registrar el evento; el acuse tampoco certifica almacenamiento, apertura o lectura del archivo. [Decisión D-03](decisiones/D-03_MEDICION_DESCARGA_PDF.md). Están pendientes los registros de intentos, la recepción y validación de acuses, la idempotencia y las métricas correspondientes. La ventana de espera del acuse se definirá técnicamente en C-05, sin valor asignado por ahora.

| Componente | Decisión | Implementación |
| --- | --- | --- |
| D-02 — Contexto activo | Aprobada | Pendiente de completar y verificar. |
| D-03 — Medición PDF | Aprobada | Pendiente de implementar y verificar. |
| RF-A17 | Criterios definidos en D-02 | No cerrado. |
| C-05 — Medición PDF | Alcance definido en D-03 | No iniciado. |

**Criterio de estado:** «Aprobado» indica decisión expresa del promotor; «implementado», funcionalidad incorporada al código; «verificado», pruebas o evidencia de cumplimiento. La aprobación documental no acredita los otros dos estados.

## Propuesta de siguiente bloque B1
Implementar las reglas aprobadas en D-02 y ejecutar sus pruebas de aceptación; cerrar textos de captura; realizar pruebas reales con PostgreSQL y fallos; PDF final, notificación y atención de orientación; rate limiting y automatización de retención. Planificar después C-05 para implementar D-03, sin darlo por iniciado. Después núcleo editorial y lead magnet.

## Portal de Fase A — Entrega 1 (17 de octubre de 2026)

El promotor aprobó **CON SALVEDADES** la estructura integral navegable tras las rondas AV-01–AV-29: Home, identidad oficial, navegación, pie, páginas públicas estructurales y acceso al Check B0. La evidencia técnica se resume en [VERIFICACION.md](VERIFICACION.md). Esta aceptación visual no equivale a H2 completo, publicación ni funcionalidad de calculadora, lead magnet, blog, contacto o páginas legales definitivas.

**A-01 continúa EN CURSO:** faltan el favicon oficial y la instrumentación y verificación de clics principales. La prueba en dispositivo móvil físico corresponde a la actividad de verificación posterior. H2 sigue pendiente de aceptación integral; D-10 permanece aprobada. La siguiente capacidad funcional prioritaria del plan es **A-02 — calculadora de punto de equilibrio**, regida por D-04, sin inicio de Entrega 2 en este cierre.

## Portal de Fase A — A-02 y Entrega 2 (19 de octubre de 2026)

El promotor aprobó **CON SALVEDADES** la implementación funcional y visual de A-02, incluidos A02-AV01–AV08. La calculadora mensual de punto de equilibrio opera en Django sin JavaScript obligatorio, con tres entradas validadas, cálculo decimal en servidor y cuatro resultados según D-04. [Evidencia de verificación](VERIFICACION.md). Esta actualización no cambia el corte histórico de B0 ni las decisiones aprobadas.

**A-02 y Entrega 2 continúan EN CURSO; D-04 permanece APROBADA.** `TOOL_STARTED` y `TOOL_COMPLETED` se registran por interacción sin importes, pero O-08 sigue pendiente de integración y verificación transversal. La limitación de AV-06 queda aceptada: F5 puede reenviar el POST; el servidor evita eventos duplicados y regresa a un GET vacío, sin persistir importes ni exigir JavaScript. Los estados visuales positivo, cero y negativo de AV-08 quedaron aprobados tras revisión de escritorio y móvil.

El siguiente recorrido funcional de la secuencia de Entrega 2 es A-05/A-06 (blog y videos), sujeto a autorización de ejecución; A-03 conserva la dependencia del Excel definitivo externo para su entrega real. No se iniciaron esos trabajos en este cierre.

## Portal de Fase A — cierre funcional y visual A-05/A-06 (20 de octubre de 2026)

El promotor **aprobó y cerró el alcance funcional y visual local de A-05 y A-06**, incluidos A05-AV09 y AV10. El blog ofrece artículos publicados y vigentes por categoría y slug, editor Quill, sanitización HTML, tablas, biblioteca de imágenes, vista previa protegida y administración de borradores, publicación y retiro en el backoffice con OTP. La sección Contenidos presenta videos externos publicados y los reproduce a solicitud del visitante. El promotor verificó manualmente la publicación y retiro de artículos y la reproducción efectiva de YouTube; [evidencia técnica](VERIFICACION.md).

Un artículo y un video sintéticos utilizados para la revisión quedaron como **borradores locales**; no permanecen publicaciones sintéticas visibles. A-05/A-06 están cerradas en este alcance de desarrollo, sin afirmar habilitación productiva ni cierre de Entrega 2. Siguen pendientes por separado el contenido real aprobado, O-03 para persistencia de medios, los controles de publicación y las demás actividades de H2–H4. A-02 y O-08 conservan su estado anterior. No se inició A-07 en ese cierre.

## Portal de Fase A — A-07 en revisión (20 de octubre de 2026)

Se implementó el formulario público de contacto para comentarios y solicitudes, con confirmación, persistencia y seguimiento en el backoffice OTP. El correo se exige cuando se solicita respuesta; un comentario sin respuesta puede enviarse sin contacto. La notificación interna usa correo local de desarrollo si se configura un destinatario y registra su resultado sin perder la solicitud. A-07 y Entrega 2 permanecen **EN CURSO** hasta revisión del promotor. O-04, O-07, O-08, revisión jurídica y publicación siguen pendientes. [Evidencia](VERIFICACION.md).

## Portal de Fase A — ajuste A07-AV01 (21 de octubre de 2026)

Por decisión del promotor, el formulario de contacto exige nombre y correo válido tanto para comentarios como para solicitudes; se retiró la casilla pública de respuesta. Comentario identificado no compromete respuesta y solicitud identificada pasa a seguimiento. La regla se aplica en el formulario sin alterar el modelo ni los registros históricos que pudieran carecer de esos datos. La suite completa quedó verde tras cerrar una respuesta de archivo en una prueba aislada de A-05; no cambió su funcionalidad. A-07 permanece **EN CURSO** para revisión del promotor. O-04, O-07, O-08, revisión jurídica y publicación continúan pendientes. [Evidencia](VERIFICACION.md).

## Portal de Fase A — bandeja ligera A-07 (21 de octubre de 2026)

El backoffice Django con OTP presenta una bandeja de comentarios y solicitudes sobre el modelo y tabla existentes. Lista remitente, estado, tipo y fecha; ofrece filtros y búsqueda, detalle del mensaje completo, notas internas y cambio de estado. Los conteos de recibidos y pendientes (nuevo o en seguimiento) se calculan desde la base, sin duplicar registros. La verificación de navegador utilizó solo datos sintéticos en una base de prueba aislada. A-07 sigue **EN CURSO** hasta revisión del promotor; no se habilitó acceso público a los mensajes. La referencia de Stripe TEST se registró solo en H6 de [PLAN_TRABAJO.md](PLAN_TRABAJO.md); no existe integración ni enlace en el portal. [Evidencia](VERIFICACION.md).

## Portal de Fase A — cierre local A-07 (21 de octubre de 2026)

El promotor **aprobó y cerró el alcance funcional y visual local de A-07**, incluidos A07-AV01, el formulario público, su persistencia y confirmación, la bandeja administrativa con OTP y la corrección aislada de la prueba de medios A-05 en Windows. La suite completa de 72 pruebas y las comprobaciones de Django, migraciones y diff sustentan el cierre técnico; las evidencias visuales usan datos sintéticos. [Detalle de verificación](VERIFICACION.md). Las secciones anteriores conservan el historial de implementación y revisión.

**Entrega 2 y los hitos superiores siguen abiertos.** O-02, O-04, O-07, O-08 y la validación jurídica permanecen pendientes independientes; este cierre local no acredita correo productivo, base PostgreSQL verificada ni autorización de despliegue. La referencia Stripe TEST permanece únicamente documental.

## Portal de Fase A — A-03 en desarrollo (21 de octubre de 2026)

Se implementó el recorrido J4 para solicitar el lead magnet y autorizar su entrega desde un enlace privado: nombre/correo, consentimiento comercial separado, reutilización del lead, correo de prueba local, enlace de 72 horas, tres accesos máximos, `GET` sin consumo y confirmación por `POST`. Los eventos distinguen visita, lead nuevo, fallo de correo y entrega autorizada. [Verificación](VERIFICACION.md).

**El Excel definitivo `Mapa_de_Caja_PyME_v0.3.xlsx` no se encontró en el proyecto.** La página informa el bloqueo y no acepta solicitudes mientras falte el archivo privado válido. Las pruebas usan un archivo sintético aislado; no prueban entrega del producto real. A-03 y Entrega 2 siguen **EN CURSO** hasta integración del Excel y revisión del promotor. O-02, O-03, O-04, O-07, O-08 y la validación jurídica permanecen pendientes independientes. No se realizó despliegue.

## Portal de Fase A — cierre funcional local A-03 (22 de octubre de 2026)

El promotor **aprobó el alcance funcional local de A-03** después de completar manualmente la descarga del Excel definitivo desde el enlace privado. El archivo permanece en almacenamiento local privado excluido de Git. La corrección CSRF de la página de acceso establece `Referrer-Policy: strict-origin`; se verificó que el POST legítimo funciona y que los orígenes no confiables son rechazados. La última suite Django completa registró **83 pruebas correctas**. No se guardó una captura de la descarga para evitar revelar el enlace privado. [Detalle de verificación](VERIFICACION.md).

**Entrega 2, H2 y H3 permanecen abiertos.** O-02 (PostgreSQL y concurrencia), O-03 (almacenamiento productivo), O-04 (correo real), O-07 (protección compartida), O-08 (medición transversal) y revisión jurídica siguen pendientes independientes. Este cierre local no autoriza despliegue.

## Tienda digital — B-01 en desarrollo (22 de octubre de 2026)

Se implementó el primer incremento del catálogo administrable: modelo de producto digital, edición y vista previa en el backoffice OTP, publicación y retiro, páginas dinámicas `/tienda/` y `/tienda/<slug>/`, navegación y reutilización de imágenes editoriales. Los productos sintéticos de verificación solo existieron en una base de pruebas aislada; la tienda local permanece sin productos comerciales aprobados. La suite Django registró **88 pruebas correctas** y la inspección en Chrome cubrió escritorio y móvil sin desbordamiento. [Evidencia](VERIFICACION.md).

**B-01 sigue EN CURSO** para revisión del promotor y definición del primer producto real, precio, archivo y condiciones comerciales. No se implementaron compra, pago, orden, derecho de descarga ni almacenamiento cloud. H5 y H6 permanecen abiertos; no hay autorización de venta ni despliegue.

## Tienda digital — piloto técnico de Checkout TEST en B-01 (22 de octubre de 2026)

El producto digital admite un Payment Link TEST opcional, editable en el backoffice OTP y validado para HTTPS y la ruta `buy.stripe.com/test_`. Solo una ficha publicada, etiquetada TEST, en desarrollo y con `STORE_TEST_CHECKOUT_ENABLED=1` presenta «Probar compra en Stripe» bajo el precio, junto a la advertencia de pago de prueba sin cargos reales ni entrega. La referencia de $499 proporcionada por el promotor **no se asignó automáticamente** a ningún producto ni al DEMO de $299. La suite Django completa registró **90 pruebas correctas** y la revisión de navegador usó un enlace sintético interceptado, sin contactar Stripe. [Evidencia](VERIFICACION.md).

Es un **piloto técnico de B-01**, no una integración de pagos ni activación comercial. B-01, H5 y H6 siguen abiertos; no hay webhook, orden, derecho de descarga, magic link comercial ni despliegue.

## Tienda digital — cierre funcional y visual local B-01 (22 de octubre de 2026)

El promotor **aprobó el alcance funcional y visual local** del catálogo autoadministrable y del piloto de Checkout TEST. Revisó la tienda y la ficha publicada, y completó un pago simulado del Simulador de Crédito. Una consulta de solo lectura a la base local confirmó una ficha publicada con el producto y precio Stripe TEST indicados y $499.00 MXN; el DEMO de $299 no tiene el mismo enlace. Stripe tiene configurada una redirección a `/tienda/` local después del pago, pero **no se ha confirmado manualmente en navegador la navegación final de retorno**. La última suite Django reportada registró **90 pruebas correctas**. [Evidencia](VERIFICACION.md).

**H5 y H6 siguen abiertos**, junto con B-02–B-08, Checkout Sessions definitivo, webhooks, órdenes, derechos de descarga, correo comercial, almacenamiento privado definitivo y condiciones fiscales, jurídicas y operativas. El cierre local no autoriza ventas LIVE ni despliegue productivo.
