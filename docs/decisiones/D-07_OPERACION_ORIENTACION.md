# D-07 — Operación de solicitudes de orientación

**Estado:** APROBADA — Alcance funcional  
**Fecha de propuesta:** 17 de octubre de 2026  
**Fecha de aprobación funcional:** 17 de octubre de 2026  
**Responsable de la decisión:** promotor del proyecto  
**Evidencia:** autorización expresa del promotor durante la revisión documental del proyecto

## Propósito y límites

D-07 aprueba el flujo funcional de solicitudes de orientación del Check PyME y su seguimiento básico, conforme a RF-A14 y J3, sin convertir la Fase A en un CRM completo. La persona responsable concreta, los horarios y el objetivo de primera respuesta quedan como **configuración operativa pendiente antes de habilitar la atención pública**. No se publica un compromiso de respuesta hasta que esos datos estén definidos.

Se conservan las reglas ya documentadas: la persona solicita orientación **expresamente desde la pantalla de resultado completo** y dentro del contexto activo aprobado en D-02. El sistema usa nombre, correo, empresa y WhatsApp solo si fue proporcionado y corresponde al seguimiento autorizado; no exige volver a capturarlos. La solicitud no suscribe a comunicaciones comerciales ni habilita recuperación pública del diagnóstico. D-06 conserva la separación de finalidades y la validación de textos previa a publicación.

## Flujo funcional aprobado

1. En el resultado activo, la persona selecciona «Solicitar orientación». **El botón es suficiente:** no se agrega campo de descripción, archivos ni información adicional. Se reutilizan los datos de contacto y diagnóstico existentes.
2. La acción explícita registra la solicitud ligada al lead y al diagnóstico, con estado `nuevo`, y muestra confirmación. Solo puede existir **una solicitud abierta por diagnóstico**: si ya hay una en `nuevo` o `contactado`, un doble clic o reenvío no crea otra solicitud ni repite `ORIENTATION_REQUESTED`.
3. La solicitud registrada queda visible para el personal autorizado en el backoffice y se intenta la notificación interna. `ORIENTATION_REQUESTED` se emite al registrar una solicitud nueva; el envío del aviso interno es un hecho operativo separado.
4. La persona que se designe consulta las solicitudes y realiza el seguimiento por **correo electrónico como canal principal**. WhatsApp es alternativa solo cuando fue proporcionado y su uso está autorizado para esta finalidad. La primera respuesta cambia el estado a `contactado`; el cierre del seguimiento lo cambia a `cerrado`. Las acciones y fechas necesarias para operar estos estados se registran sin agregar etapas de CRM.
5. Si falla la notificación interna, la solicitud permanece registrada y visible en el backoffice; se registra `EMAIL_FAILED` conforme a J3 para que operación detecte el fallo. No se informa al visitante que el mensaje interno fue enviado si no hay evidencia de ello, ni se pierde la solicitud.

| Estado | Significado operativo aprobado | Siguiente paso |
| --- | --- | --- |
| `nuevo` | Solicitud recibida, pendiente de primera atención. | La persona responsable realiza el primer contacto y registra el avance. |
| `contactado` | Se efectuó el primer contacto por el canal autorizado. | Continuar el seguimiento hasta cerrarlo. |
| `cerrado` | El seguimiento terminó y se registra su cierre. | Sin nuevas etapas automáticas. |

### Atención fuera de horario y fallos

La solicitud se registra y confirma aunque llegue fuera del horario que se establezca; permanece `nuevo` para atención en el siguiente periodo operativo. El objetivo de primera respuesta y la forma de expresarlo a la persona se fijarán **después** de configurar horario y responsable. No prometer respuesta inmediata ni un número de horas aún no decidido. La falla del correo interno no cambia el estado a `contactado`, no invalida la solicitud ni elimina la tarea visible en backoffice.

La agrupación de envíos por **24 horas** que J3 mencionaba como propuesta **no se adopta**. La regla aprobada es una sola solicitud abierta por diagnóstico y la idempotencia de reenvíos de la misma operación, sin ventana temporal adicional.

## Configuración operativa pendiente antes de habilitar la atención pública

| Dato pendiente | Definición requerida |
| --- | --- |
| Responsable de recibir y atender | Designar persona o rol concreto con acceso al backoffice y recepción de la notificación interna. |
| Horario | Definir días, franja horaria y zona horaria de atención. |
| Objetivo de primera respuesta | Definir el plazo y desde qué momento se cuenta para solicitudes dentro y fuera de horario. Sin este dato no se publica una promesa de atención. |

## Criterios de aceptación para C-09 y C-10

- Solo una persona con contexto activo D-02 puede solicitar orientación para su diagnóstico; la acción explícita usa los datos existentes y no crea una suscripción comercial.
- La solicitud nueva queda vinculada al lead y diagnóstico, visible en backoffice con estado `nuevo`, y genera `ORIENTATION_REQUESTED` una vez. No coexisten dos solicitudes abiertas para un diagnóstico; doble clic y reenvíos de una solicitud abierta no duplican la solicitud ni el evento.
- El personal autorizado puede registrar el primer contacto y cierre mediante `nuevo → contactado → cerrado`; se conserva evidencia operativa mínima de quién y cuándo efectuó el cambio.
- Se intenta la notificación interna. Si falla, la solicitud sigue visible y se registra `EMAIL_FAILED`; el fallo no se presenta como una solicitud perdida.
- Se verifica que el botón funciona sin descripción, adjuntos ni nueva captura de contacto.
- Se verifica el tratamiento de solicitudes fuera de horario conforme al horario y plazo que se configuren antes de habilitar la atención pública, sin comunicar un compromiso distinto.
- El correo electrónico es el canal principal; WhatsApp solo se usa como alternativa si fue proporcionado y su uso corresponde al seguimiento autorizado.

## Fundamento y dependencias

- [PLAN_TRABAJO.md](../PLAN_TRABAJO.md), D-07 y C-09/C-10: designar operación y completar solicitud, notificación y seguimiento.
- BRD v0.6, RF-A14: reutilizar contacto capturado, solicitud ligada al lead y diagnóstico, notificación interna, estados `nuevo`, `contactado`, `cerrado` y `ORIENTATION_REQUESTED`.
- Sitemap y journeys v0.2, J3: solicitud desde resultado, backoffice y `EMAIL_FAILED` ante fallo interno. Su propuesta de agrupación de 24 horas no se adopta en D-07.
- [D-02](D-02_CONTEXTO_ACTIVO_CHECK.md): acceso solo durante contexto activo, sin recuperación pública del diagnóstico.
- [D-06](D-06_TEXTOS_PRIVACIDAD_CONSENTIMIENTOS.md): orientación por solicitud expresa, finalidad separada del marketing y textos publicables sujetos a validación jurídica.
- Concepto y alcance v0.8: orientación solicitada con seguimiento manual en Fase A.

**Estado de implementación:** D-07 quedó aprobada en su alcance funcional el 17 de octubre de 2026. C-09 y C-10 siguen pendientes de implementación y verificación. Antes de habilitar la atención pública deben configurarse responsable concreto, horario y objetivo de primera respuesta; no se publican compromisos de atención sin ellos. La aprobación funcional no implica que el servicio de orientación esté habilitado.
