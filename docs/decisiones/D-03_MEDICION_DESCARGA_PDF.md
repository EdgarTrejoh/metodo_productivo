# D-03 — Medición de la descarga del PDF del Check

**Estado:** aprobada por el promotor del proyecto  
**Fecha de propuesta y aprobación:** 17 de octubre de 2026  
**Evidencia:** autorización expresa del promotor durante la revisión documental del proyecto

## Decisión aprobada

`PDF_DOWNLOADED` se registra cuando el cliente web termina de recibir el PDF, solicita al navegador su descarga y el servidor recibe un acuse válido asociado al intento. El evento representa una **entrega reportada por el cliente**, no una comprobación independiente de almacenamiento en el dispositivo. No certifica que el archivo haya sido guardado, abierto o leído.

El servidor puede validar la integridad y autorización del acuse, pero **no puede verificar independientemente mediante ese acuse** que el navegador recibió todos los bytes. El cliente puede no enviar el acuse o puede reportar incorrectamente su estado. La métrica es operativa, no una certificación forense.

No registrar `PDF_DOWNLOADED` al generar el PDF, enviar la respuesta HTTP, abrir la URL ni pulsar el botón. Ninguno de esos hechos acredita la recepción completa.

### Flujo medible

1. Una **solicitud efectiva y autorizada** de PDF crea un ID de intento asociado al diagnóstico y lo deja en `INICIADO`. Un doble clic accidental mientras la solicitud funcional sigue en curso no crea un segundo intento.
2. El cliente web recibe la respuesta del PDF. Si detecta un error funcional de generación, respuesta, red o cancelación, muestra un mensaje adecuado y permite reintentar **el mismo diagnóstico** dentro del contexto D-02. El error funcional puede llevar el intento a `FALLIDO`.
3. Si el cliente termina de recibir el PDF, solicita al navegador la descarga y envía el ID de intento en un acuse. Solo un acuse válido lleva el intento a `CONFIRMADO`. Esto registra el reporte del cliente; el servidor no comprueba de forma independiente la recepción completa ni el guardado en disco.
4. El primer intento confirmado crea `PDF_DOWNLOADED` **una sola vez por ejecución**. Cada intento, incluidos los reintentos explícitos, se conserva por separado. Repetir un acuse no crea otro evento ni incrementa contadores.
5. Si el acuse no llega, se pierde o falla su envío, la descarga funcional **puede haber ocurrido**. No mostrar un error de descarga exclusivamente por un fallo de telemetría. Tras vencer la ventana de espera, clasificar el intento sin confirmación ni fallo definitivo como `DESCONOCIDO`; no inferir una entrega exitosa ni crear `PDF_DOWNLOADED`.

### Ciclo de vida de los intentos

| Estado | Significado | Transiciones permitidas |
| --- | --- | --- |
| `INICIADO` | Solicitud efectiva de PDF aceptada y asociada a la ejecución autorizada. | A `CONFIRMADO` por acuse válido dentro de vigencia; a `FALLIDO` por error funcional detectado; a `DESCONOCIDO` si vence la ventana sin acuse ni fallo definitivo. |
| `CONFIRMADO` | Acuse válido recibido y registrado. | Terminal; repetir el mismo acuse devuelve el mismo resultado sin otro evento ni contador. |
| `FALLIDO` | Error funcional de entrega detectado. | Terminal; un nuevo intento requiere una nueva solicitud explícita, sin crear otro diagnóstico. |
| `DESCONOCIDO` | Terminó la ventana sin acuse ni fallo definitivo. | Terminal; un acuse tardío no lo convierte retroactivamente en confirmado. |

La **duración de la ventana de espera es un parámetro técnico pendiente de definición en C-05**; no se fija aquí un valor. El intento y su acuse deben permanecer dentro de esa ventana y del contexto autorizado por D-02. Los acuses tardíos, de intentos fallidos o desconocidos se rechazan para efectos de conteo. Si acuse, fallo y vencimiento compiten, una actualización atómica del estado decide una única transición desde `INICIADO`; los demás eventos observan el estado resultante y no duplican métricas. Un reintento explícito posterior es otro intento del mismo diagnóstico. La interfaz evita intentos adicionales por doble clic mientras la solicitud funcional está en curso.

### Validación del acuse

El servidor valida que el intento existe, corresponde al diagnóstico de la ejecución activa, está autorizado por la sesión y el contexto D-02 y sigue vigente cuando recibe su primer acuse. Si ese mismo acuse ya confirmó el intento, responde de forma idempotente sin cambiar estado ni contadores; si el intento terminó en `FALLIDO` o `DESCONOCIDO`, no lo confirma. La aceptación del primer acuse y la creación de `PDF_DOWNLOADED` deben resistir solicitudes concurrentes. Estas comprobaciones protegen la **integridad del registro**, pero no prueban por sí mismas la recepción completa del PDF en el navegador.

El evento es una métrica operativa aproximada. No debe usarse como comprobante legal, de facturación ni como control de las tres descargas de recursos pagados de la Fase B, que tienen reglas separadas.

## Métricas y deduplicación

| Métrica | Unidad | Regla |
| --- | --- | --- |
| Diagnósticos liberados | Diagnóstico único | `DIAGNOSIS_RELEASED`, una vez por ejecución. |
| Intentos de descarga | Intento único | Cada solicitud efectiva y autorizada crea un ID nuevo; un doble clic durante la solicitud no lo hace. |
| Intentos confirmados por acuse | Intento único | Estado `CONFIRMADO` por acuse válido; expresa el reporte del cliente. |
| Diagnósticos únicos con `PDF_DOWNLOADED` | Diagnóstico único | Una vez por ejecución, después del primer intento confirmado. |
| Reintentos | Intento | Intentos explícitos posteriores al primero de la misma ejecución, se confirmen o no. |
| Resultados desconocidos | Intento | Estado `DESCONOCIDO`; no se cuenta como entrega confirmada ni como fallo funcional. |

La **conversión resultado → PDF** usa como denominador los diagnósticos únicos liberados de una misma población y periodo de análisis y como numerador el subconjunto de esos diagnósticos con `PDF_DOWNLOADED` confirmado al corte del reporte. No dividir eventos de periodos o poblaciones distintas.

El modelo actual de `ProductEvent` impone unicidad por tipo y ejecución: sirve para `PDF_DOWNLOADED` único, pero **no** para registrar varios intentos. C-05 deberá incorporar registros independientes de intentos con ID, ejecución, estado y marcas de tiempo. No almacenar datos personales ni contenido del PDF en eventos analíticos. No modificar `ProductEvent` durante esta decisión documental.

## Criterios de aceptación para C-05

- El cliente termina de recibir la respuesta del PDF antes de solicitar su descarga al navegador y enviar el acuse; generar o responder el PDF sin acuse no crea `PDF_DOWNLOADED`.
- Un acuse válido durante la vigencia crea como máximo un `PDF_DOWNLOADED` por ejecución. Acuses duplicados o concurrentes y reintentos del mismo diagnóstico no duplican este evento.
- Dos intentos confirmados de un mismo diagnóstico se cuentan como dos intentos confirmados y un diagnóstico único con `PDF_DOWNLOADED`.
- La ausencia o pérdida del acuse deja el intento en `DESCONOCIDO` al vencer la ventana, aunque la descarga funcional haya podido ocurrir. No se muestra al usuario un error de descarga solo por ese fallo de telemetría.
- Un error funcional detectado deja el intento en `FALLIDO`, muestra un mensaje de descarga y permite un reintento del mismo diagnóstico dentro de D-02; no se confunde con un fallo de acuse.
- Un doble clic accidental mientras la solicitud está en curso produce un solo intento; un reintento explícito posterior produce uno nuevo sin crear diagnóstico adicional.
- Intentos inexistentes, ajenos, expirados o ya cerrados y acuses tardíos o inválidos no producen confirmaciones nuevas. El vencimiento y acuses concurrentes resuelven una sola transición atómica.
- Resultado, PDF, reintentos y acuses requieren la autorización y permanencia del contexto activo D-02.
- El reporte separa diagnósticos liberados, intentos, intentos confirmados, diagnósticos únicos con `PDF_DOWNLOADED`, reintentos y resultados desconocidos; calcula la conversión sobre la misma población y periodo, y aclara que el acuse no prueba guardado en disco.

## Fundamento y límites

- BRD v0.6, evento `PDF_DOWNLOADED`: entrega completada en el recorrido activo; reintentos separados de resultados únicos.
- Arquitectura v0.5, secciones 9 y 12: transmisión controlada y medición sin equiparar URL o redirección con descarga exitosa.
- [Estado B0](../ESTADO.md) y [verificación](../VERIFICACION.md): el PDF actual se genera y puede reintentarse, pero no se registra `PDF_DOWNLOADED` porque generar bytes no acredita recepción.
- [D-02](D-02_CONTEXTO_ACTIVO_CHECK.md): la confirmación y los reintentos solo operan durante el contexto activo aprobado.

**Alcance de la aprobación:** `PDF_DOWNLOADED` representa una entrega **reportada por el cliente** mediante acuse válido; no demuestra almacenamiento ni permite verificar independientemente la recepción completa. La ventana de espera del intento sigue pendiente de definición técnica en C-05. Esta decisión está aprobada, pero la medición aún no está implementada ni verificada; C-05 no se ha iniciado.
