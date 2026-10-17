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
