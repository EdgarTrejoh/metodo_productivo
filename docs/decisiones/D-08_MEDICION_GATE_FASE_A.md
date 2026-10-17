# D-08 — Medición de sesiones calificadas y gate de Fase A

**Estado:** APROBADA por el promotor del proyecto  
**Fecha de propuesta:** 17 de octubre de 2026  
**Fecha de aprobación:** 17 de octubre de 2026  
**Responsable de la decisión:** promotor del proyecto  
**Evidencia:** autorización expresa del promotor durante la revisión documental del proyecto

## Propósito

D-08 define una medición comparable del gate de Fase A: población, fuentes, exclusiones, deduplicación y periodo. Los umbrales del BRD v0.6 y del concepto v0.8 se conservan íntegros como **hipótesis iniciales de validación**, no metas comerciales definitivas. Su aprobación documental no acredita instrumentación verificada ni autoriza por sí sola avanzar a Fase B.

### Umbrales ya documentados

| Indicador del gate A | Umbral inicial documentado | Fuente funcional |
| --- | --- | --- |
| Sesiones calificadas acumuladas | Al menos 500 | Sesiones y eventos de páginas/herramientas. |
| Tasa de captación de leads por sesión calificada | Al menos 5 % | Leads nuevos únicos / sesiones calificadas; no equivale a conversión de visitantes únicos. |
| Finalización del Check entre quienes lo inician | Al menos 40 % | `CHECK_STARTED` y `CHECK_COMPLETED`. |
| Diagnósticos liberados | Al menos 15 | `DIAGNOSIS_RELEASED`, una vez por diagnóstico. |
| Solicitudes de orientación | Al menos 3 | Solicitudes aceptadas y `ORIENTATION_REQUESTED`, sin duplicados. |
| Datos y seguridad | Sin incidentes graves | Revisión del periodo, además de los conteos. |

El gate requiere un reporte con periodo, fuentes, exclusiones, resultados y decisión expresa del promotor: **avanzar, iterar Fase A o ampliar la muestra**, conforme a H5. Alcanzar los indicadores no autoriza automáticamente Fase B. No inferir éxito o fracaso de producto a partir de tráfico no calificado o datos incompletos.

## Fuentes y unidad de conteo aprobadas

- **Sesiones calificadas:** usar eventos de analítica de páginas públicas y herramientas, asociados a un identificador técnico de sesión. Una sesión califica con **al menos dos vistas de páginas distintas mediante navegación efectiva**, sin contar recargas accidentales, o con **una interacción real con una herramienta**. Utilizar eventos ya definidos que acrediten uso efectivo, como `TOOL_STARTED` del demostrador D-04 y `CHECK_STARTED` al iniciar efectivamente el Check; abrir una página, enfocarla o ver un campo no cuenta como interacción de herramienta. Excluir bots identificados, tráfico interno y pruebas.
- **Leads:** obtener altas únicas de la base transaccional, conforme a RN-015 y `LEAD_CREATED`. Un mismo correo normalizado cuenta como un lead, aunque tenga varias interacciones, consentimientos o diagnósticos. No incluir actualizaciones como altas nuevas.
- **Check:** contar ejecuciones únicas iniciadas y completadas; `CHECK_COMPLETED` significa fin de las ocho preguntas, no liberación del informe. `CHECK_CONTACT_SUBMITTED` y `DIAGNOSIS_RELEASED` miden pasos posteriores y no sustituyen el numerador de finalización.
- **Diagnósticos y orientación:** contar diagnósticos únicos liberados y solicitudes de orientación nuevas aceptadas. Reintentos técnicos, doble clic y eventos repetidos no incrementan el conteo; el seguimiento `nuevo → contactado → cerrado` no crea otra solicitud. La solicitud se rige por D-07.
- **PDF y lead magnet:** sus eventos sirven para análisis de recorrido, pero no reemplazan los indicadores del gate. `PDF_DOWNLOADED` sigue D-03 y `LEADMAGNET_DELIVERED` sigue D-05; no mezclar intentos, entregas y entidades únicas.

Las sesiones provienen de analítica; leads, diagnósticos y solicitudes provienen de registros transaccionales, según arquitectura v0.5. Los eventos deben permitir distinguir origen, paso y resultado sin incluir correos, respuestas, importes, secretos ni contenido de diagnósticos en analítica. El reporte explicará cualquier diferencia entre ambas fuentes; un evento perdido no se reconstruye suponiendo una conversión exitosa. No se incorpora un sistema sofisticado de identificación de personas o bots para esta medición.

## Exclusiones y deduplicación

| Aspecto | Regla aprobada |
| --- | --- |
| Tráfico excluido | Bots identificados, personal interno y pruebas quedan fuera de la población del gate. Los pilotos anteriores a la liberación pública se excluyen y reportan por separado. Documentar los criterios aplicados, datos faltantes y discrepancias entre fuentes, sin requerir datos personales innecesarios. |
| Sesión | Una sesión calificada cuenta una vez aunque tenga múltiples vistas o interacciones. Solo cuentan dos páginas distintas vistas mediante navegación efectiva o interacción real con herramienta; recargas accidentales y eventos duplicados no agregan calificaciones. |
| Lead | Un correo normalizado cuenta una vez como lead nuevo; solicitudes y diagnósticos posteriores no generan otro `LEAD_CREATED`. |
| Check | Una ejecución cuenta una vez en inicio y, si corresponde, una vez en finalización. Separar las ejecuciones de un mismo lead. |
| Diagnóstico y orientación | Un diagnóstico liberado cuenta una vez. Cada solicitud nueva aceptada cuenta una vez, sin duplicar la solicitud abierta por diagnóstico aprobada en D-07. |

No utilizar el correo como identificador de sesión pública. La deduplicación de eventos técnicos y las reglas de privacidad se resolverán al instrumentar O-08; D-08 no prescribe un proveedor ni infraestructura adicional.

## Inicio, corte y fórmulas aprobados

La medición válida comienza **con la liberación pública de Fase A**, después de verificar la instrumentación. Se excluyen pruebas internas y pilotos anteriores, que se reportan por separado. La muestra se mide de forma **acumulada** y la primera evaluación formal ocurre al alcanzar **500 sesiones calificadas**. Cada reporte indica fechas, población, fuentes y exclusiones aplicadas.

Para el corte de evaluación, una ejecución del Check iniciada antes de alcanzarlo puede concluirse y contabilizarse en su cohorte de inicio, incluso si su finalización o liberación ocurre después del corte, siempre dentro del contexto autorizado de D-02: **30 minutos de inactividad renovables mediante peticiones válidas y límite absoluto de 2 horas desde el inicio**. Las ejecuciones nuevas después del corte pertenecen al siguiente periodo. No se extiende la vigencia del Check para completar métricas.

| Tasa | Fórmula aprobada | Límite de interpretación |
| --- | --- | --- |
| Finalización del Check | Ejecuciones únicas con `CHECK_COMPLETED` / ejecuciones únicas con `CHECK_STARTED` en una misma cohorte de inicio. | Permitir concluir ejecuciones previas al corte solo dentro de la vigencia D-02; señalar eventos faltantes. |
| **Tasa de captación de leads por sesión calificada** | Leads nuevos únicos / sesiones calificadas de la población y corte correspondientes. | Conserva el umbral inicial del **5 %** del BRD, pero no mide visitantes únicos. Un lead puede originarse en una sesión anterior o distinta a la sesión calificada; reportar esas limitaciones de atribución y no inferir correspondencia individual perfecta entre fuentes. |

La conversión resultado → PDF definida en D-03 puede informarse aparte, usando diagnósticos únicos con entrega confirmada sobre diagnósticos liberados de la misma población y periodo; no es umbral del gate A. Los umbrales de Fase B y las tres descargas de compras pagadas no intervienen en D-08.

## Reglas de lectura del reporte

1. Registrar cuándo se verificó la instrumentación y comenzó la liberación pública; distinguir en el reporte los pilotos y pruebas excluidos.
2. Mostrar la primera evaluación al alcanzar 500 sesiones calificadas y el tratamiento de ejecuciones del Check abiertas antes de ese corte, sin superar la vigencia D-02.
3. Identificar los filtros de bots, tráfico interno y pruebas, así como datos faltantes o discrepancias. No rellenar faltantes con supuestos de éxito ni ocultar limitaciones de atribución.
4. Presentar cada indicador junto a su fuente, unidad de conteo, denominador y periodo. El resultado del gate requiere decisión expresa del promotor, aun cuando todos los umbrales se cumplan.

## Criterios de aceptación para la futura implementación

- O-08 instrumenta los eventos necesarios sin datos sensibles innecesarios; O-09 presenta periodo, población, exclusiones y fuentes. Ninguna de estas actividades se inicia por D-08.
- El reporte permite reproducir sesiones calificadas, leads únicos, ejecuciones iniciadas/completadas, diagnósticos únicos y solicitudes nuevas, con deduplicación verificable.
- Las tasas usan denominador explícito y población comparable; los datos faltantes se señalan, no se tratan automáticamente como cero o éxito.
- H5 aplica los umbrales iniciales del BRD con revisión de incidentes y documenta la decisión del promotor entre avanzar, iterar Fase A o ampliar la muestra. La medición no sustituye esa decisión.

## Fundamento y dependencias

- [PLAN_TRABAJO.md](../PLAN_TRABAJO.md), D-08, O-08/O-09 y H5: definición documental antes de instrumentación y evaluación del gate.
- BRD v0.6, RN-015, RF-A13, secciones 13 y 14: lead único, sesión calificada, eventos y umbrales de Fase A.
- Concepto y alcance v0.8, sección 17: muestra y señales iniciales; tráfico no calificado no implica fracaso del producto.
- Sitemap y journeys v0.2, sección 4 y J1/J3/J5: etapas del embudo y separación de inicio, finalización, captura y resultado.
- Arquitectura v0.5, analítica: sesiones desde eventos, entidades de negocio desde PostgreSQL y eventos críticos auditables internamente.
- [D-03](D-03_MEDICION_DESCARGA_PDF.md), [D-04](D-04_CALCULADORA_PUNTO_EQUILIBRIO.md), [D-05](D-05_PRIMER_LEAD_MAGNET.md) y [D-07](D-07_OPERACION_ORIENTACION.md): semántica de eventos y deduplicación ya aprobadas para cada recorrido.

**Estado de implementación:** D-08 quedó aprobada el 17 de octubre de 2026. O-08 y O-09 permanecen pendientes de implementación y verificación; H5 aún no se ha evaluado. La decisión aprobada no acredita instrumentación operativa ni autoriza avanzar automáticamente a Fase B.
