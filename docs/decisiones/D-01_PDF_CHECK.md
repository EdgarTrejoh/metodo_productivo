# D-01 — Contenido y diseño del PDF del Check PyME

**Estado:** aprobada por el promotor del proyecto  
**Fecha de propuesta y aprobación:** 17 de octubre de 2026  
**Evidencia:** aprobación expresa en la conversación de trabajo del proyecto

## Decisión aprobada

El PDF será una copia descargable del diagnóstico liberado en pantalla, generada a partir del mismo resultado persistido. Tendrá una lectura ejecutiva al inicio y un detalle de las ocho respuestas al final. No tendrá un número fijo de páginas. No se enviará por correo ni se ofrecerá recuperación pública después de salir del recorrido.

### Contenido y orden

1. **Portada breve:** logotipo y nombre Método Productivo, título «Informe Check PyME», nombre de la empresa, fecha de emisión y versión del Check. No incluir correo ni WhatsApp en el PDF.
2. **Resultado ejecutivo:** puntuación de 0 a 100, nivel correspondiente y puntos brutos de 0 a 16. Explicar que la puntuación resume prácticas declaradas y no una evaluación verificada de la empresa.
3. **Desglose:** las ocho dimensiones, en el orden del cuestionario, con puntuación de 0 a 2 cada una. No representar diferencias de un punto como porcentajes financieros.
4. **Hallazgos:** hasta dos fortalezas y hasta dos brechas, con el mismo orden y los mismos textos que en pantalla. Si una lista queda vacía, usar el mensaje de ausencia previsto en el BRD; no inventar hallazgos.
5. **Plan para 30 días:** exactamente las tres acciones distintas seleccionadas del catálogo aprobado, cada una con dimensión, texto de acción y evidencia sugerida de cumplimiento. Mostrar el orden de prioridad que devuelve la selección; no cambiarlo por criterio editorial.
6. **Detalle de respuestas:** para cada una de las ocho preguntas, mostrar dimensión, pregunta y texto exacto de la opción elegida, seguido de su puntuación de 0 a 2. En financiamiento mostrar la opción elegida, no solo la puntuación, porque varias opciones tienen el mismo valor.
7. **Alcance y trazabilidad:** aviso de alcance visible; versiones del Check, catálogo, regla de selección y plantilla del informe. La fecha de emisión y los textos mostrados deben corresponder al diagnóstico original, incluso después de actualizar preguntas o catálogo.

### Aviso de alcance aprobado editorialmente

> Este informe resume prácticas declaradas por la persona que respondió el Check PyME. Método Productivo no ha verificado la información proporcionada. El resultado es orientativo y no constituye una calificación crediticia, un diagnóstico financiero integral, una recomendación de inversión ni una certificación de la empresa. Las acciones sugeridas son puntos de partida para organizar información y mejorar prácticas; no sustituyen asesoría profesional adaptada a cada caso.

La redacción final del aviso y su ubicación en pantalla requieren la revisión de textos legales y de consentimiento prevista en D-06. D-01 puede fijar estructura y contenido editorial sin dar por aprobada esa revisión.

### Diseño propuesto

- Formato A4 vertical, fondo blanco, márgenes amplios, encabezados azul profundo (`#07345F`) y verde productivo (`#00A987`) para resaltar el resultado. Mantener contraste legible también en impresión en escala de grises.
- Jerarquía de lectura: resultado y plan de acción visibles antes del detalle de respuestas. Tablas con encabezados repetidos si cruzan páginas; evitar cortes dentro de una acción o respuesta.
- Usar las fuentes de la identidad visual cuando estén disponibles e incorporadas al proyecto; prever una sustitución legible en PDF. El logotipo debe provenir de `docs/identidad/assets/` o de su copia preparada para la aplicación.
- Texto seleccionable y orden de lectura coherente; no convertir el contenido en una imagen. El tamaño y número de páginas dependerán de la extensión real del contenido.
- Mostrar «Descarga tu informe antes de salir. Para obtener otro, deberás realizar el Check nuevamente» junto al botón de descarga en pantalla; no depender del PDF para explicar la regla de acceso.

## Criterios de aceptación para C-03

- Pantalla y PDF muestran el mismo score, nivel, ocho puntuaciones, fortalezas, brechas y tres acciones, tomados del mismo diagnóstico persistido.
- El PDF reproduce las ocho opciones textuales elegidas, incluida la opción específica de financiamiento, y conserva las versiones de contenido usadas al emitirlo.
- Los casos extremos del BRD (todo 0, todo 2, una sola fortaleza, una sola brecha y empates) no agregan hallazgos ficticios.
- El informe se puede leer, imprimir y reintentar dentro del recorrido activo; falla de generación no crea otro diagnóstico ni borra el resultado en pantalla.
- Producto revisa una muestra visual en escritorio e impresión y aprueba texto, orden, marca y aviso antes de cerrar C-03.

## Fundamento y límites

- BRD v0.6, secciones 7, 7.1, RF-A05, RF-A16 y RF-A17: contenido mínimo, selección reproducible, entrega inmediata y ausencia de recuperación.
- Concepto y alcance v0.8, Anexo A: resultado orientativo basado en respuestas declaradas y límites del disclaimer.
- Propuesta visual v0.2, pantalla 3B y sistema de identidad: hallazgos, acciones, descarga y lenguaje visual.
- [Estado técnico B0](../ESTADO.md): el PDF actual es provisional y todavía no incluye todas las respuestas textuales.

**Alcance de la aprobación:** quedan definidos contenido, orden, diseño y detalle de respuestas para implementar C-03. La revisión jurídica de la redacción final del aviso y los textos de consentimiento permanece en D-06 antes de publicar.
