# D-04 — Demostrador gratuito de Fase A y futura herramienta Excel de pago

**Estado:** APROBADA por el promotor del proyecto  
**Fecha de propuesta:** 17 de octubre de 2026  
**Fecha de aprobación:** 17 de octubre de 2026  
**Responsable de la decisión:** promotor del proyecto  
**Evidencia:** autorización expresa del promotor durante la revisión documental del proyecto

## Decisión aprobada

Se aprueba como primera herramienta pública de Fase A un **demostrador web gratuito de punto de equilibrio mensual para un solo producto o servicio**. Estará disponible sin cuenta ni captura de datos personales en `/herramientas/punto-de-equilibrio/`. El resultado se calcula en el servidor; JavaScript podrá mejorar la interacción, pero el formulario deberá funcionar sin él. Su alcance es deliberadamente acotado: muestra la utilidad del método, no entrega el producto Excel completo. El prototipo visual es una referencia de diseño, no una especificación financiera aprobada.

### Relación con la tienda de herramientas Excel

| Entregable | Fase y propósito | Límite |
| --- | --- | --- |
| Demostrador web de punto de equilibrio | Fase A; cumple la calculadora pública sin registro exigida por RF-A02 y atrae visitantes al Check y a recursos relacionados. | Cálculo puntual con tres entradas; sin archivo Excel, pago ni datos personales. |
| Lead magnet | Fase A; recurso gratuito entregado tras la captura y el consentimiento propios de RF-A03. | D-05 decidirá si será una versión inicial de una herramienta Excel, una plantilla distinta u otro recurso. El uso de la calculadora web por sí solo no equivale a la entrega de este lead magnet. |
| Herramienta Excel completa de pago | Fase B; producto digital del futuro catálogo de la sección «Herramientas». | Sus funciones, archivo, precio, condiciones y soporte se definirán en B-01. La compra y entrega seguirán el flujo aprobado de Stripe Checkout, pago confirmado y acceso controlado; no se implementan en Fase A. |

La navegación puede reunir demostradores gratuitos y, cuando se habilite Fase B, productos Excel de pago bajo «Herramientas», distinguiendo claramente qué es muestra y qué es producto. La aprobación de D-04 no aprueba el catálogo pagado ni D-05.

### Entradas

| Campo | Definición | Validación aprobada |
| --- | --- | --- |
| Costos fijos mensuales (`CF`) | Costos mensuales que permanecen relativamente constantes dentro del volumen de operación considerado; por ejemplo, renta, sueldos fijos y servicios contratados. Si el negocio vende varios productos, no necesariamente corresponde atribuir todos sus costos fijos a uno solo. | MXN, de 0 a 999,999,999.99; máximo dos decimales. |
| Precio de venta por unidad (`P`) | Precio efectivamente esperado por una unidad completa del producto o servicio; aplicar descuentos habituales antes de ingresarlo. | MXN, de 0.01 a 999,999,999.99; máximo dos decimales. |
| Costo variable por unidad (`CV`) | Costo directamente asociado a cada unidad vendida: compra o fabricación, empaque, comisiones por venta, entrega y distribución variables u otros costos por unidad. Estos son ejemplos, no campos adicionales. | MXN, de 0 a 999,999,999.99; máximo dos decimales. |

Los tres campos son obligatorios. `CF` corresponde al mes; `P` y `CV` corresponden a una misma unidad de producto o servicio. El modelo considera unidades completas e indivisibles, por lo que no contempla unidades fraccionables, como horas parciales. Los importes se capturan sin impuestos trasladados, con criterios consistentes entre precio y costos. No se solicitan ventas proyectadas, correo, nombre ni información financiera detallada. La herramienta presupone precio y costo variable constantes en el rango considerado; no modela mezcla de productos, capacidad, estacionalidad, impuestos, financiamiento ni cambios escalonados de costos.

**Validación de entrada:** comprobar en el servidor que los tres campos estén presentes, sean numéricos, respeten los rangos indicados y tengan como máximo dos decimales. `P` debe ser estrictamente positivo; `CF` y `CV` deben ser no negativos. La relación entre `CV` y `P` se evalúa después como resultado económico, no como error de captura.

**Evaluación económica:** si `CV < P`, el margen es positivo y se calcula el equilibrio; si `CV = P`, el margen es cero y las ventas no contribuyen a cubrir costos fijos; si `CV > P`, cada unidad vendida aporta una contribución negativa. Los dos últimos casos producen una explicación interpretable, sin unidades ni ingresos de equilibrio engañosos, incluso cuando `CF = 0`.

### Cálculo y resultados

- **Margen de contribución por unidad:** `M = P − CV`.
- **Margen de contribución porcentual:** `M / P × 100`.
- **Equilibrio teórico:** `CF / M`, solo cuando `M > 0`.
- **Unidades enteras mínimas para cubrir costos:** `U = techo(CF / M)`, solo cuando `M > 0`; si además `CF = 0`, `U = 0`.
- **Ingresos con las unidades enteras mínimas:** `I = U × P`, solo cuando `M > 0`. La etiqueta no debe sugerir que `I` es el ingreso teórico exacto cuando hubo redondeo de unidades.

Etiquetar las cuatro salidas principales previstas en la propuesta visual como **unidades mínimas mensuales para cubrir costos**, **ingresos con las unidades mínimas**, **margen de contribución unitario** y **margen de contribución porcentual**. Con margen cero o negativo, mostrar el margen y su porcentaje junto con la explicación económica; las salidas de unidades e ingresos de equilibrio indicarán que no aplican, sin sustituirlas por cero. Explicar que el equilibrio teórico puede contener fracciones, pero las unidades necesarias se redondean **hacia arriba** porque son indivisibles. Calcular con aritmética decimal exacta en el servidor; mostrar montos a dos decimales, porcentaje a un decimal y unidades sin decimales. La gráfica de ingresos y costos es solo apoyo visual: los resultados oficiales son los calculados y presentados por el servidor en texto.

**Ejemplo de comprobación:** `CF = $75,000`, `P = $1,200`, `CV = $650` producen `M = $550`, equilibrio teórico de aproximadamente `136.36` unidades, `U = 137` unidades mínimas, `I = $164,400` y margen porcentual `45.8 %`. Las 137 unidades aportan $75,350 de contribución: un excedente de $350 sobre los $75,000 fijos. Este excedente explica el redondeo del ejemplo y no constituye un quinto indicador principal.

### Mensajes y casos límite

| Caso | Respuesta aprobada |
| --- | --- |
| Campo vacío, no numérico, con más de dos decimales o fuera de rango; `CF` o `CV` negativos | Mensaje específico junto al campo; conservar los otros valores; no mostrar resultados calculados con entradas inválidas. |
| `P = 0` | Precio inválido: se requiere un precio positivo. |
| `CV = P` | «Cada venta cubre solo su costo variable; no queda margen para cubrir costos fijos.» Mostrar margen cero y su porcentaje, pero no unidades o ingresos de equilibrio como `0`, incluso si `CF = 0`. |
| `CV > P` | «Cada venta genera una contribución negativa; no existe un punto de equilibrio con ventas positivas bajo estos valores.» Mostrar el margen negativo y su porcentaje, sin unidades ni ingresos de equilibrio numéricos, incluso si `CF = 0`. |
| `CF = 0` y `M > 0` | Mostrar `0` unidades e ingresos `$0.00`, con nota: no hay costos fijos mensuales que cubrir en este modelo. |
| Resultado entero muy grande, pero dentro de los límites de entrada | Mostrar el valor completo con separadores de miles y una advertencia de que es una estimación bajo supuestos constantes; no truncar ni convertirlo en `0`. |

**Texto de alcance aprobado, visible junto al resultado:** «Esta calculadora ofrece una estimación mensual para un producto o servicio con precio y costo variable unitarios constantes. Ingrese un precio esperado después de sus descuentos habituales y use importes sin impuestos trasladados. La herramienta no modela cambios de descuentos, impuestos, capacidad, mezcla de productos ni todos los costos posibles. Revise sus datos antes de tomar decisiones; el resultado no sustituye un análisis financiero adaptado a su negocio.»

### Experiencia y medición

- Mostrar definiciones breves y ejemplos sencillos de costos fijos y variables para las tres entradas. Indicar «MXN por mes» para `CF` y «MXN por unidad» para `P` y `CV`.
- Enviar el formulario mediante `POST` y mostrar el resultado en la misma página, sin registro. En ausencia de JavaScript, el servidor valida y presenta tanto el resultado como los errores específicos por campo. No colocar importes en parámetros de URL, registros del servidor ni analítica, y no persistir los importes capturados.
- Ofrecer bajo el resultado un CTA contextual al Check PyME y, cuando D-05 esté implementada, un enlace al recurso gratuito correspondiente. La promoción de la herramienta Excel de pago se habilitará al abrir la tienda en Fase B, con una distinción visible respecto del demostrador.
- Registrar `TOOL_STARTED` ante el primer envío efectivo del formulario para solicitar un cálculo, aunque después falle la validación. Abrir la página o enfocar un campo no inicia la herramienta.
- Registrar `TOOL_COMPLETED` cuando el servidor procesa entradas válidas y produce un resultado económico interpretable: equilibrio con margen positivo o explicación con margen cero o negativo. No registrarlo ante validación fallida, solicitud incompleta ni error del servidor.
- Deduplicar ambos eventos por interacción de cálculo: un doble clic, una recarga o un reenvío accidental de la misma interacción no incrementan las métricas; un nuevo envío deliberado constituye otra interacción. El identificador de interacción y los eventos no contienen importes ni datos personales. La definición transversal de sesiones calificadas queda en D-08; D-04 no requiere infraestructura analítica adicional.
- Asegurar operación por teclado, foco visible, errores asociados a cada campo, lectura comprensible del resultado por lectores de pantalla, contraste y presentación correcta en móvil y escritorio, con y sin JavaScript.

## Criterios de aceptación para A-02

1. El servidor exige los tres campos, verifica valores numéricos, rangos y máximo dos decimales, rechaza `P <= 0` y costos negativos, y muestra errores específicos por campo. Si hay validación en cliente, coincide con la del servidor.
2. Con `CV < P`, las fórmulas de margen, equilibrio teórico, techo de unidades e ingresos se calculan en el servidor con aritmética decimal exacta. Se comprueban el ejemplo, el redondeo hacia arriba, límites, precisión decimal y valores grandes sin truncamiento.
3. Con `CV = P` y `CV > P`, el servidor entrega una explicación interpretable, sin unidades ni ingresos de equilibrio numéricos. Se prueban estos casos también con `CF = 0`; con `CF = 0` y margen positivo se muestran cero unidades y cero ingresos con su nota explicativa.
4. El formulario mediante `POST`, la validación, los resultados y los errores funcionan con y sin JavaScript; una falla del servidor no se presenta como resultado completado.
5. Las etiquetas distinguen unidades mínimas mensuales, ingresos asociados, margen unitario y porcentual; explican la diferencia entre equilibrio teórico y unidades enteras. La advertencia de alcance aparece junto al resultado y la gráfica no sustituye los valores textuales.
6. No se capturan datos personales ni se persisten importes; las entradas financieras no aparecen en URL, logs ni eventos analíticos. Se verifica que `TOOL_STARTED` ocurra con el primer envío efectivo, aun si la validación falla, y no al abrir o enfocar la página.
7. `TOOL_COMPLETED` ocurre solo con entradas válidas y resultado económico interpretable, incluso margen cero o negativo; se omite ante entradas inválidas, solicitudes incompletas y errores del servidor. Doble clic, recarga y reenvío accidental no duplican los eventos de la misma interacción; un nuevo cálculo deliberado se registra por separado.
8. La interfaz permite usar teclado y lectores de pantalla, presenta foco y errores asociados, y funciona correctamente en móvil y escritorio. Se mantienen las explicaciones de entradas, unidades MXN y CTA al Check PyME.
9. El alcance gratuito queda identificable como demostrador sin descarga Excel. El lead magnet depende de D-05 y el catálogo Excel de pago, su cobro y entrega pertenecen a Fase B; A-02 no los implementa.

## Fundamento

- BRD v0.6, RF-A02: una calculadora independiente, sin registro, con validación y eventos de inicio/finalización.
- Concepto y alcance v0.8: una calculadora como parte de la Fase A; D-04 cierra la selección que permanecía pendiente en esa versión.
- Sitemap y journeys v0.2, J5: resultado inmediato sin datos personales, cálculo en servidor y uso sin JavaScript.
- Propuesta visual v0.2, pantalla 4: referencia de diseño para punto de equilibrio y cuatro indicadores; D-04 aprueba su alcance funcional y financiero.
- BRD v0.6, RF-A03 y RF-B01–RF-B03: el lead magnet gratuito tiene captura y entrega propias; el catálogo de recursos pagados, Checkout y confirmación de pago pertenecen a Fase B.
- [U.S. Small Business Administration — Break-even point](https://legacy.sba.gov/business-guide/plan-your-business/calculate-your-startup-costs/break-even-point): fórmula de costos fijos divididos entre precio menos costo variable para una unidad de producto o servicio.

**Estado de implementación:** D-04 quedó aprobada el 17 de octubre de 2026, pero A-02 sigue pendiente de implementar y verificar. D-05 decidirá el lead magnet y B-01 definirá el primer producto Excel de pago; ninguna de esas decisiones queda aprobada por D-04.
