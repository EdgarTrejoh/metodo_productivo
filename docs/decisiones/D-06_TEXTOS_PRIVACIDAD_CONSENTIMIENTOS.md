# D-06 — Textos de servicio, privacidad y consentimiento comercial

**Estado:** APROBADA — Alcance funcional  
**Fecha de propuesta:** 17 de octubre de 2026  
**Fecha de aprobación funcional:** 17 de octubre de 2026  
**Responsable de la decisión:** promotor del proyecto; revisión jurídica y de privacidad requerida antes de publicar los textos  
**Evidencia:** autorización expresa del promotor durante la revisión documental del proyecto

## Objetivo de la decisión

D-06 aprueba el alcance funcional de los textos de formularios de Fase A, el aviso de privacidad y la regla de preferencias y baja comercial. Esta aprobación **no autoriza publicar textos legales ni certifica cumplimiento jurídico integral**. Los textos de prueba actuales deben sustituirse solo cuando la redacción final y los datos del responsable estén validados.

### Datos realmente capturados por el Check PyME v1.3

El Check formula ocho preguntas sobre **prácticas de gestión empresarial** y conserva las respuestas, puntuación y diagnóstico asociados. No solicita importes de ventas o deudas, cuentas bancarias, estados financieros ni documentación financiera o patrimonial; el portal tampoco permite cargar documentos en este recorrido. La captura personal obligatoria se limita a **nombre, correo electrónico y empresa**; WhatsApp es opcional. Contacto, respuestas y resultado se conservan internamente durante **12 meses desde la finalización** del Check. Al abandonar el contexto autorizado, el diagnóstico no se recupera públicamente, conforme a D-02.

Los datos de contacto y su vinculación con el diagnóstico requieren protección. La formulación de las preguntas no justifica clasificar automáticamente todo el cuestionario como tratamiento de datos personales sensibles. Cualquier clasificación jurídica adicional deberá basarse en los datos efectivamente tratados y validarse antes de producción. La falta de recuperación pública del informe **no limita los derechos ARCO** que correspondan legalmente.

### Reglas ya documentadas que D-06 debe respetar

| Recorrido | Finalidad necesaria | Separación requerida |
| --- | --- | --- |
| Check PyME | Tratar respuestas y datos asociados para generar y mostrar el resultado y conservar internamente el diagnóstico durante 12 meses desde su finalización. | El informe se libera en el recorrido activo sin correo de acceso ni recuperación pública. El consentimiento comercial es independiente y opcional. La orientación solo se solicita por acción expresa. |
| Lead magnet D-05 | Capturar nombre y correo para entregar el Excel externo solicitado mediante correo transaccional y enlace de propósito específico. | Solicitar el recurso no equivale a aceptar marketing. El correo de entrega no incluye invitación al Check; el CTA permanece en la página de gracias. |
| Contacto y orientación | Usar la información necesaria para atender la solicitud formulada por la persona. | La solicitud no crea por sí sola una suscripción comercial. |
| Comunicaciones comerciales | Enviar únicamente según la preferencia comercial registrada. | La baja afecta los envíos comerciales, sin bloquear correos transaccionales necesarios. |

**Poner el aviso a disposición** y **obtener el consentimiento que jurídicamente corresponda** son acciones distintas. RN-005 y RF-A09 exigen separar la finalidad necesaria del Check de la comercial; RN-006 establece que el consentimiento comercial es opcional y revocable. La modalidad jurídica para cada finalidad se validará antes de producción: D-06 no presupone una casilla de aceptación idéntica y obligatoria en todos los formularios. Los plazos de otros leads y consentimientos que aparecen como valores de trabajo en BRD v0.6 no se convierten en política publicable por esta propuesta.

## Redacciones funcionales aprobadas, pendientes de validación para publicación

Estas frases breves expresan el alcance funcional aprobado para cada finalidad. Deben pasar por revisión jurídica y editorial, junto con el aviso aplicable y la modalidad de consentimiento de cada finalidad, antes de convertirse en texto final publicable de interfaz.

| Ubicación | Texto funcional aprobado | Control |
| --- | --- | --- |
| Captura del Check | «Usaremos tus respuestas para generar y mostrar tu resultado del Check PyME y tus datos de contacto para asociarlo a esta solicitud. Conservaremos internamente el diagnóstico y los datos asociados durante 12 meses desde su finalización. Al salir, no podrás recuperar el informe desde el portal. Consulta el Aviso de Privacidad.» | Aviso a disposición y tratamiento necesario para el servicio; la modalidad de consentimiento se validará jurídicamente. La falta de recuperación pública no afecta los derechos ARCO aplicables. |
| Captura del lead magnet | «Usaremos tu nombre y correo para enviarte el acceso a la plantilla gratuita solicitada. Consulta el Aviso de Privacidad.» | Aviso a disposición y tratamiento necesario para entregar el recurso; modalidad de consentimiento pendiente de validación jurídica. |
| Consentimiento comercial, cuando corresponda | «Quiero recibir comunicaciones comerciales de Método Productivo por correo. Puedo darme de baja después.» | Opción independiente, voluntaria, revocable y desmarcada por defecto. Rechazarla no condiciona el Check, el lead magnet ni la orientación solicitada. |
| Solicitud de orientación | «Solicito que me contacten sobre este diagnóstico usando los datos que ya proporcioné. Esta solicitud no me suscribe a comunicaciones comerciales.» | Acción expresa en la pantalla de resultado, conforme al contexto activo aprobado. |
| Confirmación de baja | «Dejaste de recibir comunicaciones comerciales. Seguirás recibiendo los mensajes necesarios para los servicios o recursos que solicites.» | Confirmación después de la baja efectiva. |

La selección del canal de contacto para orientación y el eventual campo opcional de descripción pertenecen a D-07; esta propuesta no los decide. El correo transaccional aprobado en D-05 conserva su alcance de entrega y no se reescribe aquí.

## Requisitos previos a publicación: aviso y validación jurídica

Mantener un aviso breve junto a cada formulario y un aviso integral accesible en `/privacidad/`. La versión integral debe identificar al responsable del tratamiento; describir datos, finalidades necesarias y comerciales, retención según cada finalidad, opciones para limitar uso o divulgación, canales para derechos ARCO, revocación y baja comercial, y cómo se comunicarán cambios. La revisión jurídica definirá la redacción exacta, el domicilio, destinatarios o transferencias aplicables y la modalidad de consentimiento que corresponda. La ausencia de recuperación pública del diagnóstico no restringe el ejercicio de derechos ARCO. **No completar datos del responsable, proveedores, canales o plazos con supuestos.**

| Conjunto | Plazo documentado | Estado para publicación |
| --- | --- | --- |
| Contacto, respuestas y resultado del Check | 12 meses desde la finalización del Check. | Regla de negocio conservada; tratamiento, eliminación o anonimización y respaldos sujetos a validación de privacidad antes de producción. |
| Otros leads sin relación posterior | 24 meses desde la última interacción, según BRD v0.6. | Valor de trabajo pendiente de validación; no prolonga el diagnóstico del Check. |
| Consentimiento comercial | Hasta baja u oposición, o 24 meses de inactividad, según BRD v0.6. | Valor de trabajo pendiente de validación; conservar evidencia mínima de supresión. |
| Comentarios y solicitudes | 12 meses después del cierre, según BRD v0.6. | Valor de trabajo pendiente de validación de la política aplicable. |

Antes de aprobar la redacción publicable, el promotor deberá proporcionar o confirmar:

1. Identidad y domicilio del responsable del tratamiento, así como canal responsable de solicitudes de privacidad.
2. Inventario de datos y destinatarios reales por formulario e integración de Fase A, incluido el proveedor de correo cuando se seleccione; clasificación jurídica fundada en los datos efectivamente tratados.
3. Redacción final del aviso breve e integral, canales para derechos ARCO, revocación y baja, y forma de comunicar cambios.
4. Política validada para otros leads, consentimientos, solicitudes y respaldos, preservando la retención del Check y la evidencia mínima de baja.
5. Revisión jurídica y editorial de las frases de servicio, modalidad de consentimiento por finalidad y opción comercial antes de su publicación.

## Preferencias, baja y evidencia

- Se aprueba una preferencia comercial mínima: **acepta / no acepta o revoca** comunicaciones comerciales. No inferir aceptación del uso del Check, la descarga del lead magnet o la solicitud de orientación.
- Cada formulario registra la versión del texto, fecha y hora y la opción elegida cuando corresponda, conforme a RF-A09. Un lead único por correo puede conservar interacciones y decisiones de consentimiento separadas.
- Cada correo comercial automatizado incluye acceso a la baja. Según J8, `GET /baja/{token}/` solo muestra la página; el `POST` ejecuta la baja con efecto inmediato y muestra confirmación. Una baja conserva la evidencia mínima necesaria y detiene nuevos envíos comerciales, sin impedir correos transaccionales solicitados.
- Si el enlace de baja es inválido, mostrar el mensaje genérico y la ruta de contacto previstos en J8. El detalle operativo de preferencias y baja se implementará y verificará en A-04; la aprobación funcional de D-06 no acredita esa implementación.

## Aprobación funcional, publicación y dependencias

- **Aprobación funcional de D-06:** el promotor confirmó las finalidades separadas, las redacciones funcionales, la preferencia comercial desmarcada y revocable, y la baja que no afecta correos transaccionales. Esta aprobación no equivale a publicación ni a cumplimiento jurídico integral.
- **Antes de publicación:** contar con datos reales del responsable, aviso integral y avisos breves definitivos, clasificación jurídica aplicable, mecanismos de derechos ARCO y revocación, y validación jurídica de modalidades de consentimiento, textos y retenciones. Hasta entonces los textos de prueba no se sustituyen como textos publicables.
- Confirmar que rechazar marketing no bloquea Check, lead magnet u orientación solicitada; mantener identificados los plazos que son solo valores de trabajo.
- C-06 y A-04 implementarán los textos y la baja; C-07 y C-08 resolverán retención y eliminación; A-08 publicará la página de privacidad. R-05 verificará todo antes de usar datos reales. Ninguna de esas actividades se declara iniciada o verificada por esta aprobación funcional.

## Fundamento

- [PLAN_TRABAJO.md](../PLAN_TRABAJO.md), H0 D-06 y dependencias de H1/H2.
- BRD v0.6, sección 7 y RN-005, RN-006, RF-A05, RF-A09–RF-A11, RF-A14 y sección 12: datos y reglas reales del Check, separación de finalidades, evidencia, baja, correo transaccional y valores de trabajo de retención.
- Concepto y alcance v0.8, sección 14: privacidad por finalidad y 12 meses de conservación interna del Check, sujetos a validación de privacidad antes de producción.
- [D-02](D-02_CONTEXTO_ACTIVO_CHECK.md) y [D-05](D-05_PRIMER_LEAD_MAGNET.md): acceso temporal del Check sin recuperación pública y entrega del recurso por finalidad propia.
- Sitemap y journeys v0.2, J1, J4 y J8: captura, entrega y baja mediante `POST`.
- [D-01](D-01_PDF_CHECK.md): disclaimer del PDF aprobado; su aviso requiere revisión jurídica.
- [Ley Federal de Protección de Datos Personales en Posesión de los Particulares, texto vigente consultado el 17 de octubre de 2026](https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf), artículos 7 y 14–16: referencia para revisión jurídica; su cita no sustituye esa revisión.

**Estado de publicación y verificación:** D-06 quedó aprobada en su alcance funcional el 17 de octubre de 2026. Siguen pendientes la revisión jurídica, los datos reales del responsable, los canales ARCO, los avisos definitivos y la validación de retenciones antes de producción. Los textos no están autorizados para publicación; la implementación y la verificación permanecen pendientes.
