# Plan de trabajo y seguimiento — Método Productivo

**Actualizado:** 17 de octubre de 2026  
**Punto de partida:** bloque local B0 del Check PyME v1.3 y estructura pública del portal pendiente.

**Alcance de este plan:** construir y publicar la plataforma integral de Fase A —contenidos, educación financiera, herramientas, captación y orientación—, completar el Check como componente diferenciador y preparar las Fases B y C únicamente al superar sus decisiones y gates.

## Cómo usar este documento

- Marcar `[x]` solo cuando la actividad cumpla su criterio de aceptación y exista evidencia revisable.
- Registrar en la [bitácora de avances](#bitácora-de-avances) fecha, ID, responsable, resultado y enlace a evidencia. Una tarea iniciada conserva `[ ]` hasta su cierre.
- Actualizar la tabla de hitos en cada revisión semanal. Estados: **Pendiente**, **En curso**, **Bloqueado** o **Aceptado**.
- Documentar cambios de alcance, responsables y decisiones en el [registro de decisiones](#registro-de-decisiones). No interpretar las estimaciones como fechas comprometidas.

**Fuentes rectoras:** [Concepto y alcance v0.8](producto/concepto_alcance_v08.docx), [BRD v0.6](producto/BRD_Plataforma_Digital_v0_6.docx), [Arquitectura v0.5](arquitectura/arquitectura_v05.docx), [Sitemap y journeys v0.2](experiencia/Sitemap_Journeys_FaseA_v0_2.docx), [Catálogo de acciones v0.1](producto/check-pyme/Catalogo_Acciones_Check_PyME_v0_1.json) y [Propuesta visual v0.2](experiencia/propuesta_visual_portal_metodo_productivo_v0_2.md). El estado técnico actual está en [ESTADO.md](ESTADO.md) y [VERIFICACION.md](VERIFICACION.md).

Las precisiones funcionales aprobadas en D-01–D-09 rigen cuando un documento visual o de recorridos anterior todavía presenta una cuestión como propuesta o pendiente. No se modifican esas fuentes en este reenfoque.

## Línea base verificada

- [x] Check de ocho preguntas, score, niveles y selección determinista de tres acciones; catálogo de 72 acciones idéntico al JSON aprobado.
- [x] Captura de nombre, correo y empresa, WhatsApp opcional, consentimientos separados y liberación inmediata del resultado y PDF.
- [x] Acceso por contexto de sesión, salida explícita y ausencia de recuperación pública por correo o ID.
- [x] Prueba local: 28 pruebas Django y recorrido completo en Chrome de escritorio y Edge con viewport móvil (17 de octubre de 2026).

**Límite de la línea base:** B0 es un prototipo de desarrollo; `DJANGO_DEBUG=0` está bloqueado. La prueba móvil no se hizo en un dispositivo físico. No se han validado PostgreSQL, despliegue ni operación con datos reales.

## Hitos y seguimiento

Estimación orientativa para una persona de desarrollo a tiempo completo con apoyo parcial de producto, diseño, QA, operación y revisión de privacidad. Los trabajos de H1, H2 y H3 pueden coordinarse en paralelo cuando sus dependencias reales lo permitan. La Fase A podría requerir **12–16 semanas de construcción y validación**, más el periodo necesario para medir sus resultados. El reenfoque puede afectar la distribución del esfuerzo y el calendario; se revisará con capacidad y alcance de cada incremento antes de cambiar estas estimaciones.

| Hito | Entrega | Estimación | Responsable | Estado | Fecha objetivo | Evidencia de aceptación |
| --- | --- | --- | --- | --- | --- | --- |
| H0 | Decisiones y criterios de aceptación cerrados | 1 semana | Por asignar | En curso | Por definir | Registro de decisiones y backlog aprobados |
| H1 | Check PyME listo para aceptación funcional | 3–4 semanas | Por asignar | Pendiente | Por definir | Pruebas, PDF final, retención y orientación operativos |
| H2 | Capacidades públicas de Fase A completas | 4–5 semanas | Por asignar | Pendiente | Por definir | Recorridos J4–J8 y backoffice probados |
| H3 | Staging y controles de producción preparados | 3–4 semanas, en paralelo | Por asignar | Pendiente | Por definir | Despliegue, seguridad, monitoreo y restauración probados |
| H4 | Piloto, aceptación y publicación de Fase A | 2 semanas de QA/piloto | Por asignar | Pendiente | Por definir | Acta de aceptación y plan de operación |
| H5 | Gate de resultados de Fase A evaluado | Según tráfico real | Por asignar | Pendiente | Por definir | Reporte de métricas y decisión documentada |
| H6 | Fase B: recursos de pago | Estimar tras H5 | Por asignar | Pendiente | Por definir | Gate B y pruebas de compra/entrega |
| H7 | Fase C: servicios y eventos | Estimar tras H6 | Por asignar | Pendiente | Por definir | Gate C y pruebas de agenda/eventos |

## H0 — Decisiones previas y backlog

**Cierre:** cada decisión tiene responsable, versión, criterio de aceptación y aprobación registrada. Los pendientes exclusivos de B/C no bloquean la construcción de A.

- [x] **D-01** Aprobar contenido, orden, diseño y disclaimer editorial del PDF del Check; definir qué respuestas textuales incluir. [Decisión aprobada](decisiones/D-01_PDF_CHECK.md). La revisión jurídica del aviso permanece en D-06.
- [x] **D-02** Definir duración e invalidación del contexto activo: recarga, historial, otra pestaña, cierre de pestaña y abandono; documentar límites técnicos de RF-A17. [Decisión aprobada](decisiones/D-02_CONTEXTO_ACTIVO_CHECK.md).
- [x] **D-03** Definir qué hecho medible constituye `PDF_DOWNLOADED`, cómo distinguir reintentos y qué hacer cuando no puede confirmarse la entrega completa. [Decisión aprobada](decisiones/D-03_MEDICION_DESCARGA_PDF.md). C-05 permanece sin iniciar.
- [x] **D-04** Aprobado el demostrador web gratuito, sus entradas, fórmula, mensajes y casos límite; se preserva la futura tienda de herramientas Excel de pago en Fase B. [Decisión aprobada](decisiones/D-04_CALCULADORA_PUNTO_EQUILIBRIO.md). La implementación funcional y visual de A-02 fue aceptada con salvedades; el ID continúa en curso por O-08.
- [x] **D-05** Aprobada la plantilla Excel gratuita de flujo de efectivo de 13 semanas como primer lead magnet, su política de acceso y el alcance funcional del correo transaccional. [Decisión aprobada](decisiones/D-05_PRIMER_LEAD_MAGNET.md). A-03 permanece pendiente de implementación y verificación; el Excel definitivo se proporcionará externamente durante A-03.
- [x] **D-06** Aprobado el alcance funcional de los textos de servicio, privacidad y consentimiento comercial, preferencias y baja. [Decisión funcional aprobada](decisiones/D-06_TEXTOS_PRIVACIDAD_CONSENTIMIENTOS.md). Antes de producción siguen pendientes datos reales del responsable, avisos definitivos, canales ARCO, revisión jurídica y validación de retenciones; implementación y verificación no iniciadas.
- [x] **D-07** Aprobado el flujo funcional de orientación: botón sin campo adicional, una solicitud abierta por diagnóstico, seguimiento básico y correo principal con WhatsApp alternativo autorizado. [Decisión funcional aprobada](decisiones/D-07_OPERACION_ORIENTACION.md). C-09 y C-10 pendientes; responsable concreto, horario y objetivo de primera respuesta se configurarán antes de habilitar atención pública.
- [x] **D-08** Aprobadas fuente, exclusiones, deduplicación, inicio y corte de medición del gate de Fase A, con tasa de captación de leads por sesión calificada. [Decisión aprobada](decisiones/D-08_MEDICION_GATE_FASE_A.md). O-08 y O-09 siguen sin implementar ni verificar; H5 no se ha evaluado.
- [x] **D-09** Aprobado el gobierno editorial del catálogo: promotor responsable y autoridad de aprobación, trazabilidad en GitHub y revisión versionada de cambios publicados. [Decisión aprobada](decisiones/D-09_GOBIERNO_CATALOGO_ACCIONES.md). El catálogo v0.1 y la selección v0.1 permanecen intactos; C-03, C-13 y C-15 no se cierran por esta decisión.
- [x] **D-10** Aprobadas historias y aceptación trazables a RF-A01–RF-A17, prioridad transversal de A-01, cuatro entregas incrementales y coordinación de H1/H2/H3. [Decisión aprobada](decisiones/D-10_BACKLOG_TRAZABILIDAD.md). A-01 inicia por la Entrega 1 y permanece en curso.

## Estrategia de ejecución transversal aprobada

Los hitos H1, H2 y H3 **conservan sus resultados y criterios de cierre**, pero no son una cola obligatoria. Se coordinan por dependencias verificables y pueden avanzar en paralelo. El Check B0 se incorpora al recorrido público sin esperar a que H1 esté cerrado; la finalización de H1 no es requisito general para comenzar H2. El orden de ejecución podrá revisarse con justificación de producto registrada en esta bitácora, manteniendo requisitos, decisiones aprobadas y controles de publicación. [D-10](decisiones/D-10_BACKLOG_TRAZABILIDAD.md) aprueba esta secuencia y su trazabilidad.

Las siguientes **entregas son cortes incrementales del plan vigente**, no fases comerciales nuevas. Un ID puede aportar a varios cortes y permanece abierto hasta cumplir todos sus criterios de aceptación. **Entrega 1: APROBADA CON SALVEDADES por el promotor el 17 de octubre de 2026.** A-01 sigue EN CURSO; H2 conserva su aceptación integral pendiente. **Entrega 2: EN CURSO desde el 19 de octubre de 2026 con A-02**, sin aceptación integral. Entregas 3–4 no iniciadas.

| Corte | Resultado visible y verificable | IDs vinculados | Evidencia de revisión |
| --- | --- | --- | --- |
| **Entrega 1 — Estructura integral navegable** | Home, encabezado, navegación, pie, identidad visual, diseño responsivo y estructura de las secciones públicas de Fase A, recorribles en desarrollo. Contenido provisional identificado; funciones pendientes no aparentan estar operativas. | A-01 como prioridad inicial; estructura de A-02, A-03, A-05, A-07 y A-08 sin cerrar esos IDs; integración de la entrada al Check B0 | Recorrido de rutas y enlaces, capturas móvil/escritorio, teclado/foco y lista de contenidos y funciones pendientes. |
| **Entrega 2 — Capacidades funcionales** | Calculadora, lead magnet, blog, videos, contacto y Check PyME se completan por recorridos con resultados reales. | A-02, A-03, A-05–A-07 y C-01–C-15, según dependencia | Pruebas funcionales y de error por recorrido; evidencia de las decisiones aplicables. |
| **Entrega 3 — Integración y operación** | Formularios, correo, backoffice, analítica, almacenamiento y controles compartidos integrados con los recorridos. | A-04, A-09, C-06–C-10 y O-02–O-09, según aplicación | Pruebas de integración, estados de entrega/error, acceso autorizado y registros operativos. |
| **Entrega 4 — Verificación y publicación** | Staging, seguridad, restauración, QA, piloto y publicación; evaluación del gate tras tráfico público. | H3, H4 y H5 con sus tareas O, R y M | Evidencias de H3, aceptación H4 y reporte/decisión H5. |

### Primera entrega: alcance y aceptación

**Cierre visual autorizado:** el promotor aprobó con salvedades la estructura integral navegable tras tres rondas AV-01–AV-29. AV-24–AV-29 quedaron resueltos con evidencia de entrada compacta al Check, navegación «Contenidos», posicionamiento de marca, revisión móvil, encabezado compartido y breadcrumbs accesibles. La aceptación cubre la estructura pública en desarrollo, identidad oficial, Home, navegación, páginas interiores responsivas e integración del acceso al Check B0; no acredita funciones futuras ni aceptación integral de H2.

**Salvedades registradas:** (1) favicon oficial pendiente; (2) instrumentación y verificación de clics principales de A-01 pendientes; (3) prueba en dispositivo móvil físico pendiente de la actividad de verificación correspondiente. El contenido provisional y las funciones futuras continúan en su backlog y no bloquean este cierre estructural.

- La Home comunica el conjunto de contenidos, educación financiera, herramientas y orientación asociada al Check, conforme al BRD, el sitemap y la propuesta visual. No se presenta el portal como un único cuestionario.
- En desarrollo, desde la Home se recorre la entrada al Check, herramientas, recurso gratuito, blog, contacto y páginas institucionales y legales previstas para Fase A. Encabezado y pie ofrecen enlaces coherentes; las rutas privadas o de propósito específico no se anuncian como páginas públicas.
- La identidad, componentes base y diseño responsivo funcionan en móvil y escritorio. El recorrido básico se puede completar con teclado, con foco visible y sin enlaces rotos.
- Todo texto de ejemplo se identifica como provisional. No se publican páginas vacías, testimonios inventados, formularios ficticios ni llamadas a acciones que aparenten una función disponible. Las páginas legales provisionales no se publican hasta cumplir D-06 y R-05.
- El recorrido, capturas de móvil y escritorio, comprobación de enlaces y teclado, y la lista de funciones pendientes sustentan esta aceptación con salvedades. A-01 solo se cierra al cumplir su alcance completo, incluida la medición de clics principales; la aceptación de Entrega 1 no cierra A-02, A-03, A-05, A-07, A-08 ni H2.

### Secuencia ejecutable y dependencias

| Orden inicial aprobado | Actividades e IDs | Dependencia indispensable / paralelismo | Condición y evidencia del siguiente corte |
| --- | --- | --- | --- |
| **Inicio inmediato** | A-01: identidad, componentes, Home, navegación y estructura responsiva; aprovechar la entrada existente del Check B0. | BRD, sitemap y propuesta visual vigentes. No requiere cerrar H1, correo, pagos ni entorno productivo. | Entrega 1 navegable en desarrollo, con capturas, revisión de enlaces y pendientes visibles. |
| **Paralelo al inicio** | Preparar historias de A-02, A-05, A-06, A-07 y C-01–C-04; revisar interfaces necesarias de O-02/O-08. | D-01–D-10 definen lo correspondiente; la implementación de esas funciones requiere una autorización posterior y su dependencia concreta. | Criterios y pruebas por historia; ninguna preparación documental equivale a implementación. |
| **Funciones por recorrido** | A-02; A-05/A-06; A-07; avance de C-01–C-15; preparación de A-03 y entrega real al recibir el Excel definitivo. | D-04 para calculadora; D-05 y archivo externo para entrega real del lead magnet; D-02/D-03/D-06/D-07 para Check. Blog, video y contacto pueden avanzar mientras se cierra H1. | Resultados funcionales, errores y accesibilidad verificados por recorrido; IDs abiertos hasta aceptación completa. |
| **Integración paralela** | A-04/A-09 y O-02–O-09, C-06–C-10 según función. | PostgreSQL para pruebas persistentes; correo para entregas/notificaciones; almacenamiento privado para archivos/PDF; MFA para backoffice; analítica conforme a D-08. | Evidencia de integración y seguridad; fallos y estados operativos visibles. |
| **Condicionado antes de publicar** | Publicación legal de A-08, R-05 y requisitos jurídicos de D-06; configuración de atención de D-07; resto de H3/H4. | Textos legales definitivos, datos del responsable, canales ARCO, revisión jurídica y retenciones validadas; responsable, horario y primera respuesta de orientación; controles de staging y publicación. | H1–H3 aceptados y H4 verificado antes de R-08; H5 solo tras liberación pública e instrumentación comprobada. |

**Bloqueos acotados:** la falta del Excel definitivo bloquea la entrega funcional de A-03, no la navegación del portal; los textos y datos jurídicos pendientes bloquean publicación legal, no el diseño de páginas; la configuración de orientación bloquea habilitar atención pública, no registrar su historia. Las dependencias de correo, almacenamiento, PostgreSQL y MFA se atienden antes de aceptar los recorridos que las usan, sin detener A-01. No se anticipan pagos, agenda ni servicios de Fases B/C.

## H1 — Cierre del Check PyME (B1)

**Dependencias para cerrar H1:** D-01, D-02, D-03, D-06 y D-07. Sus trabajos pueden avanzar en paralelo a A-01 y otros componentes de H2.

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
- [ ] **C-09** Completar solicitud de orientación con el botón aprobado en D-07, sin campo de descripción ni nueva captura; reutilizar los datos existentes, permitir una sola solicitud abierta por diagnóstico y mantenerla separada del consentimiento comercial.
- [ ] **C-10** Notificar internamente la solicitud; registrar éxito/fallo del correo y asegurar que el backoffice permita seguimiento `nuevo → contactado → cerrado`.
- [ ] **C-11** Revisar el modelo de Lead y contacto capturado frente a los datos mínimos del BRD, preservando el snapshot inmutable de cada diagnóstico.

### Verificación del Check

- [ ] **C-12** Probar persistencia, doble envío e idempotencia con PostgreSQL y solicitudes concurrentes.
- [ ] **C-13** Añadir pruebas de fallos de PDF, correo, caducidad, retención y aislamiento entre sesiones; conservar la prueba de las 6,561 combinaciones.
- [ ] **C-14** Probar el recorrido en Chrome y Edge, al menos un dispositivo móvil físico y teclado; registrar defectos y evidencias.
- [ ] **C-15** Hacer prueba de comprensión de las ocho preguntas con 5–10 PyMEs; versionar cualquier cambio de redacción como una nueva versión del Check.

## H2 — Capacidades públicas de Fase A

**Dependencias para cerrar H2:** D-04, D-05 y diseño/contenido aprobados para las funciones respectivas. A-01 puede iniciar de inmediato con las fuentes visuales y de navegación vigentes; H1 completo no es condición para empezar H2.

**Cierre:** los recorridos públicos del sitemap funcionan sin cuenta, producen los eventos acordados y pueden operarse desde el backoffice.

- [ ] **A-01 — EN CURSO** Implementar design system y Home responsiva: logo, tipografías, navegación, CTA, secciones editoriales y pie con enlaces legales; medir clics principales. **Prioridad inicial transversal:** construir primero la estructura navegable de las secciones públicas de Fase A como incremento verificable, sin marcar A-01 como terminado antes de cumplir su alcance completo.
- [ ] **A-02 — EN CURSO; implementación funcional y visual APROBADA CON SALVEDADES** Calculadora de D-04 sin captura de datos personales, con validación, resultado servido por Django y funcionamiento sin JavaScript. El promotor aceptó la implementación y los ajustes A02-AV01–AV08 el 19 de octubre de 2026. AV-06 conserva la limitación aceptada de F5: el navegador puede reenviar el POST; la aplicación deduplica eventos y vuelve a GET vacío, sin persistir importes ni exigir JavaScript. Falta integrar y verificar la medición transversal O-08 antes de cerrar el ID. Entrega 2 permanece EN CURSO.
- [ ] **A-03** Implementar el lead magnet aprobado en D-05: integrar el Excel definitivo proporcionado externamente durante A-03, con captura y consentimientos propios, deduplicación por correo, entrega por correo y acceso controlado por propósito; un GET no consume el enlace. Pendiente de implementación y verificación.
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
- [ ] **O-09** Construir reporte del gate: sesiones calificadas, tasa de captación de leads por sesión calificada, finalización, diagnósticos y orientación, con periodo y definiciones aprobados en D-08. Pendiente de implementación y verificación.
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
- [ ] **M-02** Medir la tasa de captación de leads por sesión calificada y contrastarla con la referencia inicial de 5 %, con las limitaciones de atribución documentadas en D-08.
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
| D-01 | Aprobado el contenido y diseño del PDF, incluidas las ocho respuestas textuales; revisión jurídica del aviso en D-06 | Promotor del proyecto | 2026-10-17 | [D-01_PDF_CHECK.md](decisiones/D-01_PDF_CHECK.md); aprobación expresa en la conversación |
| D-02 | Aprobados 30 minutos de inactividad y 2 horas absolutas; reglas de recarga, salida, pestañas y límite de detección del cierre | Promotor del proyecto | 2026-10-17 | [D-02_CONTEXTO_ACTIVO_CHECK.md](decisiones/D-02_CONTEXTO_ACTIVO_CHECK.md); aprobación expresa en la conversación |
| D-03 | Aprobada la entrega reportada por el cliente mediante acuse válido; intentos y diagnósticos únicos separados; ventana de espera pendiente de definición técnica en C-05 | Promotor del proyecto | 2026-10-17 | [D-03_MEDICION_DESCARGA_PDF.md](decisiones/D-03_MEDICION_DESCARGA_PDF.md); autorización expresa en la revisión documental |
| D-04 | Aprobado el demostrador web gratuito de punto de equilibrio para Fase A; A-02 no implementado ni verificado; lead magnet y tienda Excel conservan decisiones propias | Promotor del proyecto | 2026-10-17 | [D-04_CALCULADORA_PUNTO_EQUILIBRIO.md](decisiones/D-04_CALCULADORA_PUNTO_EQUILIBRIO.md); autorización expresa en la conversación |
| D-05 | Aprobada la plantilla Excel gratuita de flujo de efectivo de 13 semanas; 3 días y 3 accesos autorizados por enlace; correo transaccional sin invitación al Check. A-03 pendiente y Excel definitivo de provisión externa | Promotor del proyecto | 2026-10-17 | [D-05_PRIMER_LEAD_MAGNET.md](decisiones/D-05_PRIMER_LEAD_MAGNET.md); autorización expresa en la conversación |
| D-06 | Aprobado el alcance funcional de finalidades, textos, consentimiento comercial opcional, preferencias y baja; pendiente validación jurídica y datos reales antes de publicación | Promotor del proyecto | 2026-10-17 | [D-06_TEXTOS_PRIVACIDAD_CONSENTIMIENTOS.md](decisiones/D-06_TEXTOS_PRIVACIDAD_CONSENTIMIENTOS.md); autorización expresa en la conversación |
| D-07 | Aprobado el flujo funcional de orientación sin descripción adicional ni agrupación por 24 horas; correo principal, WhatsApp alternativo autorizado y una solicitud abierta por diagnóstico; operación pública sujeta a configuración de responsable, horario y primera respuesta | Promotor del proyecto | 2026-10-17 | [D-07_OPERACION_ORIENTACION.md](decisiones/D-07_OPERACION_ORIENTACION.md); autorización expresa en la conversación |
| D-08 | Aprobada la medición desde liberación pública instrumentada, corte acumulado al alcanzar 500 sesiones calificadas, tasa de leads únicos por sesión calificada y exclusiones documentadas; H5 exige decisión expresa | Promotor del proyecto | 2026-10-17 | [D-08_MEDICION_GATE_FASE_A.md](decisiones/D-08_MEDICION_GATE_FASE_A.md); autorización expresa en la conversación |
| D-09 | Aprobado el gobierno editorial: promotor responsable y aprobador de nuevas versiones del catálogo y la selección; registro en GitHub y correcciones de borradores separadas de cambios publicados | Promotor del proyecto | 2026-10-17 | [D-09_GOBIERNO_CATALOGO_ACCIONES.md](decisiones/D-09_GOBIERNO_CATALOGO_ACCIONES.md); autorización expresa en la conversación |
| D-10 | Aprobada: prioridad transversal A-01, cuatro entregas incrementales, ejecución coordinada de H1/H2/H3 y trazabilidad RF-A01–RF-A17; desarrollo autorizado solo para Entrega 1 de A-01 | Promotor del proyecto | 2026-10-17 | [D-10_BACKLOG_TRAZABILIDAD.md](decisiones/D-10_BACKLOG_TRAZABILIDAD.md); autorización expresa en la conversación |

## Bitácora de avances

Añadir una fila por avance relevante, bloqueo o aceptación. Usar el ID de la casilla correspondiente.

| Fecha | ID | Responsable | Avance o bloqueo | Evidencia / enlace | Próximo paso |
| --- | --- | --- | --- | --- | --- |
| 2026-10-17 | B0 | Equipo técnico | Línea base verificada: 28 pruebas Django y recorrido Chrome/Edge | [VERIFICACION.md](VERIFICACION.md) | Cerrar H0 |
| 2026-10-17 | D-01 | Promotor del proyecto | Aprobó contenido, orden, diseño y ocho respuestas textuales del PDF | [D-01_PDF_CHECK.md](decisiones/D-01_PDF_CHECK.md) | Implementar C-03; completar revisión jurídica del aviso antes de publicación |
| 2026-10-17 | D-02 | Promotor del proyecto | Aprobó la redacción de duración e invalidación del contexto activo | [D-02_CONTEXTO_ACTIVO_CHECK.md](decisiones/D-02_CONTEXTO_ACTIVO_CHECK.md) | Implementar C-01 y C-02 |
| 2026-10-17 | D-03 | Promotor del proyecto | Aprobó la definición operativa y el ciclo de intentos de `PDF_DOWNLOADED`; C-05 no iniciado | [D-03_MEDICION_DESCARGA_PDF.md](decisiones/D-03_MEDICION_DESCARGA_PDF.md) | Planificar e implementar C-05; definir técnicamente la ventana de espera |
| 2026-10-17 | D-04 | Promotor del proyecto | Aprobó el demostrador gratuito de punto de equilibrio; A-02 aún no implementado ni verificado | [D-04_CALCULADORA_PUNTO_EQUILIBRIO.md](decisiones/D-04_CALCULADORA_PUNTO_EQUILIBRIO.md) | Planificar A-02 conforme a las dependencias de H2 |
| 2026-10-17 | D-05 | Promotor del proyecto | Aprobó el primer lead magnet y retiró del correo transaccional la invitación al Check; A-03 no implementado ni verificado, Excel definitivo pendiente de provisión externa | [D-05_PRIMER_LEAD_MAGNET.md](decisiones/D-05_PRIMER_LEAD_MAGNET.md) | Integrar el Excel cuando corresponda ejecutar A-03 |
| 2026-10-17 | D-06 | Promotor del proyecto | Aprobó el alcance funcional; siguen pendientes los avisos definitivos, datos del responsable, canales ARCO, revisión jurídica y validación de retenciones; sin implementación ni verificación | [D-06_TEXTOS_PRIVACIDAD_CONSENTIMIENTOS.md](decisiones/D-06_TEXTOS_PRIVACIDAD_CONSENTIMIENTOS.md) | Completar requisitos jurídicos antes de producción |
| 2026-10-17 | D-07 | Promotor del proyecto | Aprobó orientación con botón sin descripción, una solicitud abierta por diagnóstico, correo principal y WhatsApp alternativo autorizado; C-09/C-10 sin implementar ni verificar | [D-07_OPERACION_ORIENTACION.md](decisiones/D-07_OPERACION_ORIENTACION.md) | Configurar responsable, horario y objetivo de respuesta antes de habilitar atención pública |
| 2026-10-17 | D-08 | Promotor del proyecto | Aprobó reglas de medición, tasa por sesión calificada y primer corte al alcanzar 500 sesiones; O-08/O-09 sin implementar ni verificar y H5 sin evaluar | [D-08_MEDICION_GATE_FASE_A.md](decisiones/D-08_MEDICION_GATE_FASE_A.md) | Instrumentar y verificar métricas cuando corresponda ejecutar O-08/O-09 |
| 2026-10-17 | D-09 | Promotor del proyecto | Aprobó gobierno editorial, autoridad de nuevas versiones, trazabilidad en GitHub y regla de correcciones; sin cambios al catálogo ni implementación técnica | [D-09_GOBIERNO_CATALOGO_ACCIONES.md](decisiones/D-09_GOBIERNO_CATALOGO_ACCIONES.md) | Revisar D-10; ejecutar C-03, C-13 y C-15 según la secuencia del plan |
| 2026-10-17 | D-10 | Promotor del proyecto | Aprobó IDs iniciales, matriz RF-A01–RF-A17, prioridad A-01, cuatro entregas y cierre con evidencia; autorizó Entrega 1 | [D-10_BACKLOG_TRAZABILIDAD.md](decisiones/D-10_BACKLOG_TRAZABILIDAD.md) | Construir y presentar Entrega 1 para aprobación visual, sin cerrar A-01 |
| 2026-10-17 | A-01 | Equipo técnico | En curso: estructura navegable implementada para revisión visual; 30 pruebas Django correctas y rutas públicas revisadas en Chrome de escritorio/móvil. Medición de clics y aprobación visual pendientes | [Home escritorio](../qa_artifacts/portal-home-desktop.png), [Home móvil](../qa_artifacts/portal-home-mobile.png), [Herramientas escritorio](../qa_artifacts/portal-tools-desktop.png), [Herramientas móvil](../qa_artifacts/portal-tools-mobile.png) | Recibir revisión visual del promotor; mantener A-01 abierta hasta completar sus criterios |
| 2026-10-17 | A-01 | Equipo técnico | Segunda iteración visual AV-01–AV-23: jerarquía de Home, navegación, páginas específicas y composición móvil ajustadas. Capturas en escritorio al 100 % y en 369×545/390×844; Check revisado hasta resultado móvil. Entrega 1 sigue sin aceptación visual; medición de clics y cierre de A-01 pendientes | [Home escritorio](../qa_artifacts/av2-home-1365x900.png), [Home 369×545](../qa_artifacts/av2-home-369x545.png), [Herramientas escritorio](../qa_artifacts/av2-tools-1365x900.png), [Contacto escritorio](../qa_artifacts/av2-contact-1365x900.png), [Resultado Check móvil](../qa_artifacts/av2-check-result-369x545.png) | Revisión visual del promotor; atender observaciones antes de solicitar aceptación de Entrega 1 |
| 2026-10-17 | A-01 | Equipo técnico | Tercera ronda AV-24–AV-29: entrada del Check compacta, «Contenidos» homologado, mensaje de marca ampliado, sección activa y breadcrumbs accesibles. Las seis rutas se revisaron a 1365×900, 369×545 y 390×844 sin desbordamiento horizontal; 32 pruebas Django correctas y Check recorrido hasta resultado con datos ficticios. Entrega 1 aún requiere aceptación visual del promotor | [Check escritorio](../qa_artifacts/av3-check-1365x900.png), [Check móvil](../qa_artifacts/av3-check-369x545.png), [Home móvil](../qa_artifacts/av3-home-369x545.png), [Contenidos móvil](../qa_artifacts/av3-content-369x545.png), [Resultado Check móvil](../qa_artifacts/av3-check-result-369x545.png) | Presentar Entrega 1 para aprobación visual definitiva; mantener A-01 abierta hasta completar sus criterios |
| 2026-10-17 | A-01 / Entrega 1 | Promotor del proyecto | **APROBADA CON SALVEDADES.** Cierre visual de AV-01–AV-29, con AV-24–AV-29 resueltos según la evidencia de la tercera ronda. Favicon oficial, clics principales de A-01 y prueba en móvil físico pendientes. A-01 sigue EN CURSO; H2 pendiente de aceptación integral; D-10 permanece aprobada | [Verificación de Entrega 1](VERIFICACION.md), [Home móvil](../qa_artifacts/av3-home-369x545.png), [Entrada Check móvil](../qa_artifacts/av3-check-369x545.png) | Completar salvedades en sus actividades; preparar A-02 como siguiente capacidad funcional prioritaria conforme a D-04, sin iniciar Entrega 2 automáticamente |
| 2026-10-19 | A-02 / Entrega 2 | Equipo técnico | **EN CURSO.** Calculadora mensual Django con `Decimal`, tres entradas, cuatro resultados, casos de margen y eventos por interacción. 40 pruebas Django correctas; `manage.py check` correcto; Chrome sin JavaScript en 1365×900, 369×545 y 390×844 sin desbordamiento. No se declara A-02 terminada ni Entrega 2 aceptada | [Calculadora escritorio](../qa_artifacts/a02-calculator-1365x900.png), [Calculadora móvil 369×545](../qa_artifacts/a02-calculator-369x545.png), [Calculadora móvil 390×844](../qa_artifacts/a02-calculator-390x844.png), [Prueba visual](../qa_artifacts/a02_verify.cjs) | Revisión funcional y visual del promotor; O-08 debe integrar/verificar medición transversal antes del cierre de instrumentación |
| 2026-10-19 | A-02 / refinamiento AV-01–AV-07 | Equipo técnico | AV-01, AV-02, AV-03, AV-04, AV-05 y AV-07 resueltos: breadcrumb jerárquico, tarjetas móviles sin desborde, advertencia íntegra y legible, errores por campo, Limpiar por GET y moneda negativa con signo previo. **AV-06 parcial:** F5 reenvía el POST en Chrome; el token lo deduplica y Django redirige a GET vacío, sin persistir importes ni duplicar eventos. Evitar incluso ese reenvío requeriría conservar el resultado entre POST y GET o depender de JavaScript; se mantiene la solución mínima de D-04. 42 pruebas Django y revisión Chrome sin JavaScript en 1365×900, 369×545 y 390×844 correctas. A-02 permanece EN CURSO | [Resultado móvil](../qa_artifacts/a02-refined-positive-369x545.png), [Error móvil](../qa_artifacts/a02-refined-error-369x545.png), [Margen negativo móvil](../qa_artifacts/a02-refined-negative-369x545.png), [Prueba de navegador](../qa_artifacts/a02_refine_verify.cjs) | Revisión del promotor; completar O-08 y criterios pendientes antes de cerrar A-02 |
| 2026-10-19 | A-02 / AV-08 | Equipo técnico | **Estados visuales implementados:** positivo conserva cuatro tarjetas normales; cero usa advertencia ámbar; negativo usa alerta roja suave y destaca margen y explicación. Cada estado se identifica también por texto. Sin cambios a fórmulas, límites, validaciones ni eventos. 44 pruebas Django correctas; Chrome sin JavaScript en 1365×900, 369×545 y 390×844: cuatro tarjetas por estado, cifras exactas, sin desbordamiento y contraste medido superior a 7:1 en etiquetas y explicaciones. A-02 sigue EN CURSO; AV-06 y O-08 conservan sus salvedades | [Positivo móvil](../qa_artifacts/a02-state-positive-369x545.png), [Cero móvil](../qa_artifacts/a02-state-zero-369x545.png), [Negativo móvil](../qa_artifacts/a02-state-negative-369x545.png), [Prueba comparativa](../qa_artifacts/a02_states_verify.cjs) | Revisión visual del promotor antes de cerrar A-02; completar O-08 según plan |
| 2026-10-19 | A-02 / aceptación funcional y visual | Promotor del proyecto | **APROBADA CON SALVEDADES** la implementación funcional y visual de la calculadora, incluidos A02-AV01–AV08. Se acepta AV-06: F5 puede reenviar el POST, pero no duplica eventos y termina en GET vacío; no se añaden persistencia de importes ni JavaScript obligatorio. Se aprueban los estados positivo, cero y negativo de AV-08 tras revisión de escritorio y móvil. **A-02 y Entrega 2 siguen EN CURSO; D-04 permanece APROBADA; O-08 requiere integración y verificación transversal.** | [Verificación A-02](VERIFICACION.md), [D-04](decisiones/D-04_CALCULADORA_PUNTO_EQUILIBRIO.md), [Positivo escritorio](../qa_artifacts/a02-state-positive-1365x900.png), [Cero escritorio](../qa_artifacts/a02-state-zero-1365x900.png), [Negativo escritorio](../qa_artifacts/a02-state-negative-1365x900.png) | Integrar y verificar O-08 cuando se autorice; avanzar según secuencia de Entrega 2 sin declarar A-02 terminada |

## Regla común de terminado

Una actividad se marca `[x]` cuando tiene: implementación o decisión aprobada, prueba adecuada al riesgo, evidencia enlazada, documentación operativa actualizada y responsable de operación definido. Para publicar, además debe pasar en staging y no mantener defectos críticos abiertos.
