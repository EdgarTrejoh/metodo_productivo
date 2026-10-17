# Plan de trabajo y seguimiento — Método Productivo

**Actualizado:** 17 de octubre de 2026  
**Punto de partida:** bloque local B0 del Check PyME v1.3.  
**Alcance de este plan:** cerrar el Check, completar y publicar la Fase A; preparar las Fases B y C únicamente al superar sus decisiones y gates.

## Cómo usar este documento

- Marcar `[x]` solo cuando la actividad cumpla su criterio de aceptación y exista evidencia revisable.
- Registrar en la [bitácora de avances](#bitácora-de-avances) fecha, ID, responsable, resultado y enlace a evidencia. Una tarea iniciada conserva `[ ]` hasta su cierre.
- Actualizar la tabla de hitos en cada revisión semanal. Estados: **Pendiente**, **En curso**, **Bloqueado** o **Aceptado**.
- Documentar cambios de alcance, responsables y decisiones en el [registro de decisiones](#registro-de-decisiones). No interpretar las estimaciones como fechas comprometidas.

**Fuentes rectoras:** [Concepto y alcance v0.8](producto/concepto_alcance_v08.docx), [BRD v0.6](producto/BRD_Plataforma_Digital_v0_6.docx), [Arquitectura v0.5](arquitectura/arquitectura_v05.docx), [Sitemap y journeys v0.2](experiencia/Sitemap_Journeys_FaseA_v0_2.docx), [Catálogo de acciones v0.1](producto/check-pyme/Catalogo_Acciones_Check_PyME_v0_1.json) y [Propuesta visual v0.2](experiencia/propuesta_visual_portal_metodo_productivo_v0_2.md). El estado técnico actual está en [ESTADO.md](ESTADO.md) y [VERIFICACION.md](VERIFICACION.md).

## Línea base verificada

- [x] Check de ocho preguntas, score, niveles y selección determinista de tres acciones; catálogo de 72 acciones idéntico al JSON aprobado.
- [x] Captura de nombre, correo y empresa, WhatsApp opcional, consentimientos separados y liberación inmediata del resultado y PDF.
- [x] Acceso por contexto de sesión, salida explícita y ausencia de recuperación pública por correo o ID.
- [x] Prueba local: 28 pruebas Django y recorrido completo en Chrome de escritorio y Edge con viewport móvil (17 de octubre de 2026).

**Límite de la línea base:** B0 es un prototipo de desarrollo; `DJANGO_DEBUG=0` está bloqueado. La prueba móvil no se hizo en un dispositivo físico. No se han validado PostgreSQL, despliegue ni operación con datos reales.

## Hitos y seguimiento

Estimación orientativa para una persona de desarrollo a tiempo completo con apoyo parcial de producto, diseño, QA, operación y revisión de privacidad. Los trabajos de infraestructura pueden avanzar en paralelo. La Fase A podría requerir **12–16 semanas de construcción y validación**, más el periodo necesario para medir sus resultados.

| Hito | Entrega | Estimación | Responsable | Estado | Fecha objetivo | Evidencia de aceptación |
| --- | --- | --- | --- | --- | --- | --- |
| H0 | Decisiones y criterios de aceptación cerrados | 1 semana | Por asignar | Pendiente | Por definir | Registro de decisiones y backlog aprobados |
| H1 | Check PyME listo para aceptación funcional | 3–4 semanas | Por asignar | Pendiente | Por definir | Pruebas, PDF final, retención y orientación operativos |
| H2 | Capacidades públicas de Fase A completas | 4–5 semanas | Por asignar | Pendiente | Por definir | Recorridos J4–J8 y backoffice probados |
| H3 | Staging y controles de producción preparados | 3–4 semanas, en paralelo | Por asignar | Pendiente | Por definir | Despliegue, seguridad, monitoreo y restauración probados |
| H4 | Piloto, aceptación y publicación de Fase A | 2 semanas de QA/piloto | Por asignar | Pendiente | Por definir | Acta de aceptación y plan de operación |
| H5 | Gate de resultados de Fase A evaluado | Según tráfico real | Por asignar | Pendiente | Por definir | Reporte de métricas y decisión documentada |
| H6 | Fase B: recursos de pago | Estimar tras H5 | Por asignar | Pendiente | Por definir | Gate B y pruebas de compra/entrega |
| H7 | Fase C: servicios y eventos | Estimar tras H6 | Por asignar | Pendiente | Por definir | Gate C y pruebas de agenda/eventos |

## H0 — Decisiones previas y backlog

**Cierre:** cada decisión tiene responsable, versión, criterio de aceptación y aprobación registrada. Los pendientes exclusivos de B/C no bloquean la construcción de A.

- [ ] **D-01** Aprobar contenido, orden, diseño y disclaimer del PDF del Check; definir qué respuestas textuales incluir.
- [ ] **D-02** Definir duración e invalidación del contexto activo: recarga, historial, otra pestaña, cierre de pestaña y abandono; documentar límites técnicos de RF-A17.
- [ ] **D-03** Definir qué hecho medible constituye `PDF_DOWNLOADED`, cómo distinguir reintentos y qué hacer cuando no puede confirmarse la entrega completa.
- [ ] **D-04** Seleccionar y aprobar la primera calculadora, entradas, fórmula, mensajes y casos límite.
- [ ] **D-05** Seleccionar y aprobar el primer lead magnet, archivo, política de acceso y contenido del correo.
- [ ] **D-06** Aprobar textos de servicio, privacidad y consentimiento comercial mediante la revisión correspondiente; decidir preferencias y baja.
- [ ] **D-07** Designar responsable, canal, horario y plazo de respuesta para orientación; acordar qué información adicional podrá escribir la persona solicitante.
- [ ] **D-08** Definir fuente, exclusiones, deduplicación y periodo de medición de la sesión calificada y del gate de Fase A.
- [ ] **D-09** Designar responsable editorial del catálogo y proceso de versionado/aprobación de cambios.
- [ ] **D-10** Convertir estas decisiones en historias priorizadas, dependencias y casos de aceptación trazables a RF-A01–RF-A17.

## H1 — Cierre del Check PyME (B1)

**Dependencias:** D-01, D-02, D-03, D-06 y D-07.  
**Cierre:** el recorrido J1/J3 cumple sus criterios en PostgreSQL, navegador real y dispositivos previstos, con fallos recuperables y datos sujetos a la política de retención.

### Acceso, resultado y PDF

- [ ] **C-01** Implementar y probar la regla aprobada de contexto activo, vencimiento, salida e invalidación; comprobar historial, enlaces directos y pestañas múltiples.
- [ ] **C-02** Mantener el resultado inaccesible antes de la captura y después de salir; evitar caché del contenido sensible y conservar reintentos autorizados.
- [ ] **C-03** Finalizar el PDF editorial, su contenido versionado y la igualdad de hallazgos/acciones con el resultado en pantalla.
- [ ] **C-04** Ante fallo de PDF, conservar el resultado, mostrar mensaje y reintento, registrar `ERROR_OPERATIONAL` y evitar diagnósticos duplicados.
- [ ] **C-05** Implementar la medición de descarga aprobada en D-03 sin equiparar una respuesta generada con un archivo guardado por la persona.

### Datos, consentimiento y orientación

- [ ] **C-06** Sustituir textos de prueba por los textos aprobados; conservar versión, fecha y evidencia técnica del consentimiento por finalidad.
- [ ] **C-07** Implementar eliminación o anonimización de contacto, respuestas y resultado al cumplir 12 meses; resolver leads compartidos, consentimientos y copias de respaldo conforme a la política aprobada.
- [ ] **C-08** Crear una tarea programada de retención con registro de ejecución, errores y prueba de reejecución segura.
- [ ] **C-09** Completar solicitud de orientación con los datos capturados y, si se aprueba, una descripción opcional de la necesidad; mantenerla separada del consentimiento comercial.
- [ ] **C-10** Notificar internamente la solicitud; registrar éxito/fallo del correo y asegurar que el backoffice permita seguimiento `nuevo → contactado → cerrado`.
- [ ] **C-11** Revisar el modelo de Lead y contacto capturado frente a los datos mínimos del BRD, preservando el snapshot inmutable de cada diagnóstico.

### Verificación del Check

- [ ] **C-12** Probar persistencia, doble envío e idempotencia con PostgreSQL y solicitudes concurrentes.
- [ ] **C-13** Añadir pruebas de fallos de PDF, correo, caducidad, retención y aislamiento entre sesiones; conservar la prueba de las 6,561 combinaciones.
- [ ] **C-14** Probar el recorrido en Chrome y Edge, al menos un dispositivo móvil físico y teclado; registrar defectos y evidencias.
- [ ] **C-15** Hacer prueba de comprensión de las ocho preguntas con 5–10 PyMEs; versionar cualquier cambio de redacción como una nueva versión del Check.

## H2 — Capacidades públicas de Fase A

**Dependencias:** D-04, D-05 y diseño/contenido aprobados.  
**Cierre:** los recorridos públicos del sitemap funcionan sin cuenta, producen los eventos acordados y pueden operarse desde el backoffice.

- [ ] **A-01** Implementar design system y Home responsiva: logo, tipografías, navegación, CTA, secciones editoriales y pie con enlaces legales; medir clics principales.
- [ ] **A-02** Publicar una calculadora independiente sin captura de datos personales, con validación, resultado servido por Django y funcionamiento sin JavaScript.
- [ ] **A-03** Implementar lead magnet: captura y consentimientos propios, deduplicación por correo, entrega por correo y acceso controlado por propósito; un GET no consume el enlace.
- [ ] **A-04** Implementar preferencias y baja de comunicaciones comerciales sin afectar mensajes necesarios del servicio.
- [ ] **A-05** Crear blog con listado, detalle, slug, fecha, categoría, metadatos SEO, CTA contextual y administración editorial.
- [ ] **A-06** Incorporar videos destacados mediante proveedor externo, sin almacenar el video pesado en la aplicación.
- [ ] **A-07** Implementar contacto/comentarios categorizados, confirmación, estado interno y notificación a operación.
- [ ] **A-08** Publicar páginas Acerca de, Privacidad y Términos con textos aprobados y enlaces desde formularios y pie.
- [ ] **A-09** Ampliar backoffice para artículos, recursos, testimoniales, leads, solicitudes y métricas; registrar acciones administrativas sensibles.
- [ ] **A-10** Crear sitemap, robots, canonical, OpenGraph y páginas 404/500 útiles; revisar indexación prevista en el sitemap.

## H3 — Infraestructura, seguridad y operación de Fase A

**Cierre:** staging reproduce la configuración objetivo; un despliegue y una restauración se pueden repetir siguiendo runbooks, sin datos de producción en pruebas.

- [ ] **O-01** Preparar ambientes local, staging y producción con configuración separada; habilitar `DEBUG=0` solo después de completar los controles de publicación.
- [ ] **O-02** Desplegar monolito Django en Cloud Run y PostgreSQL en Cloud SQL; verificar migraciones, transacciones, concurrencia y conexión.
- [ ] **O-03** Configurar almacenamiento privado de archivos/PDF y metadatos necesarios; impedir rutas permanentes públicas.
- [ ] **O-04** Integrar proveedor de correo transaccional, estados de envío y error; configurar dominio y entregabilidad antes de publicar.
- [ ] **O-05** Guardar secretos fuera del código; configurar HTTPS, hosts, cookies seguras y permisos mínimos.
- [ ] **O-06** Completar enrolamiento y runbook de MFA del backoffice; limitar acceso al personal autorizado.
- [ ] **O-07** Añadir límite de solicitudes compartido en formularios y endpoints sensibles, y CAPTCHA donde el riesgo lo justifique; probar varias instancias.
- [ ] **O-08** Implementar eventos de página, CTA, herramientas, Check, formularios, correo y errores; excluir tráfico interno/bots y evitar datos sensibles innecesarios.
- [ ] **O-09** Construir reporte del gate: sesiones calificadas, conversión visitante→lead, finalización, diagnósticos y orientación, con periodo y definiciones documentados.
- [ ] **O-10** Configurar logs con ID de solicitud, alertas de errores e integraciones, health check y tablero de operación.
- [ ] **O-11** Automatizar backups y realizar una restauración en entorno aislado; documentar responsables y tiempos de recuperación.
- [ ] **O-12** Ampliar CI/CD: formato/lint, pruebas, análisis de dependencias, build, despliegue a staging, smoke test y promoción manual.

## H4 — QA, piloto y salida productiva de Fase A

**Dependencias:** H1, H2 y H3 aceptados.  
**Cierre:** aprobación conjunta de producto, operación, QA y revisión de privacidad; sin defectos críticos abiertos ni incidentes graves de datos o seguridad.

- [ ] **R-01** Ejecutar pruebas de extremo a extremo de J1 y J3–J9, incluidos envíos duplicados, correo fallido, PDF fallido, expiración y recuperación operativa.
- [ ] **R-02** Revisar formularios, teclado, foco, contraste y mensajes frente al objetivo WCAG 2.2 AA; corregir hallazgos priorizados.
- [ ] **R-03** Medir y ajustar rendimiento y experiencia móvil/desktop; verificar Core Web Vitals en condiciones razonables.
- [ ] **R-04** Probar cargas y límites de abuso esperados, concurrencia de datos, backups y restauración.
- [ ] **R-05** Validar textos, consentimiento, retención, aviso de privacidad y operación del correo antes de usar datos reales.
- [ ] **R-06** Ejecutar piloto controlado, registrar observaciones y resolver problemas de comprensión o conversión sin alterar silenciosamente el Check versionado.
- [ ] **R-07** Preparar checklist de publicación, responsables de incidentes, rollback, monitoreo inicial y acta de aceptación.
- [ ] **R-08** Publicar Fase A y comprobar rutas, eventos, entregas y alertas con tráfico controlado.

## H5 — Medición y decisión de avanzar a Fase B

**Cierre:** reporte con periodo, fuentes, exclusiones, resultados y decisión explícita: avanzar, iterar A o ampliar muestra. Los umbrales del BRD son hipótesis iniciales, no promesas comerciales.

- [ ] **M-01** Confirmar al menos 500 sesiones calificadas acumuladas, excluyendo bots y tráfico interno/de prueba.
- [ ] **M-02** Medir conversión visitante→lead y contrastarla con la referencia de 5 %.
- [ ] **M-03** Medir finalización del Check entre quienes lo inician y contrastarla con 40 %.
- [ ] **M-04** Confirmar al menos 15 diagnósticos liberados y 3 solicitudes de orientación.
- [ ] **M-05** Revisar errores, entregabilidad, privacidad y seguridad; confirmar ausencia de incidentes graves.
- [ ] **M-06** Documentar la decisión de producto y actualizar backlog y estimación de B.

## H6 — Fase B: monetización digital (condicionada a H5)

**Antes de construir:** aprobar catálogo/precios, operación fiscal, políticas de reembolso y soporte. La compra usa correo capturado en Checkout; el Check mantiene su propio recorrido sin magic link.

- [ ] **B-01** Definir productos, versiones, precios, términos de venta, soporte y criterios de entrega.
- [ ] **B-02** Diseñar orden, pago, derecho de entrega, descarga, magic link y auditoría; usar un entorno de pruebas de pagos separado del modo real.
- [ ] **B-03** Integrar Stripe Checkout Sessions para pago único y confirmar el pago en el servidor mediante webhook validado e idempotente; nunca liberar por la página de retorno.
- [ ] **B-04** Enviar acceso por correo al comprador tras pago confirmado; GET del enlace no consume uso ni descarga.
- [ ] **B-05** Aplicar vigencia de 14 días desde pago y máximo de tres **descargas exitosas** por derecho, compartidas entre enlaces reemitidos; probar fallos y concurrencia.
- [ ] **B-06** Implementar reemisión sin reiniciar límites y excepciones de soporte documentadas y auditadas.
- [ ] **B-07** Implementar solicitud y seguimiento de factura manual asistida, sin almacenar ni distribuir XML/PDF de CFDI en la plataforma.
- [ ] **B-08** Probar pagos exitosos, pendientes/fallidos, webhooks repetidos, conciliación, recuperación y entrega; medir el gate B del BRD.

## H7 — Fase C: servicios y eventos (condicionada a H6)

- [ ] **F-01** Aprobar servicios, duración, precios, cupos, cancelación, reprogramación, reembolsos y vencimiento de reservas temporales.
- [ ] **F-02** Implementar disponibilidad, bloqueo temporal, caducidad y prevención de dobles reservas.
- [ ] **F-03** Integrar pago y confirmación de cita/evento; usar Google Calendar como integración operativa, con la base interna como fuente de verdad.
- [ ] **F-04** Implementar acceso por propósito para gestionar citas e inscripciones, sin cuentas públicas.
- [ ] **F-05** Implementar recordatorios y seguimiento de errores y cambios de agenda.
- [ ] **F-06** Probar concurrencia, zonas horarias, fallos de pago/Calendar, cambios y cancelaciones; medir el gate C del BRD.

## Registro de decisiones

| ID | Asunto y decisión | Responsable | Fecha | Documento/versión y evidencia |
| --- | --- | --- | --- | --- |
| D-01…D-10 | Pendiente | Por asignar | — | — |

## Bitácora de avances

Añadir una fila por avance relevante, bloqueo o aceptación. Usar el ID de la casilla correspondiente.

| Fecha | ID | Responsable | Avance o bloqueo | Evidencia / enlace | Próximo paso |
| --- | --- | --- | --- | --- | --- |
| 2026-10-17 | B0 | Equipo técnico | Línea base verificada: 28 pruebas Django y recorrido Chrome/Edge | [VERIFICACION.md](VERIFICACION.md) | Cerrar H0 |

## Regla común de terminado

Una actividad se marca `[x]` cuando tiene: implementación o decisión aprobada, prueba adecuada al riesgo, evidencia enlazada, documentación operativa actualizada y responsable de operación definido. Para publicar, además debe pasar en staging y no mantener defectos críticos abiertos.
