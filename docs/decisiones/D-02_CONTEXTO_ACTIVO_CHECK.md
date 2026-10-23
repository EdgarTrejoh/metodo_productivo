# D-02 — Duración e invalidación del contexto activo del Check

**Estado:** aprobada por el promotor del proyecto

**Aprobación original:** 17 de octubre de 2026

**Actualización aprobada:** 23 de octubre de 2026, D02-AV01–AV03

**Evidencia:** autorizaciones expresas del promotor en la conversación de trabajo del proyecto

## Decisión aprobada

Una ejecución del Check pertenece a la sesión del navegador que la inició. El resultado y el PDF son accesibles solo mientras esa ejecución siga activa. El ID del diagnóstico, el correo y la URL por sí solos no conceden acceso.

### Vigencia

- **Inactividad:** el plazo comienza al iniciar el cuestionario y vence exactamente a los 30 minutos desde la última petición válida y autorizada del recorrido del Check. Cada petición válida renueva el plazo; consultar el resultado y reintentar el PDF son actividad válida. El servidor comprueba el vencimiento antes de renovar o permitir acceso. Un contexto vencido no puede reactivarse.
- **Sin límite absoluto:** la actualización D02-AV01 del 23 de octubre sustituyó el máximo original de dos horas. No se usa heartbeat ni temporizador automático para mantener artificialmente activo el contexto.
- **Al vencer:** bloquear resultado, PDF y orientación con una pantalla de expiración; conservar el diagnóstico interno conforme a la política de retención, sin habilitar recuperación pública. Para obtener otro informe, iniciar y contestar un nuevo Check.
- Las peticiones inválidas, no autorizadas, la entrada pública al Check y la consulta de `/privacidad/` no renuevan el plazo.

### Acciones y navegación

| Situación | Regla aprobada |
| --- | --- |
| Recargar la página de resultado o reintentar el PDF | Permitido dentro de la vigencia y de la misma sesión; no genera otro diagnóstico. |
| Usar «Atrás» tras completar el Check | No permite cambiar respuestas de un diagnóstico ya emitido; las rutas de preguntas redirigen al resultado activo. Tras salir o vencer, el historial no debe mostrar contenido sensible cacheado. |
| Pulsar «Salir» | Revocación inmediata en el servidor para todas las pestañas que comparten esa sesión. |
| Consultar `/privacidad/` | No revoca ni renueva el contexto; al volver solo continúa si todavía está vigente. |
| Navegar a otra página del portal, excepto `/privacidad/` | Revocación inmediata cuando el servidor recibe esa navegación; volver al Check exige una ejecución nueva. |
| Iniciar otro Check en la misma sesión, incluso desde otra pestaña | La nueva ejecución reemplaza e invalida el contexto anterior. Los formularios de la ejecución anterior se rechazan sin modificar, completar ni revocar la nueva. |
| Abrir la URL del resultado en otra pestaña del mismo navegador | Mientras la sesión y la ejecución estén activas, se puede ver el mismo resultado. La pestaña no crea un permiso independiente; salir o vencer revoca ambas. Esta conducta debe probarse y explicarse como acceso de la misma sesión. |
| Abrir la URL en otro navegador o dispositivo | Denegado por no compartir la sesión autorizada. |
| Cerrar la pestaña, navegar a un sitio externo o perder conexión | La revocación inmediata no se puede garantizar porque el servidor puede no recibir aviso. El acceso remanente termina por inactividad; cerrar el navegador también debe expirar la cookie de sesión en condiciones normales. |

No se prometerá «revocación instantánea al cerrar la pestaña». Si el negocio exige esa garantía, RF-A17 necesitará un criterio distinto, ya que un navegador no proporciona al servidor una señal de cierre infalible. Tampoco se usará un evento de navegador como único control de acceso.

## Criterios de aceptación para C-01 y C-02

1. El servidor comprueba sesión, ejecución y vencimiento por inactividad antes de renovar o permitir cada acceso protegido del Check; no existe vencimiento absoluto.
2. Resultado y PDF usan `Cache-Control: no-store`; tras salir o vencer, las rutas devuelven expiración y el historial no restaura contenido sensible desde caché.
3. Recarga y reintentos durante la vigencia mantienen el mismo diagnóstico; un inicio nuevo crea una ejecución distinta.
4. Salida explícita y navegación interna distinta de `/privacidad/` revocan el contexto compartido por todas las pestañas. Abrir el aviso no lo renueva; regresar tras vencer no lo recupera.
5. Se prueba el límite exacto de 30 minutos desde la última actividad válida, la continuidad más allá de dos horas con actividad legítima, relojes simulados, errores y solicitudes concurrentes pertinentes.
6. Formularios antiguos de preguntas, captura, orientación y salida se rechazan sin afectar la ejecución nueva; se prueban pestañas múltiples y navegadores separados.
7. Los textos de pantalla describen la posibilidad de reintento durante el recorrido y la necesidad de repetir el Check al salir; no prometen detectar un cierre externo inmediato.

## Fundamento

- Arquitectura v0.5, sección 9.1: autorización por contexto activo y reconocimiento del límite de detección de cierre, salida externa o pérdida de conexión.
- BRD v0.6, RF-A17: reintentos dentro del recorrido, nueva ejecución tras salir y ausencia de recuperación por ID o correo.
- [Estado B0](../ESTADO.md): la caducidad provisional de 30 minutos desde el inicio correspondía a la implementación anterior; no cerraba RF-A17.

## Trazabilidad de la actualización del 23 de octubre de 2026

La decisión original del 17 de octubre aprobó **30 minutos de inactividad más un máximo absoluto de dos horas**, revocación al visitar cualquier otra página del portal y sustitución de la ejecución anterior al iniciar otra. D02-AV01 **sustituye** exclusivamente el máximo absoluto por la vigencia renovable de 30 minutos; evita cortar una consulta legítima del resultado o un reintento de PDF por el mero tiempo transcurrido desde el inicio. D02-AV02 **exceptúa** `/privacidad/` de la revocación general para permitir consultar el aviso sin perder el recorrido, sin ampliar su vigencia. D02-AV03 **precisa** que los formularios abiertos antes de iniciar una ejecución nueva no pueden actuar sobre ella. Se conservan las demás protecciones originales, la ausencia de cuentas públicas y la imposibilidad técnica de detectar infaliblemente el cierre externo de una pestaña.

**Alcance de la aprobación actualizada:** el promotor aprobó expresamente D02-AV01–AV03 el 23 de octubre de 2026 y aceptó después la implementación funcional local de C-01. Su cierre integral sigue pendiente de verificar solicitudes verdaderamente concurrentes en PostgreSQL; C-02 conserva su actividad independiente.
