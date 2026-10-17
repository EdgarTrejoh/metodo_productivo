# D-09 — Responsable editorial y gobierno del catálogo de acciones del Check PyME

**Estado:** APROBADA por el promotor del proyecto  
**Fecha de aprobación:** 17 de octubre de 2026  
**Evidencia:** autorización expresa del promotor durante la revisión documental del proyecto  
**Responsable editorial y autoridad de aprobación:** promotor del proyecto

## Propósito y base aprobada

Definir quién custodia editorialmente el catálogo de acciones del Check PyME y cómo se proponen, revisan, versionan y aprueban cambios futuros. D-09 no reabre el contenido del **Catálogo de acciones v0.1** ni la **regla de selección v0.1**, aprobados e incorporados por referencia en BRD v0.6. El Check v1.3 cambió captura y entrega, no esas reglas.

Los anexos [Word](../producto/check-pyme/Catalogo_Acciones_Check_PyME_v0_1.docx) y [JSON](../producto/check-pyme/Catalogo_Acciones_Check_PyME_v0_1.json) contienen las mismas 72 acciones y evidencias sugeridas, con ID, dimensión, puntuación aplicable, orden y versión. El Word permite revisión editorial y el JSON alimenta la implementación. Si divergen, no publicar esa versión hasta homologarlos. La selección de tres acciones es determinista y no usa IA en Fase A.

## Gobierno y flujo editorial aprobados

1. El **promotor del proyecto** es responsable editorial: recibe las propuestas de cambio con motivo, texto actual, texto propuesto e IDs afectados. Puede delegar esta labor en el futuro mediante una designación trazable; la delegación editorial no transfiere la autoridad de aprobación. Distingue ajustes de redacción, cambios de elegibilidad u orden, y cambios a la regla de selección; ninguno se aplica silenciosamente a la versión publicada.
2. Los **borradores no publicados** pueden corregirse sin generar nuevas versiones aprobadas. Una vez publicada una versión, cualquier cambio de contenido requiere preparar una nueva versión para revisión y aprobación, conservando la anterior. Se comprueba correspondencia de IDs, dimensión, puntuación aplicable, orden, texto de acción y evidencia sugerida entre Word y JSON. Si cambia la regla de selección, esta recibe su propia versión y revisión explícita.
3. Se revisan claridad, aplicabilidad para PyMEs y consistencia con el BRD: tres acciones distintas, sin inventar hallazgos ni exigir compra de software, contratación de servicios o nueva deuda. Los cambios que afecten selección se verifican con los casos del BRD, incluidos empates y 6,561 combinaciones válidas.
4. El **promotor autoriza** cada nueva versión del catálogo y de la regla de selección. La trazabilidad se conserva en **GitHub**, registrando cambios, motivo, versión, evidencia de revisión y autorización del promotor. No se crean actas ni sistemas adicionales. Solo una versión aprobada y verificada se habilita para diagnósticos nuevos. Esta aprobación de D-09 no aprueba cambios concretos del catálogo o la selección.
5. Los diagnósticos ya emitidos conservan sus versiones, IDs y texto o snapshot inmutable. Una versión nueva no reescribe resultados ni PDFs anteriores; su liberación se acompaña de pruebas de igualdad entre pantalla y PDF para nuevos diagnósticos.

## Criterios de aceptación documental

- El promotor ejerce la responsabilidad editorial y la autoridad de aprobación; cualquier delegación editorial futura queda identificada y registrada en GitHub.
- Las propuestas y revisiones de nuevas versiones dejan en GitHub el cambio, motivo, versión, evidencia de revisión y autorización del promotor.
- Los borradores no publicados admiten correcciones sin nueva versión aprobada; ningún contenido de una versión publicada se cambia sin nueva revisión versionada y aprobación.
- No se altera v0.1 sin una propuesta trazable y aprobación. Word y JSON de cada versión publicada coinciden; una divergencia impide usarla.
- Los cambios de elegibilidad, orden o regla de selección conservan determinismo y pasan las pruebas aplicables del BRD; un cambio de redacción no altera silenciosamente IDs o puntuaciones.
- El resultado y el PDF de diagnósticos existentes permanecen inmutables y atribuibles a las versiones con que fueron emitidos, conforme a D-01 y RN-016.
- La versión nueva entra en vigor solo para diagnósticos posteriores a su aprobación y verificación; no se infiere que el catálogo futuro tenga el mismo contenido o cantidad de acciones que v0.1.

## Fundamento y dependencias

- [PLAN_TRABAJO.md](../PLAN_TRABAJO.md), D-09: responsable editorial y proceso de versionado/aprobación.
- BRD v0.6, RN-016, sección 7.2 y RF-A16: catálogo v0.1 y selección v0.1 aprobados, anexos normativos, paridad Word/JSON, selección determinista, persistencia de versiones y mantenimiento pendiente de responsable.
- Concepto y alcance v0.8: catálogo aprobado preservado al pasar a Check v1.3.
- [D-01](D-01_PDF_CHECK.md): el PDF usa las tres acciones seleccionadas y muestra versiones; el contenido emitido no se altera retroactivamente.
- H1 C-03, C-13 y C-15 del plan: igualdad pantalla/PDF, pruebas de selección y versionado de cambios del Check. Estas tareas siguen pendientes de implementación o verificación según corresponda.

**Alcance de la aprobación:** queda cerrado el gobierno editorial de D-09 el 17 de octubre de 2026. No se modifican el catálogo v0.1, la regla de selección v0.1 ni el código; las actividades técnicas dependientes conservan su estado pendiente.
