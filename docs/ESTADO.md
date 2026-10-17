# Bloque inicial B0 - 16 oct 2026

Fuente: Concepto v0.8, BRD v0.6, arquitectura v0.5, Check v1.3 y catálogo v0.1.
Implementación local de desarrollo. No equivale a Fase A terminada ni autorizada para producción.

## Implementado
- Django SSR; configuración PostgreSQL y SQLite para prueba local sin infraestructura.
- Cuestionario de ocho preguntas, sin respuestas implícitas; validación servidor.
- Captura nombre/correo/empresa; WhatsApp opcional; consentimiento comercial separado.
- Resultado solo tras persistencia; selección determinista, versión y snapshot inmutable de informe/contacto.
- PDF generado desde el snapshot, orientación idempotente, lead único y registro de eventos críticos.
- Admin con requisito OTP; sin credenciales predeterminadas.
- Acceso por sesión y ejecución, sin IDs como credenciales ni recuperación por correo.
- Caducidad provisional de 30 minutos desde inicio, configurable SOLO para desarrollo. No es una decisión de negocio aprobada.
- Salida explícita o visita a otra ruta del portal invalida contexto. Cabeceras no-store.

## Límites y siguiente bloque
- RF-A17 NO cerrado: recarga conserva contexto; cerrar pestaña/navegar fuera no se detecta de forma infalible. No afirmar invalidación inmediata. Definir ciclo de vida antes de producción.
- Retención: fecha de 12 meses calculada; faltan borrado/anonimización, tratamiento de leads compartidos, backups y verificación legal.
- Avisos legales son textos de prueba; correo exclusivamente en memoria. Orientación registra solicitud, no envía notificaciones.
- PDF funcional provisional: no reproduce todavía la maqueta editorial ni incluye todas las respuestas textuales. Aceptación PDF/pantalla pendiente.
- Falta rate limiting compartido, CAPTCHA, recuperación de errores operativos y revisión integral de accesibilidad y diseño. El 17 oct se verificó el flujo en Chrome escritorio y Edge con viewport móvil; no equivale a QA visual exhaustivo.
- PostgreSQL/concurrencia se configuraron pero NO se verificaron en servidor real; SQLite no prueba locks de PostgreSQL.
- Sin calculadora, blog, lead magnet, métricas de sesiones calificadas, recursos pagados ni infraestructura GCP.
- No registrar PDF_DOWNLOADED por generar una respuesta: no prueba recepción completa.
- Compras de Fase B conservan 14 días y hasta tres descargas exitosas; no se implementaron ni alteraron.

## Propuesta de siguiente bloque B1
Cerrar contexto temporal y textos de captura; implementar ciclo de vida, pruebas reales con PostgreSQL y fallos; PDF final, notificación y atención de orientación; rate limiting y automatización de retención. Después núcleo editorial y lead magnet.
