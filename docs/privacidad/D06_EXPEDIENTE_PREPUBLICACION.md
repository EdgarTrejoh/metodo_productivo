# D-06 — Expediente de privacidad previo a publicación

**BORRADOR INTERNO — NO AUTORIZADO PARA PUBLICACIÓN**

**Corte de revisión:** 29 de octubre de 2026

**Objeto:** preparar la revisión administrativa, jurídica y técnica de D-06 sin modificar su aprobación funcional del 17 de octubre de 2026. Este archivo no sustituye el aviso provisional local ni autoriza usar datos reales o publicar textos. O-02 sigue su curso independiente.

**Fuente editorial posterior:** «Aviso de privacidad integral – Método Productivo.docx», versión 1.1, entregado por el promotor (SHA-256 `8BBEFED8E10DECA53ABD358619DD54ECC96FAADA3B5E6DAD602B831228B1DCF6`; archivo maestro externo al repositorio). La sección 4 de este expediente conserva el borrador histórico; la pantalla local `/privacidad/` integra la versión 1.1 conforme a [VERIFICACION.md](../VERIFICACION.md). La revisión jurídica y la publicación permanecen pendientes.

## 1. Alcance, fuentes y criterio de lectura

Se contrastaron [D-06](../decisiones/D-06_TEXTOS_PRIVACIDAD_CONSENTIMIENTOS.md), [D-02](../decisiones/D-02_CONTEXTO_ACTIVO_CHECK.md), [D-05](../decisiones/D-05_PRIMER_LEAD_MAGNET.md), [D-07](../decisiones/D-07_OPERACION_ORIENTACION.md), [PLAN_TRABAJO](../PLAN_TRABAJO.md), BRD v0.6 y el código local de `diagnostics`, `leads`, `analytics`, `core`, `content`, `store`, `config`, plantillas y backoffice. Las afirmaciones de implementación describen este corte de código; no acreditan operación productiva. La referencia jurídica es la [LFPDPPP vigente, última reforma DOF 14-11-2025](https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf), especialmente artículos 5, 7–9, 11–16, 18–20, 21–36. La [reforma del 14 de noviembre de 2025](https://www.dof.gob.mx/nota_detalle.php?codigo=5773097&fecha=14/11/2025) modificó el artículo 4; no se usa una versión anterior de la ley para este expediente.

**Distinción:** los plazos funcionales del Check y otros recorridos confirmados en D06-AVISO-04, el acceso por contexto activo, la separación de finalidades, el opt-in comercial opcional y la baja inmediata son decisiones funcionales aprobadas. Su implementación y validación jurídica, la identidad del responsable, el aviso publicable, la modalidad de consentimiento por finalidad, la clasificación de datos y las transferencias siguen pendientes. Poner el aviso a disposición no equivale a obtener consentimiento; la ley contempla consentimiento expreso, tácito y excepciones, según el caso. No se presupone una casilla obligatoria universal.

## 2. Matriz de tratamientos reales de Fase A

**Clave:** «actual» describe código local; «propuesto» es trabajo sujeto a validación. Los identificadores de evento pueden vincularse con datos por ejecución, solicitud o contexto, aunque la tabla de eventos no guarde nombres. No se atribuyen al Check importes, cuentas, documentos financieros, datos patrimoniales ni datos sensibles solicitados: sus ocho respuestas son opciones sobre prácticas de gestión. Las preguntas pueden referirse a existencia de información empresarial, sin pedir sus cifras.

| Recorrido | Datos recopilados | Finalidad | Consentimiento | Conservación | Destinatarios/proveedores | Implementación |
| --- | --- | --- | --- | --- | --- | --- |
| Navegación pública, blog, tienda informativa y sesión | Cookie de sesión/CSRF, solicitudes y metadatos técnicos que el servidor o infraestructura pudieran registrar; navegación a contenido. No hay cuenta pública. | Entregar páginas, seguridad y continuidad del recorrido. | Aviso y modalidad técnica por confirmar, incluido uso de cookies y registros. | Sesión de navegador; plazo de logs por confirmar. | Alojamiento, proxy y operación por confirmar. | Django SSR; `SESSION_EXPIRE_AT_BROWSER_CLOSE=True`; no se identificó SDK de analítica de terceros. Tienda B-01 es escaparate local, sin venta LIVE. |
| Check PyME: cuestionario, captura, resultado y PDF | Ocho respuestas codificadas sobre prácticas de gestión; nombre, correo, empresa y WhatsApp opcional; ejecución, versiones, puntuación, nivel, acciones, fechas y resultado. | Generar y mostrar diagnóstico; conservar internamente contacto, respuestas y resultado 12 meses; PDF dentro del contexto activo. | Finalidad necesaria separada de comercial. Modalidad jurídica pendiente; el código exige una casilla `service` provisional. | **12 meses desde finalización aprobados**; `retention_until` se calcula al crear el diagnóstico. Contexto de acceso: 30 minutos de inactividad renovables, sin recuperación pública. | Personal autorizado y alojamiento/base de datos por confirmar; no se envía el informe por correo. | `Diagnostic` guarda JSON de contacto, respuestas y resultado; `Lead` por correo; `Consent` servicio/comercial y eventos. No hay borrado al vencer el plazo. |
| Solicitud de orientación desde resultado | Reutiliza diagnóstico, nombre, correo, empresa y WhatsApp opcional; estado y fecha de solicitud. No pide descripción ni adjuntos. | Atender orientación solicitada expresamente. | El botón es acción expresa de solicitud; no implica marketing. Modalidad jurídica y aviso por validar. | Política de solicitud/seguimiento pendiente; vínculo al diagnóstico de 12 meses requiere resolución. | Personal de backoffice; eventual proveedor de correo interno y uso autorizado de WhatsApp por confirmar. | `Orientation` se crea una vez por diagnóstico y evento `ORIENTATION_REQUESTED`; aún faltan notificación, responsable, trazabilidad de seguimiento y control operativo de D-07. |
| Recurso Excel gratuito: solicitud, correo, enlace y entrega | Nombre, correo, recurso, identificador de solicitud, hash de token, emisión, vencimiento, contador de acceso, estado de correo, operación y fecha de acceso; IP transformada en hash temporal para límite de frecuencia. | Enviar el enlace transaccional y autorizar la entrega privada del Excel solicitado. | Solicitud del recurso independiente del comercial. Se graba `service=True` sin casilla de servicio; modalidad jurídica pendiente. | Enlace: 72 horas y máximo tres accesos aprobados. Solicitudes y otros leads: 24 meses desde última interacción como política funcional, aún sin purga ni validación jurídica. Hashes de límite: una hora en caché local. | Backend de correo configurado; proveedor real pendiente. Archivo privado local en este entorno. | Recorrido A-03 local: `GET` intermedio, `POST` de autorización, `LEADMAGNET_DELIVERED` por operación y `EMAIL_FAILED` si procede. El correo transaccional no promociona el Check. |
| Contacto: comentario o solicitud | Tipo, mensaje libre de hasta 3000 caracteres, nombre y correo; identificador, solicitud de respuesta, estado, nota interna y fechas. | Recibir comentario; dar seguimiento a la solicitud cuando corresponda; bandeja y aviso interno. | Enviar contacto no suscribe a marketing. Aviso y modalidad jurídica por validar. | 12 meses después del cierre como política funcional, aún sin purga ni validación jurídica. | Personal de backoffice; destinatario de notificación interna y proveedor de correo por confirmar. El aviso interno actual solo remite al backoffice, sin cuerpo del mensaje. | `ContactSubmission` y `FORM_SUBMITTED`; estado de notificación. Los campos libres `message` e `internal_note` pueden contener datos personales adicionales que la persona incluya espontáneamente, incluso información que exija tratamiento reforzado. No se solicita tal información; revisar minimización, acceso, respuesta y supresión. |
| Preferencia y comunicaciones comerciales | Correo asociado al lead, elección booleana por ejecución, versión de texto y fecha; potencial historial de elecciones separadas. | Registrar preferencia y, solo si procede, enviar contenido comercial. | Opción independiente, voluntaria, desmarcada y revocable según D-06. Check, Excel, contacto y orientación no equivalen a opt-in. | Hasta revocación o 24 meses de inactividad como política funcional, aún sin purga ni validación jurídica; evidencia mínima de supresión por validar. | Plataforma/proveedor de envíos comerciales aún no identificado. | Check y recurso registran `Consent(commercial)` verdadero o falso. No se identificó envío comercial, centro de preferencias ni ruta `GET`/`POST /baja/{token}/` implementados. |
| Analítica y eventos de producto | Tipo de evento, UUID de ejecución y fecha; algunos eventos permiten asociación indirecta con diagnóstico, lead, contacto o entrega. Calculadora: importes en POST para cálculo inmediato, sin persistencia de importes. | Medir uso, conversión, entrega y fallos operativos conforme al alcance aprobado. | Relación con aviso, base/modalidad y minimización por revisar; no inferir permiso comercial. | Eventos y logs: plazo pendiente; revisar desasociación al vencer datos fuente. | Base de datos local; eventual servicio analítico por confirmar. | `ProductEvent` conserva `kind`, `execution`, `occurred_at`; se registran eventos de Check, lead magnet, contacto y calculadora. No se identificó analítica externa configurada. `PAGE_VIEW` aparece en recurso; O-08 sigue pendiente. |
| Administración, contenido y seguridad | Cuenta, credenciales gestionadas por Django, permisos, sesión, dispositivo TOTP; acciones sobre leads, diagnósticos, mensajes, medios y productos; archivos editoriales pueden contener datos personales si se cargan. | Control de acceso y operación editorial y de solicitudes. | Relación laboral/contractual y avisos internos separados por confirmar; no se cubre con opt-in comercial del visitante. | Cuentas, TOTP, logs, medios y notas: plazos por confirmar. | Personal autorizado; alojamiento/almacenamiento por confirmar. Video público: YouTube se carga por acción del visitante y requiere inventario de destinatario/cookies antes de publicar contenidos. | Admin OTP; `Lead`, `Consent`, `Diagnostic` y `ProductEvent` solo lectura; `ContactSubmission` permite estado y nota interna. Registro de acciones administrativas sensibles A-09 aún pendiente. |

## 3. Información administrativa faltante

| Dato por proporcionar o confirmar | Responsable de aportarlo | Uso en el expediente |
| --- | --- | --- |
| Identidad legal exacta del responsable, tipo de persona y domicilio para el aviso | Promotor | Encabezado legal y avisos simplificados. |
| Persona o departamento de privacidad, correo/canal ARCO, revocación, limitación y domicilio/medio alterno; responsable de plazos | Promotor | Procedimiento publicable y atención efectiva. |
| Canal de baja comercial y remitente/dominio para correos reales | Promotor | Baja, evidencia y textos de correo. |
| Proveedor y ubicación contractual/técnica de hosting, base de datos, respaldos, correo transaccional, notificaciones, eventual marketing, almacenamiento, monitoreo, analítica y video | Promotor/operación | Inventario de encargados y terceros; transferencias. No se supone GCP ni proveedor activo. |
| Personal con acceso, roles, receptores de contacto y orientación; horario y objetivo de primera respuesta de D-07 | Promotor | Accesos, confidencialidad y aviso operativo. |
| Política de logs, respaldos, restauración, respuesta a incidentes y borrado seguro | Promotor/operación | Plazos y garantías técnicas. |
| Plazos definitivos de lead ajeno al Check, solicitud de recurso, accesos, contacto, consentimiento, eventos, medios y cuentas | Promotor con asesoría jurídica | Matriz publicable de conservación. |
| Identificación de cualquier destinatario externo o país de acceso/almacenamiento y finalidad precisa | Promotor/operación | Análisis de encargado frente a transferencia y cláusulas aplicables. |

## 4. Borrador de aviso integral

**BORRADOR INTERNO — NO AUTORIZADO PARA PUBLICACIÓN. Los marcadores administrativos restantes requieren datos verificados; todo el aviso requiere aprobación jurídica y editorial.**

### Aviso de privacidad integral de Método Productivo — versión [VERSIÓN Y FECHA POR APROBAR]

**Responsable.** [IDENTIDAD LEGAL DEL RESPONSABLE] con domicilio en [DOMICILIO DEL RESPONSABLE] es responsable del tratamiento descrito aquí. Para asuntos de privacidad y derechos ARCO: [ÁREA O PERSONA DESIGNADA], [CANAL ARCO], [HORARIO/MEDIO ALTERNATIVO, SI APLICA].

**Datos tratados.** Al usar el Check PyME se tratan nombre, correo, empresa, WhatsApp si se proporciona, ocho respuestas sobre prácticas de gestión, puntuación, diagnóstico y datos técnicos necesarios para operar el recorrido. Para entregar el Excel solicitado se tratan nombre, correo y datos de emisión/acceso al enlace. En Contacto se tratan nombre, correo, tipo y contenido del mensaje, así como notas y estado de seguimiento. Para preferencias comerciales se conserva la elección, versión del texto y fecha.

Para permitir el funcionamiento del portal, utilizamos cookies técnicas relacionadas con la sesión y la protección de formularios. Asimismo, pueden generarse registros técnicos de funcionamiento y errores, utilizados para mantener la seguridad del servicio, detectar fallas y prevenir usos indebidos.

El cuestionario del Check PyME no solicita datos financieros, patrimoniales ni datos personales sensibles. En los formularios que permiten escribir mensajes libres, como Contacto, recomendamos no proporcionar información sensible, confidencial o innecesaria para atender la solicitud.

**Finalidades necesarias del recorrido solicitado.** Los datos personales proporcionados se utilizan para prestar los servicios solicitados: elaborar y mostrar el diagnóstico del Check PyME, permitir su descarga durante el contexto autorizado, entregar recursos digitales, atender mensajes y dar seguimiento a solicitudes expresas de orientación. También se realizan operaciones técnicas necesarias para el funcionamiento y la seguridad del portal.

Estas finalidades son independientes de las comunicaciones comerciales y no requieren que la persona acepte recibir publicidad.

El diagnóstico y sus datos asociados se conservan internamente 12 meses desde la finalización; salir o vencer el contexto impide recuperarlo públicamente, sin limitar derechos ARCO.

**Finalidad comercial separada.** Si la persona acepta voluntariamente recibir comunicaciones comerciales, Método Productivo podrá enviarle por correo electrónico contenidos de educación financiera, productividad y gestión empresarial, novedades sobre herramientas y recursos digitales, así como información y promociones de sus productos y servicios.

Esta finalidad es opcional. Rechazarla no impide utilizar el Check PyME, descargar recursos gratuitos ni solicitar orientación.

**Consentimiento comercial.** La autorización para recibir comunicaciones comerciales se solicita mediante una casilla independiente, desmarcada por defecto. La elección se registra por separado del tratamiento necesario para prestar los servicios solicitados.

La autorización podrá revocarse mediante los mecanismos de baja que deberán estar disponibles antes de habilitar los envíos comerciales.

**Conservación.** Como política funcional, el diagnóstico del Check PyME y sus datos asociados se conservan 12 meses desde su finalización. Otros leads y solicitudes de recursos: 24 meses desde la última interacción. Comentarios y solicitudes: 12 meses después de su cierre. El consentimiento comercial permanece hasta su revocación o 24 meses de inactividad. Tras una baja se conservará únicamente la evidencia mínima necesaria para respetarla, conforme a una política pendiente de validación jurídica.

El enlace del Excel permite acceso durante 72 horas y hasta tres entregas autorizadas; ese límite de acceso no sustituye el plazo de conservación de la solicitud. La eliminación automática, el bloqueo y el tratamiento de respaldos aún no están implementados ni validados para publicación.

**Opciones y derechos.** Para limitar el uso o divulgación, revocar el consentimiento que proceda o ejercer los derechos de acceso, rectificación, cancelación y oposición, se utilizará el correo ARCO configurado en el YAML privado. La solicitud se recibirá, se verificará la identidad o representación de quien la presenta, se localizarán los datos pertinentes y se comunicará la respuesta conforme a la normativa aplicable. La falta de recuperación pública del diagnóstico no limita estos derechos.

La baja comercial será independiente de los mensajes transaccionales necesarios para servicios que se soliciten después. Su mecanismo efectivo debe implementarse antes de habilitar envíos comerciales. Los medios de respuesta y, en su caso, costos de reproducción requieren validación jurídica y operativa.

**Destinatarios y transferencias.** La identificación de proveedores tecnológicos definitivos, sus funciones, la ubicación efectiva de los datos y las posibles transferencias permanece pendiente. Debe distinguirse a quienes traten datos por cuenta del responsable de terceros destinatarios antes de concluir este apartado.

Los videos externos de YouTube se solicitan al activar su reproducción; la página no carga el reproductor al abrirse. El tratamiento de datos que pueda realizar el proveedor externo requiere verificación y revisión jurídica antes de publicar este aviso.

**Cambios.** Las modificaciones del aviso se publicarán en `/privacidad/`, con su número de versión y fecha de actualización indicados en el documento mediante el YAML privado. Los cambios que requieran un nuevo consentimiento quedarán sujetos a la autorización correspondiente antes de aplicarse.

### D06-AVISO-03 — trazabilidad de la depuración editorial

Las cinco redacciones anteriores fueron aprobadas por el promotor para el borrador de revisión. El código usa middleware de sesión y CSRF de Django, con cookies técnicas para continuidad y protección de formularios; no define una política propia de logs HTTP, plazos de conservación ni frecuencia de correos comerciales. La redacción «pueden generarse registros técnicos» evita afirmar un tratamiento de logs más específico que el verificado. Los eventos de producto se almacenan por separado en la base de datos.

**Validación jurídica y operativa pendiente:** confirmar la clasificación aplicable al inventario completo, incluido el texto libre de Contacto; modalidad y redacción definitiva del consentimiento para cada finalidad, incluida la casilla de servicio del Check; existencia y funcionamiento de la baja antes de enviar comunicaciones comerciales; política de logs, cookies, retención y proveedores reales. La aprobación editorial de estas frases no autoriza la publicación del aviso ni suple C-06/A-08/R-05.

**Marcadores que permanecen en la vista local después de D06-AVISO-03:**

| Apartado | Marcador pendiente | Resolución requerida |
| --- | --- | --- |
| Encabezado y responsable | `[NOMBRE COMERCIAL]`, `[VERSIÓN POR APROBAR]`, `[FECHA POR APROBAR]`, `[IDENTIDAD LEGAL DEL RESPONSABLE]`, `[DOMICILIO DEL RESPONSABLE]`, `[ÁREA O PERSONA DESIGNADA]`, `[CANAL ARCO]`, `[HORARIO/MEDIO ALTERNATIVO, SI APLICA]` | Completar y verificar los datos administrativos en `config.yaml`; versión y fecha requieren aprobación editorial. El canal alternativo es opcional. |
| Conservación | `[INSERTAR PLAZOS VALIDADOS, HECHOS DE INICIO, EXCEPCIONES LEGALES, BLOQUEO Y RESPALDOS]` | Definir y validar la retención de recorridos ajenos al Check y su operación real; conservar los 12 meses aprobados del Check. |
| Opciones y derechos | `[CANAL Y PROCEDIMIENTO DEFINITIVOS]`, `[ENLACE/PROCEDIMIENTO FINAL]`, `[DESCRIBIR MEDIOS DE RESPUESTA Y COSTOS REPRODUCCIÓN SI APLICA]` | Aprobar el procedimiento ARCO y de revocación, implementar y verificar la baja comercial, y revisar jurídicamente los medios de respuesta. |
| Destinatarios y transferencias | `[LISTAR PROVEEDORES Y SUS FUNCIONES REALES, PAÍSES DE ACCESO/ALMACENAMIENTO, TERCEROS DESTINATARIOS, TRANSFERENCIAS Y CLÁUSULA/OPCIÓN DE ACEPTACIÓN CUANDO PROCEDA]`, `[CONFIRMAR CARGA DE VIDEO Y SUS IMPLICACIONES]` | Cerrar inventario de proveedores/ubicaciones y validar jurídicamente encargados, transferencias y carga de video. |
| Cambios | `[MEDIO Y PROCEDIMIENTO APROBADOS]`, `[UBICACIÓN APROBADA]` | Aprobar cómo se comunicarán modificaciones y dónde se mostrará el historial o versión vigente. |

### D06-AVISO-04 — consolidación aprobada para revisión visual

La tabla anterior registra el estado histórico tras D06-AVISO-03. En D06-AVISO-04 el promotor confirmó la política funcional de conservación, el correo ARCO administrado en YAML, la publicación de cambios en `/privacidad/` y la independencia de la baja comercial. Estos acuerdos sustituyen los marcadores de conservación, canal/procedimiento general de ARCO y cambios en la vista local. También se sustituyó la instrucción sobre video por el comportamiento verificado en `static/video_embed.js`: el reproductor externo se crea cuando la persona activa la reproducción.

**Pendientes administrativos en el aviso:** identidad y domicilio de la persona física, persona responsable de atención, correo ARCO, versión y fecha se obtienen únicamente de `config.yaml`; si faltan, sus marcadores continúan visibles. El canal alternativo es opcional y se omite cuando está vacío. Completar el YAML no autoriza jurídicamente el aviso.

**Pendientes sustantivos para dictamen:** identificar proveedores definitivos, ubicación efectiva y posibles transferencias; distinguir encargados de terceros destinatarios; verificar el tratamiento del proveedor audiovisual; definir operación de respaldos, bloqueo y eliminación; implementar y probar la baja comercial; validar los medios de respuesta ARCO y eventuales costos de reproducción; determinar modalidad de consentimiento por finalidad; obtener aprobación jurídica y editorial final. Los plazos confirmados son **política funcional**, no evidencia de purga automática ni validación legal. La redacción de destinatarios declara expresamente su incompletitud: **NO AUTORIZADO PARA PUBLICACIÓN**.

## 5. Avisos simplificados propuestos por formulario

La ley (arts. 15–16) exige que el aviso simplificado para captura electrónica contenga al menos identidad/domicilio del responsable, datos tratados, finalidades con distinción de las que requieren consentimiento, opciones para limitar uso/divulgación y ubicación del aviso integral. Por eso los siguientes bloques son **estructura de trabajo**, no copias publicables. Reemplazar marcadores y validar modalidad por finalidad.

| Ubicación | Propuesta funcional de bloque breve, sujeta a validación |
| --- | --- |
| Captura del Check | «[RESPONSABLE Y DOMICILIO] tratará tu nombre, correo, empresa, WhatsApp opcional y respuestas sobre prácticas de gestión para generar y mostrar tu Check PyME y conservar internamente el diagnóstico y datos asociados durante 12 meses desde su finalización. Al salir no podrás recuperar el informe en el portal. La recepción de comunicaciones comerciales es opcional e independiente. Puedes limitar usos mediante [MEDIO] y consultar el aviso integral en `/privacidad/`. [MODALIDAD DE CONSENTIMIENTO VALIDADA]». |
| Recurso Excel | «[RESPONSABLE Y DOMICILIO] usará tu nombre y correo para enviarte el enlace privado del Excel que solicitas y registrar su entrega. La opción comercial es independiente. Puedes limitar usos mediante [MEDIO]. Consulta `/privacidad/`. [MODALIDAD VALIDADA]». |
| Contacto | «[RESPONSABLE Y DOMICILIO] tratará tu nombre, correo, tipo y mensaje para recibir tu comentario o atender tu solicitud. Evita incluir datos personales innecesarios en el texto libre. Enviar este mensaje no te suscribe a comunicaciones comerciales. Puedes limitar usos mediante [MEDIO]. Consulta `/privacidad/`. [MODALIDAD VALIDADA]». |
| Orientación desde resultado | «Solicito contacto sobre este diagnóstico usando los datos ya proporcionados. Esta solicitud no me suscribe a comunicaciones comerciales». Mostrar enlace al aviso integral y referencia a responsable/medio de limitación validada en el contexto, sin nueva captura ni descripción. |

**Consentimiento comercial opcional, texto funcional D-06:** «Quiero recibir comunicaciones comerciales de Método Productivo por correo. Puedo darme de baja después». Casilla independiente y desmarcada; registrar decisión incluso si es negativa, texto/versión y fecha según RF-A09. El envío comercial y su contenido concretos deberán corresponder al aviso validado. No copiar el texto provisional del Check como dictamen sobre consentimiento de servicio.

## 6. Procedimiento propuesto ARCO, revocación y baja

1. **Recepción.** Publicar [CANAL ARCO] y designar [RESPONSABLE INTERNO]. Registrar fecha, tipo de petición y folio; proteger los documentos de identidad. La ausencia de acceso público al informe no impide solicitar datos del diagnóstico conservado internamente.
2. **Acreditación y localización.** Solicitar nombre y medio de notificación, acreditación de identidad o representación, derecho ejercido y descripción que permita localizar registros (art. 28). Buscar por correo normalizado y relaciones con diagnósticos, solicitudes, consentimiento, eventos y respaldos; evitar revelar datos a quien no acredite titularidad. No exigir ID público del Check.
3. **Evaluación y respuesta.** Documentar procedencia, corrección, acceso, bloqueo/cancelación u oposición y excepciones legales. La ley establece comunicación de la determinación en máximo 20 días desde recepción y, si procede, hacerla efectiva dentro de los 15 días siguientes; una ampliación única por periodo igual requiere justificación (art. 31). Validar cómputo y formatos con asesoría jurídica.
4. **Revocación.** Recibir por [CANAL], verificar identidad, detener el tratamiento futuro al que aplique sin efecto retroactivo, conservar solo la evidencia mínima autorizada y comunicar resolución. Separar revocación de servicio, oposición y baja comercial; analizar obligaciones de conservación antes de eliminar.
5. **Baja comercial.** Conforme a D-06/J8, `GET /baja/{token}/` muestra página sin cambiar preferencia; `POST` válido cambia inmediatamente a no aceptar/revoca y confirma. Token inválido: mensaje genérico y ruta de contacto. Suprimir nuevos envíos comerciales, conservar evidencia mínima de supresión y permitir correos transaccionales de solicitudes posteriores. La ruta y el proceso aún no existen en el código.
6. **Cierre y control.** Guardar folio, petición, decisión, fechas, sistemas afectados y evidencia mínima con acceso restringido y plazo aprobado. Si hay encargados o terceros que deban actuar sobre rectificación/cancelación, coordinarlo conforme al dictamen. Probar el flujo con datos sintéticos antes de datos reales.

## 7. Matriz de conservación y propuesta de disposición

| Conjunto | Regla o valor de trabajo | Estado y disposición propuesta |
| --- | --- | --- |
| `Diagnostic.contact`, `answers`, `result` y vínculo al lead | **12 meses desde finalización, aprobado** | `retention_until` ya se calcula. C-07 debe suprimir o anonimizar efectivamente al vencer, con criterio verificable; no hay tarea de purga. Resolver antes la relación con orientación, eventos y lead compartido. |
| Contexto de sesión del Check | 30 minutos de inactividad renovables, D-02 | Es acceso temporal, no retención del diagnóstico. Expira/sale sin recuperación pública. |
| Enlace de recurso | 72 horas, máximo tres accesos, D-05 | Revocar acceso por vencimiento/agotar; solicitudes, hashes y registros de acceso necesitan plazo separado. |
| Otros leads y solicitudes de recursos | 24 meses desde última interacción, política funcional confirmada en D06-AVISO-04 | **No implementado ni validado jurídicamente.** Definir «última interacción» y resolver cuando un mismo lead tenga diagnósticos, recursos o consentimientos con plazos distintos. |
| Consentimiento comercial | Hasta revocación o 24 meses de inactividad, política funcional confirmada en D06-AVISO-04 | **No implementado ni validado jurídicamente.** Distinguir permiso activo de evidencia mínima de supresión; no reactivar por una solicitud transaccional. |
| Comentarios, solicitudes y notas | 12 meses después del cierre, política funcional confirmada en D06-AVISO-04 | **No implementado ni validado jurídicamente.** Definir cierre, tratamiento de texto libre y solicitudes sin respuesta. |
| Orientación | Sin plazo aprobado específico | Definir interacción con diagnóstico de 12 meses, seguimiento y cierre; evitar conservación indefinida. |
| Eventos, logs, IP hashes, cuentas, medios y respaldos | Sin plazo aprobado específico; caché de límites local de una hora | Definir mínimos por finalidad, disociación, rotación y restricciones de restauración. Los UUID de eventos pueden seguir siendo enlazables. |

**Diseño propuesto para C-07/C-08.** Ejecutar purga idempotente por fecha, en transacción o lotes seguros, con conteos y errores sin datos personales en logs. Separar datos del diagnóstico vencido de un `Lead` que aún respalde otra solicitud; mantener solo el identificador o evidencia mínima que tenga fundamento y plazo aprobados. La anonimización solo cuenta si impide razonablemente reidentificar mediante otras tablas/UUID; borrar el JSON visible sin romper vínculos no basta. Revisar la política de bloqueo por responsabilidades antes de supresión definitiva (arts. 10 y 24–25). Definir tratamiento de copias de respaldo: periodo de rotación, acceso restringido, no uso ordinario y reaplicación de supresiones tras restauración. Documentar incidentes, reejecución segura y prueba con datos sintéticos. Ninguna de estas acciones está implementada por este expediente.

## 8. Proveedores, encargados y transferencias por confirmar

| Función observada o prevista | Evidencia local | Confirmación necesaria |
| --- | --- | --- |
| Alojamiento, proxy, base PostgreSQL y respaldos | Configuración local Docker/PostgreSQL y variables de staging; O-02 separado | Proveedor real, país, acceso administrativo, subencargados, contrato, respaldo y retención. |
| Correo transaccional del Excel y avisos internos | `send_mail`; backend local por defecto; `DEFAULT_FROM_EMAIL` de prueba | Proveedor, remitente, países, datos que recibe y contrato. |
| Correo comercial | No hay motor/ruta de envío comercial implementados | Determinar si existirá y quién lo operará antes de mencionarlo como destinatario efectivo. |
| Almacenamiento privado y medios editoriales | Directorio privado local, `MEDIA_ROOT` local | Ubicación productiva, acceso, retención y respaldos. |
| Analítica/monitoreo | Eventos Django en base; no se identificó SDK analítico externo | Confirmar eventuales servicios, cookies, identificadores y acceso a logs antes de avisar o activar. |
| Video externo | Código de YouTube embebido al activar reproducción por el visitante | Precisar datos/cookies enviados, destinatario, país y texto/control aplicable. |
| Personal interno y soporte | Admin OTP, usuario/roles y bandeja | Personas, permisos, confidencialidad y acceso a mensajes libres/diagnósticos. |

**Pregunta jurídica:** distinguir a cada proveedor que trata datos por cuenta e instrucciones del responsable de un tercero receptor de una transferencia. Para transferencias nacionales o internacionales, revisar los artículos 35–36, la comunicación del aviso, cláusula de aceptación o excepción aplicable, contratos y jurisdicción. No afirmar que existe transferencia internacional solo por contemplar infraestructura futura.

## 9. Observaciones para dictamen jurídico

| ID | Cuestión concreta | Evidencia/decisión | Dictamen requerido |
| --- | --- | --- | --- |
| J-01 | Modalidad de consentimiento para Check, recurso, Contacto, orientación, seguridad/analítica y marketing; alcance de la casilla obligatoria actual | D-06 separa aviso y consentimiento; art. 7 contempla tácito/expreso y art. 9 excepciones | Determinar modalidad por finalidad y ajustar C-06 sin crear obligación universal. |
| J-02 | Clasificación de datos del Check y de texto libre | Check no solicita importes ni sensibles; Contacto permite mensaje y nota libre | Clasificar datos efectivamente tratados y protocolo para datos adicionales no solicitados. |
| J-03 | Contenido final integral y simplificado | Arts. 14–16; faltan responsable/domicilio/canal | Aprobar texto, ubicación, versión y medio de cambios. |
| J-04 | Operación de los plazos aprobados y bloqueo | Política funcional D06-AVISO-04; código sin purga | Validar jurídicamente detonantes, excepciones, supresión, respaldo y evidencia mínima; implementar y comprobar después. |
| J-05 | ARCO y revocación frente a informe no recuperable | D-02 impide acceso público, no derechos; arts. 21–34 | Aprobar identificación, canales, plazos y operación interna. |
| J-06 | Proveedores, cookies, analítica, video y transferencias | Infraestructura productiva no cerrada; art. 35–36 | Calificar encargados/terceros, países, contratos y cláusulas. |
| J-07 | Uso de WhatsApp para orientación | D-07 solo si fue proporcionado y autorizado para esa finalidad | Aclarar aviso, canal y evidencia de autorización. |
| J-08 | Baja comercial, conservación de supresión y reactivaciones | D-06/J8; código solo `Consent` por ejecución | Aprobar efecto, identidad del solicitante, historial y plazo de evidencia. |
| J-09 | Datos de personal y contenido editorial | Admin OTP y medios; fuera de captura de visitante | Delimitar aviso interno, roles y tratamiento de imágenes o contenido con personas. |

## 10. Diferencias entre lo aprobado y lo implementado

| Regla aprobada o necesaria | Estado observado al corte | Actividad |
| --- | --- | --- |
| Aviso integral y breves definitivos | `/privacidad/` es página estructural no publicable; Check, recurso y Contacto muestran textos provisionales. | D-06, C-06, A-08 |
| Evidencia por finalidad y preferencia comercial | Check y recurso guardan `Consent` con valor, fecha y versión demo; Contacto no tiene registro de versión de aviso. No existe resolución global de preferencia por lead. | C-06, A-04 |
| Modalidad de consentimiento por finalidad | Check exige casilla `service`; recurso graba `service=True` sin casilla; Contacto no tiene casilla. Requiere dictamen, no unificar automáticamente. | D-06, C-06 |
| Baja comercial inmediata por `POST`, sin bloquear transaccionales | No hay ruta, token, preferencia efectiva ni envío comercial. | A-04 |
| Retención efectiva de 12 meses del Check y otros plazos validados | Existe `retention_until`; no hay eliminación/anonimización, política de respaldo ni tarea programada. | C-07, C-08 |
| Orientación D-07 completa | Botón y registro básico existen; notificación, responsable, estados operativos auditables y atención quedan pendientes. | C-09, C-10 (relación con D-06) |
| Validación antes de datos reales | Solo pruebas locales; no hay dictamen ni revisión de correo/proveedores/retención. | R-05 |

## 11. Checklist de aceptación y secuencia sin dependencia de GCP

Marcar solo con evidencia verificable; las casillas pendientes no cambian el estado del plan.

- [x] **D-06 funcional:** alcance y finalidades separadas aprobadas el 17-10-2026; expediente preparatorio elaborado.
- [ ] **D-06 publicable:** promotor completa identidad, domicilio, canal y proveedores; asesoría jurídica aprueba textos, modalidades, clasificación, transferencias y plazos; responsable editorial valida versión.
- [ ] **C-06:** sustituir textos demo solo tras aprobación; ligar versión inmutable, fecha y elección por finalidad a cada formulario; probar negativa comercial sin bloquear servicio y trazabilidad de aviso.
- [ ] **C-07:** política de supresión/anonimización del Check a 12 meses y otros conjuntos aprobada; resolver lead compartido, orientación, eventos, bloqueo y respaldos; probar solicitudes ARCO y vencimiento con datos sintéticos.
- [ ] **C-08:** tarea programada local idempotente, logs sin datos personales, errores visibles, reejecución y restauración probadas; calendarización puede instalarse después según entorno.
- [ ] **A-04:** preferencia comercial efectiva por lead e historial, baja `GET` informativa/`POST` efectiva, token inválido genérico, evidencia mínima y separación de correos transaccionales.
- [ ] **A-08:** publicar aviso integral y simplificados aprobados en `/privacidad/` y formularios; versión y medio de cambios visibles; navegación D-02 hacia Privacidad preservada.
- [ ] **R-05:** revisión jurídica/editorial documentada, pruebas de formularios, rechazo/aceptación comercial, baja, ARCO, retención, respaldo, correo transaccional, permisos y ausencia de datos reales antes del gate.

Tras validar textos y política, C-06, C-07, C-08, A-04 y A-08 pueden desarrollarse y probarse en Django local con SQLite/PostgreSQL y datos sintéticos, sin GCP. La elección de proveedor de correo y hosting real sigue siendo necesaria para cerrar el aviso y R-05; no se contrata ni activa servicio desde este expediente. O-02 no se reabre ni se da por cerrado aquí.

**Punto de parada:** remitir este borrador al promotor y a asesoría jurídica para completar marcadores y dictaminar J-01–J-09. No publicar, implementar, hacer commit ni push como resultado de esta preparación.
