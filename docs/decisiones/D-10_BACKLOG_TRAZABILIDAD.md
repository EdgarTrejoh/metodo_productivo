# D-10 — Historias, dependencias y aceptación trazables de Fase A

**Estado:** APROBADA por el promotor del proyecto  
**Fecha de aprobación:** 17 de octubre de 2026  
**Evidencia:** autorización expresa del promotor para aprobar D-10 e iniciar A-01  
**Responsable de la decisión:** promotor del proyecto

## Propósito y límites

Convertir las decisiones D-01 a D-09 y los requisitos RF-A01–RF-A17 del BRD v0.6 en un backlog verificable para la **plataforma integral de Fase A**: contenidos, educación financiera, herramientas, captación y orientación. El Check PyME es una capacidad central, pero no condiciona por sí solo el inicio de las demás. Los IDs C, A y O existentes son la unidad inicial de trabajo; cada uno se detallará como historia ejecutable antes de su implementación. Una misma historia puede cubrir varios requisitos, y un requisito puede necesitar varias historias. La matriz aprobada es trazabilidad documental, no evidencia de implementación o verificación.

Los hitos **H1, H2 y H3** conservan su alcance y criterios de cierre, pero pueden ejecutarse de forma coordinada y en paralelo cuando las dependencias reales lo permitan. La prioridad de ejecución se revisa transversalmente según valor visible para el usuario, dependencia técnica, riesgo y capacidad disponible, con justificación registrada en el [plan vigente](../PLAN_TRABAJO.md). **A-01 inicia la secuencia aprobada** con identidad visual, design system, Home, navegación, estructura de páginas y diseño responsivo. H4 conserva las condiciones de publicación y H5 su gate; B y C quedan fuera de esta definición. Las estimaciones existentes no se modifican por esta decisión.

## Estrategia incremental aprobada

| Entrega | Resultado verificable | IDs principales | Relación con otros trabajos |
| --- | --- | --- | --- |
| 1. Estructura integral navegable | Portal de Fase A recorrible en desarrollo: Home, encabezado, navegación, pie, identidad, páginas públicas estructuradas y experiencia responsiva. Contenido provisional identificado y funciones aún no disponibles señaladas con claridad. | A-01; estructura de A-02, A-03, A-05, A-07 y A-08 sin dar por terminados esos IDs | Puede comenzar con diseño y sitemap aprobados; el Check B0 existente se integra a la navegación sin esperar el cierre de H1. |
| 2. Capacidades funcionales | Calculadora, lead magnet, blog, videos, contacto y Check avanzan en incrementos verificables por recorrido. | A-02, A-03, A-05, A-06, A-07; C-01–C-15 según dependencia | D-04/D-05 y D-01–D-03/D-06/D-07 rigen cada flujo; el Excel definitivo condiciona la entrega real de A-03. |
| 3. Integración y operación | Formularios, correo, backoffice, analítica, almacenamiento y controles compartidos conectados a los recorridos. | A-04, A-09, C-06–C-10, O-02–O-09, según aplicación | Infraestructura y servicios compartidos pueden prepararse en paralelo y verificarse con cada función; no se declara operativa una integración incompleta. |
| 4. Verificación y publicación | Pruebas, staging, piloto, aceptación y publicación de Fase A; medición posterior del gate. | H3, H4 y H5, con sus IDs O, R y M | Mantiene sus dependencias y evidencias: H4 exige H1–H3 aceptados; H5 se evalúa tras publicación e instrumentación verificada. |

Estas entregas son **cortes de ejecución**, no fases comerciales nuevas ni reemplazos de los hitos. Un mismo ID puede aportar a varios cortes y solo se cierra al cumplir su criterio completo. Se puede revisar el orden de tareas con una justificación de producto registrada, sin reabrir decisiones funcionales aprobadas.

### Aceptación de la Entrega 1

- En el entorno de desarrollo, se puede recorrer desde la Home la estructura pública prevista en el sitemap: entrada al Check, herramientas, recurso gratuito, blog, contacto y páginas institucionales y legales. La navegación y el pie mantienen la jerarquía de Fase A; las rutas privadas del Check y de acceso a recursos conservan su propósito y protección.
- Identidad visual y componentes base aplican la propuesta visual v0.2, con comportamiento responsivo, navegación por teclado, foco visible y lectura clara en móvil y escritorio.
- La Home comunica contenidos, educación financiera, herramientas y orientación disponible a partir del Check. Los llamados a la acción llevan a una función real o indican explícitamente que está pendiente; no se muestran testimonios inventados, formularios falsos ni resultados simulados como reales.
- Cada página estructural tiene propósito y contenido provisional marcado como tal. Las páginas legales provisionales permanecen fuera de publicación hasta cumplir D-06 y R-05; ninguna página vacía o enlace roto se presenta como producto listo.
- Se conserva evidencia revisable: recorrido de enlaces y rutas, capturas en móvil y escritorio, verificación básica con teclado y lista de contenidos/funciones aún pendientes. Esta aceptación **no cierra** A-02, A-03, A-05, A-07, A-08 ni H2.

## Formato aprobado de cada historia

Cada historia, al prepararse para ejecución, registrará: **ID del plan, resultado observable para la persona usuaria u operación, RF y decisión aplicables, dependencia previa, criterio de aceptación, prueba o evidencia esperada y estado**. Si se divide una tarea por tamaño, los subtrabajos conservarán el ID padre y su trazabilidad; dividirla no autoriza una funcionalidad nueva ni cerrar el ID padre sin cumplir todos sus criterios. Las decisiones aprobadas son fuentes normativas; una referencia documental no equivale a código probado.

Para aceptar una historia se requiere evidencia del comportamiento previsto, incluidos errores y límites relevantes del BRD o de su decisión aplicable. La casilla del plan se marca solo conforme a su regla común de terminado. Las tareas técnicas que soporten varias historias, como O-02, O-04 y O-08, se vinculan a todas las que dependen de ellas. Las tareas pueden cambiar de orden de ejecución por una razón documentada; se conservan los RF, decisiones, dependencias indispensables y evidencias de aceptación.

## Matriz aprobada de trazabilidad RF-A01–RF-A17

| Requisito BRD v0.6 | Trabajo existente principal | Decisión o referencia | Aceptación que debe conservarse |
| --- | --- | --- | --- |
| RF-A01 — Home | A-01, A-09, O-08 | BRD, propuesta visual y sitemap | CTA visibles y navegables en móvil y escritorio; medición de los principales. |
| RF-A02 — Calculadora | A-02, O-08 | [D-04](D-04_CALCULADORA_PUNTO_EQUILIBRIO.md) | Cálculo y validaciones sin registro; eventos de inicio y finalización conforme a D-04. |
| RF-A03 — Lead magnet | A-03, O-04, O-08 | [D-05](D-05_PRIMER_LEAD_MAGNET.md) | Lead único por correo, consentimientos por interacción y entrega autorizada con estado correcto. |
| RF-A04 — Check PyME | C-12, C-13, C-14, C-15 | BRD v0.6, Check v1.3 | Ocho respuestas, score y niveles correctos, incluidos cortes 0, 6, 7, 11, 12 y 16; comprensión y prueba de recorrido. |
| RF-A05 — Liberación del diagnóstico | C-02, C-03, C-04, C-11, C-12 | [D-01](D-01_PDF_CHECK.md), [D-03](D-03_MEDICION_DESCARGA_PDF.md), [D-06](D-06_TEXTOS_PRIVACIDAD_CONSENTIMIENTOS.md) | Datos mínimos, resultado y PDF tras captura válida, fallo recuperable sin duplicar diagnóstico y sin correo de acceso. |
| RF-A06 — Blog | A-05, A-10 | BRD y sitemap | Listado, detalle, slug, fecha, categoría, URL única y metadatos SEO previstos. |
| RF-A07 — Videos destacados | A-06 | BRD y sitemap | Reproducción mediante proveedor externo, sin archivo pesado en la aplicación. |
| RF-A08 — Comentarios y solicitudes | A-07, A-09 | BRD y recorridos | Fecha, categoría, contenido, contacto y estado interno registrables. |
| RF-A09 — Consentimientos | C-06, A-03, A-04, O-08 | [D-06](D-06_TEXTOS_PRIVACIDAD_CONSENTIMIENTOS.md) | Finalidades separadas y evidencia de texto, fecha/hora y opción elegida; validación jurídica antes de producción. |
| RF-A10 — Baja comercial | A-04, O-04 | [D-06](D-06_TEXTOS_PRIVACIDAD_CONSENTIMIENTOS.md) | La baja detiene mensajes comerciales y conserva los correos transaccionales necesarios. |
| RF-A11 — Correo transaccional | A-03, A-04, C-10, O-04 | [D-05](D-05_PRIMER_LEAD_MAGNET.md), [D-07](D-07_OPERACION_ORIENTACION.md) | Estados y errores visibles para operación; el Check entrega su informe en pantalla sin depender de correo. |
| RF-A12 — Backoffice mínimo | A-09, O-06 | BRD y arquitectura | Gestión prevista para personal autorizado con MFA; en Fase A basta el rol administrador. |
| RF-A13 — Analítica | O-08, O-09 | [D-03](D-03_MEDICION_DESCARGA_PDF.md), [D-04](D-04_CALCULADORA_PUNTO_EQUILIBRIO.md), [D-08](D-08_MEDICION_GATE_FASE_A.md) | Eventos sin datos sensibles innecesarios; reporte y sesión calificada según D-08, con fuente y exclusiones. |
| RF-A14 — Orientación | C-09, C-10, O-08 | [D-07](D-07_OPERACION_ORIENTACION.md) | Solicitud ligada a lead y diagnóstico, notificación, estados y `ORIENTATION_REQUESTED` sin duplicados. |
| RF-A15 — Recuperación retirada | C-01, C-02, C-13 | [D-02](D-02_CONTEXTO_ACTIVO_CHECK.md) | Control negativo: ningún formulario, enlace, endpoint o búsqueda pública recupera diagnósticos; el ID no se reutiliza. |
| RF-A16 — Catálogo de acciones | C-03, C-13, C-15 | [D-01](D-01_PDF_CHECK.md), [D-09](D-09_GOBIERNO_CATALOGO_ACCIONES.md) | Tres acciones distintas del catálogo aprobado, igualdad pantalla/PDF, versiones y 6,561 combinaciones; históricos inmutables. |
| RF-A17 — Acceso activo y nueva ejecución | C-01, C-02, C-12, C-13 | [D-02](D-02_CONTEXTO_ACTIVO_CHECK.md) | Reintento autorizado del mismo diagnóstico, doble envío idempotente, nueva ejecución tras salir y límites reales del contexto activo. |

Esta matriz no sustituye los criterios completos del BRD, las decisiones aprobadas ni los recorridos J1–J8. La verificación transversal del plan (H4) y el gate de Fase A (H5) se ejecutan después de las capacidades correspondientes; D-10 no los declara cumplidos.

## Dependencias que deben reflejar las historias

- **Check:** C-01/C-02 aplican D-02; C-03 aplica D-01 y D-09; C-05 aplica D-03; C-06 aplica D-06; C-09/C-10 aplican D-07. C-12–C-15 verifican el comportamiento pertinente antes de la aceptación de H1.
- **Capacidades públicas:** A-02 aplica D-04; A-03 aplica D-05 y necesita el Excel definitivo de provisión externa; A-04/A-08 aplican D-06. La revisión jurídica y los datos reales de D-06 son condición de publicación, no de redactar historias o avanzar en diseño.
- **Soportes compartidos:** O-02 respalda las pruebas con PostgreSQL; O-04 las entregas y avisos por correo; O-06 el acceso al backoffice; O-08/O-09 la medición aprobada en D-08. Se preparan en paralelo a los recorridos que los requieren; el orden relativo se ajusta con justificación y sin omitir sus controles.

## Criterios de aceptación de D-10

- Cada RF-A01–RF-A17 tiene un vínculo explícito con trabajo existente y una evidencia esperada; RF-A15 permanece retirado y se prueba como prohibición de recuperación pública.
- Cada historia lista sus decisiones y dependencias antes de desarrollo; ningún criterio contradice BRD v0.6 ni D-01–D-09.
- La secuencia transversal produce primero una estructura integral navegable y después incorpora funciones e integraciones verificables; el inicio de H2 no depende del cierre general de H1.
- Los estados **decidido, implementado y verificado** se mantienen separados en el plan y la evidencia de cierre.
- La aprobación de la matriz, la granularidad y la secuencia cierra D-10; no cierra tareas de H1–H5. Cada incremento requiere su propia evidencia y aceptación.

## Acuerdos aprobados por el promotor

1. **Granularidad:** los IDs C, A y O actuales son las unidades iniciales de trabajo; se permiten subdivisiones trazables al ID original.
2. **Cobertura:** se aprueba la matriz RF-A01–RF-A17, conservando las decisiones y criterios funcionales aprobados.
3. **Secuencia transversal:** A-01 es el primer incremento visible; se aprueban las cuatro entregas y la coordinación de H1, H2 y H3 según dependencias. Cualquier ajuste posterior de orden se motivará en el plan sin alterar alcance aprobado.
4. **Regla de cierre:** una historia y su ID padre solo se marcan terminados con criterios y evidencias aplicables completos, preservando dependencias técnicas y gates de publicación.

**Alcance de la aprobación:** D-10 queda aprobada el 17 de octubre de 2026 y autoriza iniciar A-01 por la Entrega 1. Esta decisión no da por terminada A-01 ni aprueba visualmente la Entrega 1: el promotor revisará experiencia, identidad, estructura y navegación al presentarse la evidencia. Las siguientes entregas requieren su autorización posterior. El posible impacto del paralelismo sobre capacidad y calendario se revisará sin cambiar aquí las estimaciones vigentes.
