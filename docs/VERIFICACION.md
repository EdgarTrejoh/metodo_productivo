# Verificación local - B0

## B-01 — aceptación funcional y visual local (22 oct 2026)

**Aceptación del promotor:** catálogo `/tienda/`, fichas dinámicas, administración OTP, publicación/retiro, imágenes reutilizables y piloto de Payment Link TEST aprobados en alcance local. El promotor revisó la tienda y la ficha del producto publicado y completó un **pago simulado** desde el Checkout TEST del Simulador de Crédito. Una lectura de la base local confirmó una ficha publicada con `prod_VU03aSWkY1qGQK`, `price_1UT23CDEvKci1tgSdgGv8n96`, $499.00 MXN y el enlace TEST correspondiente; no hay asignación de ese enlace al DEMO de $299. La prueba automatizada creó un segundo producto sintético desde Admin sin nuevas rutas ni código.

**Retorno y alcance:** el promotor confirmó que Stripe tiene configurada la redirección posterior al pago a `http://127.0.0.1:8766/tienda/`. **No se declara comprobada manualmente la navegación final de retorno en el navegador.** La página de éxito o retorno no concede archivos. No hay webhook, orden, derecho de descarga ni envío comercial. La última suite Django completa reportada tuvo **90 pruebas correctas**; las capturas previas corresponden a contenido sintético y no exponen datos de pago.

**Pendientes independientes:** H5, H6, B-02–B-08, Checkout Sessions definitivo, confirmación por webhook, correo comercial, almacenamiento privado definitivo y condiciones fiscales, jurídicas y operativas. Cierre local sin autorización de ventas LIVE ni despliegue.

## B-01 — piloto técnico de Checkout TEST (22 oct 2026)

**Comportamiento:** `stripe_test_payment_url` es opcional en el Admin OTP y rechaza HTTP, dominios ajenos, enlaces de producción, rutas o parámetros adicionales. Requiere entorno Stripe TEST. El botón «Probar compra en Stripe» aparece únicamente en la ficha pública de un producto publicado cuando el enlace pasa la validación, `DEBUG=1` y `STORE_TEST_CHECKOUT_ENABLED=1`; debajo muestra «Pago de prueba. No se realizan cargos reales ni se entregan archivos». Sin enlace, en borrador o con configuración de producción se conserva la ficha sin botón. Ningún producto existente recibió el enlace de $499 de forma automática.

**Evidencia:** suite Django completa de **90 pruebas correctas**, incluidos escenarios de URL inválida, entorno LIVE, flag apagado, `DEBUG=0`, borrador, producto DEMO de $299 sin enlace y destino TEST correcto. Chrome a 1365×900 y 390×844: botón legible, sin desbordamiento; el clic se interceptó localmente y llegó a la URL sintética configurada, **sin solicitar Stripe**. [Ficha escritorio](../qa_artifacts/b01-detail-desktop.png) y [ficha móvil](../qa_artifacts/b01-detail-mobile.png). `manage.py check`, migraciones y `git diff --check` sin incidencias.

**Límite:** este enlace solo permite iniciar una simulación externa cuando el promotor lo configure sobre el producto correcto. No se verificó una transacción real en Stripe ni existe webhook, orden, derecho de entrega o descarga comercial. H5, H6 y B-02–B-08 permanecen abiertos; B-01 sigue en revisión, sin commit, push ni despliegue.

## B-01 — catálogo administrable en desarrollo (22 oct 2026)

**Alcance:** el Admin OTP permite crear, editar, previsualizar, publicar y retirar productos digitales. Las rutas fijas `/tienda/` y `/tienda/<slug>/` muestran solo productos publicados y vigentes; un segundo producto sintético se creó desde el Admin en prueba, sin cambios de código, rutas o plantillas. El estado vacío no inventa ofertas. Las imágenes de productos publicados se sirven públicamente; las de borradores requieren acceso editorial autorizado y la relación impide eliminarlas mientras estén referenciadas. No hay botón de compra, Checkout ni entrega comercial.

**Pruebas:** suite Django completa de **88 pruebas correctas**, incluidos cinco casos nuevos de B-01; `manage.py check`, comprobación de migraciones y `git diff --check` sin incidencias. Recorrido Chrome en base aislada con contenido sintético: catálogo, ficha y Admin OTP a 1365×900 y 390×844, sin desbordamiento horizontal. [Catálogo escritorio](../qa_artifacts/b01-catalog-desktop.png), [catálogo móvil](../qa_artifacts/b01-catalog-mobile.png), [ficha escritorio](../qa_artifacts/b01-detail-desktop.png), [ficha móvil](../qa_artifacts/b01-detail-mobile.png), [Admin](../qa_artifacts/b01-admin-desktop.png). Ningún dato sintético queda publicado en la base local por esta prueba.

**Pendientes:** revisión del promotor, primera ficha/archivo/condiciones reales y verificación operativa futura del identificador privado. Stripe Product y Price son referencias opcionales etiquetadas TEST/LIVE, sin comprobación contra Stripe en este incremento. H5, H6 y B-02–B-08 siguen pendientes; sin ventas, commit, push ni despliegue.

## A-03 — aceptación funcional local (22 oct 2026)

**Aceptación:** el promotor confirmó la descarga manual satisfactoria del Excel definitivo `Mapa_de_Caja_PyME_v0.3.xlsx` mediante el recorrido J4. A-03 queda cerrada en su **alcance funcional local**. El recurso se conserva en `private_resources/`, fuera de control de versiones. No se capturó la pantalla de descarga porque expondría el enlace privado; las capturas anteriores documentan solamente páginas sin tokens.

**CSRF:** se reprodujo el rechazo 403 con `Origin: null` en el POST de confirmación. La página de acceso enviaba `Referrer-Policy: no-referrer`; se ajustó únicamente esa respuesta a `strict-origin`. Con protección CSRF habilitada, un POST legítimo desde `http://127.0.0.1:8767` se aceptó y un origen ajeno o nulo continuó rechazado. La comprobación en navegador confirmó el archivo descargado con el nombre esperado. Se conservan el límite de 72 horas, los tres accesos y la autorización por POST.

**Pruebas:** última suite Django completa: **83 pruebas correctas**; incluye la prueba CSRF focalizada. `manage.py check`, comprobación de migraciones y `git diff --check` correctos. El promotor verificó el recorrido real local; las pruebas automatizadas emplearon un XLSX sintético aislado. Las verificaciones de cierre documental y de repositorio constan en el commit de A-03.

**Pendientes independientes:** O-02 y prueba de concurrencia en PostgreSQL, O-03 almacenamiento productivo, O-04 correo real, O-07 protección compartida, O-08 medición transversal y revisión jurídica. Entrega 2, H2 y H3 permanecen abiertos. Sin despliegue.

## A-03 — Recorrido J4 en desarrollo (21 oct 2026)

**Estado:** A-03 EN CURSO, pendiente de revisión del promotor y del Excel definitivo. `/recursos/mapa-de-caja-pyme/` informa la falta del archivo en el entorno local y bloquea la captura hasta contar con él. El archivo esperado es `private_resources/Mapa_de_Caja_PyME_v0.3.xlsx` (o la carpeta privada configurada en `PRIVATE_RESOURCE_ROOT`), fuera de Git, `static/` y medios públicos. Para prueba manual local, configurar `DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` antes de iniciar el servidor; el enlace se imprime solo en su terminal y debe tratarse como privado. El backend predeterminado sigue siendo de memoria para pruebas automáticas. No se afirma envío a un buzón real. La migración `leads.0003` se aplicó a la SQLite local sin modificar los registros anteriores.

El recorrido registra `PAGE_VIEW` al abrir el formulario, `LEAD_CREATED` solo con un lead nuevo, `EMAIL_FAILED` ante fallo local y `LEADMAGNET_DELIVERED` una vez por operación autorizada después del `POST`. Las solicitudes repetidas reutilizan el lead e invalidan el enlace anterior. Una actualización condicional del contador dentro de la transacción y una operación única evitan exceder el límite o duplicar una entrega. Las pruebas de concurrencia locales emplean SQLite; falta verificar el comportamiento en PostgreSQL como parte de O-02. El limitador de frecuencia es local y básico; O-07 sigue abierto.

**Evidencia:** 10 pruebas focalizadas y suite Django completa de **82 pruebas correctas** con un XLSX sintético en carpeta temporal aislada, sin introducir un Excel ficticio en el repositorio. Validación del formulario, consentimiento, correo, fallo y reintento, `GET`/`POST`, 72 horas, tres accesos, reemisión, idempotencia, concurrencia y archivo privado. `manage.py check`, comprobación de migraciones y `git diff --check` sin incidencias. Chrome sin JavaScript en 1365×900 y 390×844: ruta y breadcrumb correctos, bloqueo honesto y sin desbordamiento horizontal. [Bloqueo escritorio](../qa_artifacts/a03-resource-desktop.png), [bloqueo móvil](../qa_artifacts/a03-resource-mobile.png), [formulario con XLSX sintético en escritorio](../qa_artifacts/a03-resource-form-desktop.png) y [móvil](../qa_artifacts/a03-resource-form-mobile.png). El archivo sintético temporal se retiró tras las capturas. El archivo real y su contenido aún no se han verificado; no se declara aceptación visual.

**Pendientes independientes:** O-02, O-03, O-04, O-07, O-08 y revisión jurídica. No hay Stripe, GCS, envío real ni despliegue.

## A-07 — aceptación funcional y visual local (21 oct 2026)

El promotor **aprobó y cerró A-07 en su alcance funcional y visual local**: A07-AV01, formulario, validaciones, confirmación, registro en `leads.ContactSubmission`, bandeja Django Admin con OTP, filtros, búsqueda, conteos, estados y notas. También aceptó la corrección aislada del archivo temporal en las pruebas de A-05. Las evidencias de las secciones siguientes conservan la secuencia de implementación y revisión; las capturas del Admin utilizan datos sintéticos en una base de prueba.

**Verificación final:** suite Django completa de 72 pruebas correcta; `manage.py check`, `makemigrations --check --dry-run` y `git diff --check` sin incidencias. El recorrido visual cubrió escritorio y móvil con el formulario sin JavaScript y la bandeja OTP con datos sintéticos. La aceptación local no cierra Entrega 2 ni acredita producción: siguen O-02, O-04, O-07, O-08 y revisión jurídica.

## A-07 — Bandeja ligera en Django Admin (21 oct 2026)

**Estado:** lista para revisión, A-07 EN CURSO. El changelist OTP reutiliza `leads.ContactSubmission` y `leads_contactsubmission`: remitente, estado, tipo, fecha, filtros, búsqueda, detalle completo y nota interna. «Recibidos» cuenta todos los registros; «Pendientes» cuenta estados nuevo y en seguimiento, incluso al filtrar la lista. Los registros históricos sin nombre o correo se identifican como tales; el dato almacenado no se altera. El Admin impide agregar y eliminar desde esta vista, y exige OTP y permisos.

- Suite Django completa: **72 pruebas correctas**, incluidas autorización, filtros, conteos cero y positivos, actualización de estado y nota, mensaje completo, ausencia de exposición pública y regresión de A-05/A-06, calculadora y Check. `manage.py check`, `makemigrations --check --dry-run` y `git diff --check`: correctos. El fallo de archivo temporal en Windows continúa resuelto por el cierre explícito de respuestas de imagen en las pruebas de A-05; no se modificó funcionalidad editorial.
- Prueba visual aislada con tres registros y una cuenta OTP **sintéticos en base de pruebas**: conteos 3 recibidos / 2 pendientes; tres filas visibles, detalle completo y sin desbordamiento global a 1365×900 y 390×844. [Bandeja escritorio](../qa_artifacts/a07-inbox-1365x900.png), [bandeja móvil](../qa_artifacts/a07-inbox-390x844.png), [detalle](../qa_artifacts/a07-inbox-detail-1365x900.png), [recorrido](../qa_artifacts/a07_inbox_browser.cjs). Los números de las capturas son de prueba, no cifras de operación.
- Stripe TEST: el producto y enlace facilitados por el promotor se consignaron únicamente como referencia futura en H6 del plan. No se añadieron al portal ni se probó checkout, pago o entrega.

**Pendientes:** aceptación del promotor y, de forma independiente, O-04, O-07, O-08, validación jurídica y publicación. Sin commit, push ni despliegue.

## A07-AV01 — Contacto identificado (21 oct 2026)

**Estado:** ajuste implementado y listo para revisión; A-07 sigue EN CURSO. Tipo y mensaje conservan su obligatoriedad y límite de 3000 caracteres. Nombre y correo válido se exigen para Comentario y Solicitud; la casilla pública de respuesta se eliminó. El modelo conserva campos vacíos para compatibilidad histórica y no se generó otra migración. La base local mantiene el registro histórico sin nombre y correo; no fue modificado. El registro sintético creado por la prueba visual de esta ronda se retiró con su evento asociado.

- Suite Django completa: **71 pruebas correctas**. Cubre ausencia de nombre/correo en ambas categorías, formato inválido, límite de mensaje, envío y confirmación de ambos tipos, persistencia, CSRF, backoffice con OTP, fallo de correo, registro histórico y regresiones del portal, Check y calculadora. `manage.py check`, `makemigrations --check --dry-run` y `git diff --check`: correctos.
- Corrección técnica aislada A-05: las dos pruebas que abren una imagen editorial ahora cierran la respuesta `FileResponse` después de comprobarla, incluida `test_sanitizer_authorized_images_and_protected_reuse`. La suite se ejecutó con `TEMP`/`TMP` apuntando a `.venv/qa312/tmp`, directorio escribible del entorno local Windows. No se alteró código funcional del blog, videos ni biblioteca.
- Chrome sin JavaScript: 1365×900, 369×545 y 390×844; cuatro campos visibles, sin casilla de respuesta ni desbordamiento horizontal. Se comprobó foco de teclado, validación y confirmación. [Escritorio](../qa_artifacts/a07-contact-1365x900.png), [móvil 369](../qa_artifacts/a07-contact-369x545.png), [móvil 390](../qa_artifacts/a07-contact-390x844.png), [error móvil](../qa_artifacts/a07-contact-error-369x545.png), [confirmación](../qa_artifacts/a07-contact-confirmation-1365x900.png), [recorrido](../qa_artifacts/a07_verify.cjs).

**Pendientes independientes:** aceptación del promotor, O-04 (correo productivo), O-07 (límites/CAPTCHA según riesgo), O-08 (medición transversal), revisión jurídica de avisos y retención; prueba en dispositivo móvil físico. No se realizó commit, push ni despliegue.

## A-07 — Contacto y solicitudes (20 oct 2026)

**Estado:** implementación en desarrollo, lista para revisión funcional y visual; sin aceptación del promotor ni publicación. Comentario anónimo, solicitud con correo, respuesta opcional a comentario, errores por campo, CSRF, confirmación y registro persistente probados. Administración con OTP y permisos; cambio de estado y nota interna comprobados. La notificación local, cuando se configura `CONTACT_NOTIFICATION_EMAIL`, solo contiene tipo e ID; su fallo deja el registro intacto y visible.

- `manage.py test leads core diagnostics`: 52 pruebas correctas. Suite completa: 69 pruebas ejecutadas, 68 correctas y un error en `content.tests.MediaEditorialTests.test_sanitizer_authorized_images_and_protected_reuse`: Windows impide eliminar una imagen temporal aún abierta por la respuesta de archivo de esa prueba anterior de A-05. Se reprodujo en una segunda ejecución y al ejecutar `content` solo; no se modificó A-05/A-06 en este incremento.
- `manage.py check`: sin incidencias; `makemigrations --check --dry-run`: sin cambios pendientes; `git diff --check`: sin errores.
- Chrome sin JavaScript: 1365×900, 369×545 y 390×844; formulario, validación de solicitud sin correo, confirmación, breadcrumb, navegación y primer foco de teclado correctos, sin desplazamiento horizontal. [Escritorio](../qa_artifacts/a07-contact-1365x900.png), [móvil 369](../qa_artifacts/a07-contact-369x545.png), [móvil 390](../qa_artifacts/a07-contact-390x844.png), [error móvil](../qa_artifacts/a07-contact-error-369x545.png), [confirmación](../qa_artifacts/a07-contact-confirmation-1365x900.png), [recorrido](../qa_artifacts/a07_verify.cjs).
- Se retiraron de la base local las dos solicitudes sintéticas generadas para la captura del navegador. No se usaron datos reales.

**Pendientes:** revisión del promotor; O-04 correo productivo y entregabilidad, O-07 límites de envíos/CAPTCHA según riesgo, O-08 medición transversal y revisión jurídica de textos, modalidad de consentimiento y retención antes de usar datos reales. El aviso de `/privacidad/` continúa provisional. La prueba móvil se hizo con viewport, no dispositivo físico.

Actualización: 17 oct 2026. Entorno local Python 3.11.9; Django 5.2.18.

- 28 pruebas Django: PASS (dominio, persistencia y cliente HTTP de prueba).
- Una prueba recorre las 6,561 combinaciones: tres acciones distintas y aplicables, reproducibilidad y elegibilidad.
- Límites de score: 0, 6, 7, 11, 12 y 16 puntos.
- Ejemplos del catálogo: coincidencia exacta.
- Captura antes de resultado, WhatsApp opcional, deduplicación, consentimiento independiente, aislamiento entre clientes, caducidad y salida explícita.
- CSRF y restricción POST; acceso administrativo exige OTP.
- PDF: respuesta válida y reintentos sin nuevo diagnóstico. No prueba guardado en dispositivo.
- `manage.py check`: sin incidencias.
- `makemigrations --check --dry-run`: sin cambios pendientes.
- Catálogo copiado byte a byte del aprobado; SHA-256 en archivo adjunto.
- Chrome 155 en escritorio y Edge 155 en viewport móvil: flujo completo PASS con datos ficticios (inicio, validación, ocho respuestas, captura, resultado, PDF, orientación y salida). Sin desbordamiento horizontal en entrada ni resultado.
- Corregidos el 403 del formulario por `Referrer-Policy: no-referrer` y la lectura de JSON sin UTF-8 explícito en Windows. Capturas y PDF de prueba en `qa_artifacts/`.

No se ejecutó CI remoto, QA visual exhaustivo, carga, restauración ni PostgreSQL real. La prueba móvil usó un viewport de Edge, no un dispositivo físico.
No afirmar conformidad integral WCAG ni cierre de RF-A17. Ver ESTADO.md.

## Entrega 1 — verificación y cierre visual (17 oct 2026)

**Estado:** APROBADA CON SALVEDADES por autorización expresa del promotor tras tres rondas AV-01–AV-29. Alcance aceptado: Home, identidad oficial, encabezado y pie compartidos, navegación pública, páginas estructurales de Fase A, diseño responsivo e ingreso al Check B0. A-01 y H2 permanecen abiertos.

- `manage.py check`: sin incidencias; `manage.py test`: 32 pruebas correctas, incluidas navegación y breadcrumbs. `git diff --check`: sin errores de espacios.
- Chrome local a 100 % (DPR 1): Home, Herramientas, Contenidos, Recursos, Contacto y entrada al Check a 1365×900, 369×545 y 390×844. Sin desbordamiento horizontal ni errores de página; enlaces públicos comprobados con respuesta HTTP 200.
- Encabezado, logotipo y menú con medidas y posiciones idénticas entre las seis páginas a 1365×900. Sección activa indicada con `aria-current`; breadcrumb semántico en páginas interiores y entrada al Check, sin incorporarlo al cuestionario ni al resultado.
- Primer foco de teclado en «Saltar al contenido», foco visible en navegación y enlaces del menú de al menos 42 px de alto. El Check se recorrió con datos ficticios hasta el resultado móvil; mantuvo tres acciones y el ancho del viewport.
- Evidencia: [Home móvil](../qa_artifacts/av3-home-369x545.png), [Herramientas móvil](../qa_artifacts/av3-tools-369x545.png), [Contenidos móvil](../qa_artifacts/av3-content-369x545.png), [Recursos móvil](../qa_artifacts/av3-resources-390x844.png), [Contacto móvil](../qa_artifacts/av3-contact-390x844.png), [Check antes](../qa_artifacts/av2-check-369x545.png), [Check después](../qa_artifacts/av3-check-369x545.png), [resultado Check](../qa_artifacts/av3-check-result-369x545.png).

**Salvedades:** favicon oficial pendiente; instrumentación y verificación de clics principales de A-01 pendientes; prueba en dispositivo móvil físico pendiente de la actividad correspondiente. Esta revisión de viewport no sustituye pruebas en dispositivo físico ni una auditoría integral de accesibilidad. Los contenidos provisionales y funciones de futuras entregas conservan su backlog.

## A-02 — calculadora de punto de equilibrio (19 oct 2026)

**Aceptación del promotor:** implementación funcional y visual **APROBADA CON SALVEDADES**, incluidos A02-AV01–AV08. D-04 continúa aprobada; A-02 y Entrega 2 continúan EN CURSO. Esta aceptación no cierra la instrumentación transversal de O-08.

- `manage.py test`: 44 pruebas correctas, incluidas fórmulas decimales, límites y precisión de los tres campos, margen positivo/cero/negativo, costos fijos cero, unidades enteras, cifras grandes, errores, reenvío e idempotencia de `TOOL_STARTED` y `TOOL_COMPLETED`, y regresión de las pruebas del portal y Check. `manage.py check` y `makemigrations --check --dry-run`: sin incidencias ni migraciones pendientes.
- Caso D-04 `CF=75000, P=1200, CV=650`: 137 unidades, $164,400.00, $550.00 y 45.8 %. Caso AV-08 `CF=65000, P=1200, CV=4500`: «No aplica», «No aplica», -$3,300.00 y -275.0 %. El cálculo es servidor Django con `Decimal`; el formulario opera sin JavaScript y no persiste los importes introducidos.
- Chrome a 1365×900, 369×545 y 390×844, con JavaScript deshabilitado: navegación por teclado y foco visible; validaciones junto a los campos; Limpiar por GET después de error y resultado; cuatro tarjetas por estado; ausencia de desbordamiento horizontal incluso con cifras grandes. Las etiquetas y explicaciones de estados tienen contraste calculado superior a 7:1. [Prueba de validaciones y F5](../qa_artifacts/a02_refine_verify.cjs), [prueba de estados](../qa_artifacts/a02_states_verify.cjs).
- Evidencia comparativa: [positivo escritorio](../qa_artifacts/a02-state-positive-1365x900.png), [cero escritorio](../qa_artifacts/a02-state-zero-1365x900.png), [negativo escritorio](../qa_artifacts/a02-state-negative-1365x900.png); [positivo móvil](../qa_artifacts/a02-state-positive-369x545.png), [cero móvil](../qa_artifacts/a02-state-zero-369x545.png), [negativo móvil](../qa_artifacts/a02-state-negative-369x545.png). [Error móvil](../qa_artifacts/a02-refined-error-369x545.png).

**Salvedades aceptadas:** AV-06: F5 puede reenviar el POST; un token de interacción impide duplicar eventos y la respuesta redirige a un GET con formulario vacío. No se afirma que el navegador evite el reenvío. O-08 debe integrar y verificar los eventos de herramientas dentro de la analítica transversal antes de cerrar A-02. Las capturas móviles usan viewports, no un dispositivo físico; no se declara auditoría integral de accesibilidad ni despliegue productivo.

## A-05/A-06 — blog, editor y videos (20 oct 2026)

**Aceptación:** el promotor aprobó y cerró el alcance funcional y visual local de A-05, A-06 y A05-AV09/10. Confirmó manualmente editor y biblioteca, publicación y retiro de artículos, y reproducción efectiva de un video de YouTube. La aceptación no constituye autorización de producción ni cierra Entrega 2, A-09 u O-03.

- `manage.py test`: **61 pruebas correctas**, con regresión de blog, videos, calculadora y Check PyME. Incluyen estados editoriales, slugs, categorías, enlaces, permisos OTP, imágenes, sanitización, tablas y espacios no separables.
- Recorridos Chrome con base de prueba aislada: editor y biblioteca; tabla Mes/Pedidos/Variación con encabezados y alineación desde edición hasta retiro; tabla de ocho columnas en 369×545 y 390×844 con desplazamiento interno y sin desbordamiento de página. [Editor](../qa_artifacts/a05-table-editor-desktop.png), [vista previa](../qa_artifacts/a05-table-preview-desktop.png), [artículo móvil](../qa_artifacts/a05-table-public-369.png), [tabla ancha móvil](../qa_artifacts/a05-table-wide-369.png).
- `manage.py check`: sin incidencias. `makemigrations --check --dry-run`: sin migraciones pendientes. `git diff --check`: sin errores de espacios.
- Comprobación de la base local después de la revisión: **0 artículos y 0 videos publicados**; un artículo y un video sintéticos se conservaron como borradores, sin borrar su contenido.

**Pendientes independientes:** contenido editorial real aprobado; O-03 para almacenamiento persistente de imágenes en despliegue; controles de staging y publicación de H3/H4. Las capturas móviles son de viewport, no de dispositivo físico. No se realizaron despliegues.
