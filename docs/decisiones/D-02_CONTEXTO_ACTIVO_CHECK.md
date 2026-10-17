# D-02 — Duración e invalidación del contexto activo del Check

**Estado:** aprobada por el promotor del proyecto  
**Fecha de propuesta y aprobación:** 17 de octubre de 2026  
**Evidencia:** aprobación expresa de la redacción D-02 en la conversación de trabajo del proyecto

## Decisión aprobada

Una ejecución del Check pertenece a la sesión del navegador que la inició. El resultado y el PDF son accesibles solo mientras esa ejecución siga activa. El ID del diagnóstico, el correo y la URL por sí solos no conceden acceso.

### Vigencia

- **Inactividad:** vencer el contexto después de 30 minutos sin una petición válida del recorrido del Check. Cada petición válida renueva este plazo.
- **Límite absoluto:** vencer el contexto 2 horas después de iniciar el cuestionario, aunque haya actividad. El vencimiento se comprueba en el servidor en cada acceso al Check.
- **Al vencer:** bloquear resultado, PDF y orientación con una pantalla de expiración; conservar el diagnóstico interno conforme a la política de retención, sin habilitar recuperación pública. Para obtener otro informe, iniciar y contestar un nuevo Check.
- Los valores actuales de 30 minutos desde el inicio son provisionales y no implementan esta regla de inactividad más límite absoluto.

### Acciones y navegación

| Situación | Regla aprobada |
| --- | --- |
| Recargar la página de resultado o reintentar el PDF | Permitido dentro de la vigencia y de la misma sesión; no genera otro diagnóstico. |
| Usar «Atrás» tras completar el Check | No permite cambiar respuestas de un diagnóstico ya emitido; las rutas de preguntas redirigen al resultado activo. Tras salir o vencer, el historial no debe mostrar contenido sensible cacheado. |
| Pulsar «Salir» | Revocación inmediata en el servidor para todas las pestañas que comparten esa sesión. |
| Navegar a otra página del portal | Revocación inmediata cuando el servidor recibe esa navegación; volver al Check exige una ejecución nueva. |
| Iniciar otro Check en la misma sesión, incluso desde otra pestaña | La nueva ejecución reemplaza e invalida el contexto anterior. |
| Abrir la URL del resultado en otra pestaña del mismo navegador | Mientras la sesión y la ejecución estén activas, se puede ver el mismo resultado. La pestaña no crea un permiso independiente; salir o vencer revoca ambas. Esta conducta debe probarse y explicarse como acceso de la misma sesión. |
| Abrir la URL en otro navegador o dispositivo | Denegado por no compartir la sesión autorizada. |
| Cerrar la pestaña, navegar a un sitio externo o perder conexión | La revocación inmediata no se puede garantizar porque el servidor puede no recibir aviso. El acceso remanente termina por inactividad o límite absoluto; cerrar el navegador también debe expirar la cookie de sesión en condiciones normales. |

No se prometerá «revocación instantánea al cerrar la pestaña». Si el negocio exige esa garantía, RF-A17 necesitará un criterio distinto, ya que un navegador no proporciona al servidor una señal de cierre infalible. Tampoco se usará un evento de navegador como único control de acceso.

## Criterios de aceptación para C-01 y C-02

1. El servidor comprueba sesión, ejecución, vencimiento por inactividad y límite absoluto en cada ruta del Check que lee o modifica información.
2. Resultado y PDF usan `Cache-Control: no-store`; tras salir o vencer, las rutas devuelven expiración y el historial no restaura contenido sensible desde caché.
3. Recarga y reintentos durante la vigencia mantienen el mismo diagnóstico; un inicio nuevo crea una ejecución distinta.
4. Salida explícita y navegación interna revocan el contexto compartido por todas las pestañas; se prueban pestañas múltiples y navegadores separados.
5. Se prueban los límites exactos de 30 minutos de inactividad y 2 horas absolutas, además de relojes simulados, errores y solicitudes concurrentes.
6. Los textos de pantalla describen la posibilidad de reintento durante el recorrido y la necesidad de repetir el Check al salir; no prometen detectar un cierre externo inmediato.

## Fundamento

- Arquitectura v0.5, sección 9.1: autorización por contexto activo y reconocimiento del límite de detección de cierre, salida externa o pérdida de conexión.
- BRD v0.6, RF-A17: reintentos dentro del recorrido, nueva ejecución tras salir y ausencia de recuperación por ID o correo.
- [Estado B0](../ESTADO.md): la caducidad actual de 30 minutos desde el inicio es provisional y no cierra RF-A17.

**Alcance de la aprobación:** se aceptan los plazos de 30 minutos de inactividad y 2 horas absolutas, el acceso compartido entre pestañas de la misma sesión y la limitación técnica del cierre de pestaña. La implementación y sus pruebas corresponden a C-01 y C-02.
