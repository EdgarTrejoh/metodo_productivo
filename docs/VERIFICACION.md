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
