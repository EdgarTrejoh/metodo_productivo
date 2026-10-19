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
