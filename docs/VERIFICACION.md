# Verificación local - B0

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
