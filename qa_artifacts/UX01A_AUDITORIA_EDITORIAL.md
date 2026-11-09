# UX-01A — Auditoría editorial y cierre de revisión

**Fecha de auditoría:** 3 de noviembre de 2026. **Estado: APROBADA editorialmente el 9 de noviembre de 2026**, en el alcance y con las salvedades indicadas a continuación. La matriz y las propuestas originales se conservan como evidencia histórica de la revisión; sus estados iniciales no describen por sí solos la implementación actual.

**Cierre editorial aprobado:** Home, Acerca de, Recursos, Herramientas, Tienda, Contenidos, Check PyME y Contacto, incluido el estado de indisponibilidad UX01A-017 del Mapa de Caja PyME. La presentación institucional aprobada de Acerca de y los textos actuales de Home quedan aceptados sin cambios adicionales. La corrección «Revisa tus datos» de la calculadora forma parte del cierre local. La captura sintética `ux01a-017-unavailable-desktop.png` se conserva como evidencia de UX01A-017.

**Salvedades de producción:** esta aprobación editorial local no acredita publicación ni habilita datos reales, correo transaccional, disponibilidad del Excel, atención de orientación, pagos LIVE o entrega digital. Permanecen pendientes los textos y controles definitivos de privacidad y términos, consentimiento y baja, configuración y operación de infraestructura, pruebas integrales y las autorizaciones comerciales y jurídicas aplicables. Los apartados 3, 5, 6, 8 y 9 registran hallazgos, propuestas y decisiones según el corte original del 3-nov-2026; deben leerse con este cierre posterior.

## 1. Resumen ejecutivo

Hay textos estáticos que describen como pendientes capacidades ya construidas y otros que presentan estados internos de desarrollo al visitante. El estado del archivo privado, publicaciones, productos y correo depende del entorno y no se ha comprobado con datos reales. La privacidad y los términos siguen siendo un bloqueo de publicación: los avisos actuales son provisionales y algunas afirmaciones dependen de operaciones aún no implementadas. La propuesta conserva las cuatro áreas de Método Productivo y no presupone disponibilidad pública.

La matriz contiene 24 hallazgos: P0: 5; P1: 14; P2: 5. Las propuestas son textos para revisión, no instrucciones para retirar las advertencias de desarrollo antes de que corresponda.

## 2. Estado funcional contrastado

| Sección | Estado y límites | Evidencia |
|---|---|---|
| Home, menú, footer y Acerca de | Plantillas y rutas implementadas; avisos de desarrollo visibles. Presentación institucional pendiente de revisión. | `templates/home.html`, `base.html`, `section.html`; `core/views.py` PAGES. |
| Herramientas y punto de equilibrio | Cálculo mensual local, formulario y validaciones implementados; un producto o servicio, unidades completas y supuestos constantes. A-02 no queda cerrada por esta auditoría. | D-04; `core/break_even.py`, `core/views.py`, `templates/break_even.html`; `docs/VERIFICACION.md`. |
| Recursos | Solicitud, correo y acceso privado implementados localmente con estado condicionado al archivo. Excel definitivo externo y servicio de correo efectivo sujetos a disponibilidad y configuración. | D-05; `leads/views.py`, `leads/lead_magnet.py`, plantillas `lead_magnet/`; D-10. |
| Check PyME | Entrada, ocho respuestas, captura, resultado y PDF implementados en contexto activo; no hay recuperación posterior. La solicitud de orientación registra localmente; operación completa y notificación pendientes. | D-02 y D-07; `diagnostics/views.py`, `services.py`, `templates/result.html`; expediente D-06 §10. |
| Contenidos y videos | Listados, filtro, detalle y videos dependen de publicaciones vigentes; no se inspeccionó ni alteró la base de datos. | `content/views.py`, `content/models.py`, `templates/blog.html`, `article_detail.html`; `content/tests.py`. |
| Tienda | Catálogo y fichas dependen de productos publicados. Pago de prueba condicionado a DEBUG, configuración y enlace válido; no hay compra real ni entrega acreditada. | `store/views.py`, `store/tests.py`, `templates/store/`. |
| Contacto | Formulario guarda solicitud y muestra confirmación; notificación depende de configuración y operación. | `core/views.py`, `leads/notifications.py`, `templates/contact.html`. |
| Privacidad y términos | Borrador local y pantalla estructural fuera de local; textos definitivos, datos, modalidades y revisión jurídica pendientes. | D-06; `docs/privacidad/D06_EXPEDIENTE_PREPUBLICACION.md` §§10–11; `core/views.py`. |

La verificación aquí es revisión de código y evidencia de pruebas documentadas, no una nueva ejecución de recorridos. `docs/VERIFICACION.md` registra suites y pruebas de navegador locales; no acredita publicación ni disponibilidad actual. D-08 y D-10 distinguen medición y aceptación de cada incremento; la aceptación local O08-01/O08-FIX-01 no cierra O-08/O-09 ni autoriza despliegue. No se consultó `config.yaml` ni se comprobó el archivo privado o registros publicados.

## 3. Matriz de hallazgos

Las citas son fragmentos literales de la interfaz o valores de plantilla. Cuando se indican alternativas, su presentación requiere verificar la condición indicada.

| ID | Página / sección | Archivo y referencia | Texto actual | Problema | Evidencia funcional | Texto propuesto | Prioridad |
|---|---|---|---|---|---|---|---|
| UX01A-001 | Home / contenidos | `templates/home.html` tarjeta | «Artículos pendientes» | Estado fijo puede contradecir publicaciones. | `content/views.py` consulta artículos vigentes. | Con artículos: «Artículos publicados»; sin artículos: «Aún sin artículos publicados». Requiere condición en Home. | P0 |
| UX01A-002 | Home / recursos | `templates/home.html` tarjeta | «Entrega pendiente» | Estado fijo puede contradecir disponibilidad del archivo. | `leads/views.py` consulta almacenamiento. | Disponible: «Plantilla disponible»; no disponible: «Temporalmente no disponible». Requiere condición. | P0 |
| UX01A-003 | Recursos / ficha | `templates/resources.html` recurso | «Archivo definitivo pendiente · A-03» | Estado fijo e identificador interno. | La ficha de solicitud comprueba disponibilidad. | Disponible: «Plantilla Excel disponible»; no disponible: «Plantilla temporalmente no disponible». Requiere condición. | P0 |
| UX01A-004 | Recursos / introducción | `core/views.py` PAGES resources intro | «Recursos prácticos que podrás llevar a tu operación. El primero será una plantilla Excel de flujo de efectivo de 13 semanas.» | Futuro fijo incluso si existe archivo. | `templates/resources.html` muestra `page.intro`; solicitud condicionada. | «Conoce recursos prácticos para tu operación, incluido el Mapa de Caja PyME, una plantilla de flujo de efectivo de 13 semanas.» | P0 |
| UX01A-005 | Privacidad / comercial | `templates/privacy.html` comunicación comercial | «Puedes retirar tu autorización en cualquier momento desde el enlace de baja incluido en cada correo» | Describe mecanismo no implementado como existente. Bloqueo jurídico y operativo. | Expediente D-06 §10: sin ruta ni token de baja; A-04 pendiente. | Conservar el borrador identificado y someter esta afirmación a dictamen; propuesta sujeta a canal efectivo: «Podrás solicitar la baja por el medio indicado en el aviso definitivo.» No publicar hasta validar e implementar el canal. | P0 |
| UX01A-006 | Home / herramienta | `templates/home.html` tarjeta | «Calculadoras»; «Ver calculadoras» | Plural sugiere varias calculadoras. | Solo punto de equilibrio en `templates/tools.html`. | «Punto de equilibrio»; «Usar la calculadora». El enlace actual lleva a Herramientas: si se conserva, usar «Conocer la calculadora». | P1 |
| UX01A-007 | Home / Check | `templates/home.html` tarjeta | «Diagnóstico inicial» | Nombre distinto al menú y al destino. | `templates/entry.html` usa Check PyME. | «Check PyME». | P1 |
| UX01A-008 | Home / recurso | `templates/home.html` tarjeta | «Conoce la plantilla gratuita de flujo de efectivo de 13 semanas prevista para Fase A.» | Referencia interna y futuro fijo. | D-05; recurso y solicitud condicionada implementados. | «Conoce el Mapa de Caja PyME, una plantilla para ordenar entradas y salidas previstas durante 13 semanas.» | P1 |
| UX01A-009 | Herramientas | `templates/tools.html` | «Herramientas · Fase A» | Jerga de proyecto visible. | La página presenta la calculadora. | «Herramientas». | P1 |
| UX01A-010 | Herramientas / título | `core/views.py` PAGES tools title | «Calculadoras para preguntas concretas.» | Plural no corresponde al catálogo actual. | Solo una calculadora en la plantilla. | «Una calculadora para una pregunta concreta.» | P1 |
| UX01A-011 | Recursos | `templates/resources.html` | «Recursos · Fase A» | Referencia interna. | Plantilla pública de recursos. | «Recursos». | P1 |
| UX01A-012 | Recursos / nota | `templates/resources.html` | «El archivo definitivo será proporcionado externamente. La página del recurso indica si la solicitud está disponible en este entorno local.» | Expone proceso interno y no explica la acción. | Estado real se consulta en página del recurso. | «Consulta la página del Mapa de Caja PyME para conocer la disponibilidad y solicitar la plantilla cuando esté disponible.» | P1 |
| UX01A-013 | Contenidos | `templates/blog.html` | «Contenidos · Fase A» | Referencia interna. | El listado funciona con datos publicados. | «Contenidos». | P1 |
| UX01A-014 | Contenidos / vacío | `templates/blog.html` | «Las primeras lecturas están en preparación editorial.» | Afirma preparación sin evidencia y repite el vacío. | `has_live_articles` solo indica existencia de artículos vigentes. | «Todavía no hay artículos publicados.» | P1 |
| UX01A-015 | Tienda / introducción | `templates/store/index.html` | «Productos digitales de Método Productivo disponibles para explorar. La compra en línea todavía no está habilitada.» | La primera frase afirma existencia aun con catálogo vacío. | `products` puede estar vacío. | Con productos: «Explora los productos digitales de Método Productivo. La compra en línea todavía no está habilitada.» Sin productos: «Aquí encontrarás productos digitales de Método Productivo cuando estén publicados. La compra en línea todavía no está habilitada.» Requiere condición. | P1 |
| UX01A-016 | Orientación / solicitud | `templates/result.html` | «¿Quieres que te contactemos sobre este diagnóstico? Usaremos los datos capturados. No te suscribe a comunicaciones comerciales.» | Puede sugerir atención operativa ya disponible. | D-07 y expediente §10: registro básico; notificación y atención pendientes. | Para pruebas locales: «Puedes registrar una solicitud de orientación sobre este diagnóstico. En esta prueba no se enviará una notificación ni se garantiza contacto. No te suscribe a comunicaciones comerciales.» Revisar antes de habilitar operación real. | P1 |
| UX01A-017 | Recurso / disponibilidad | `templates/lead_magnet/resource.html` | «El archivo Excel definitivo aún no está disponible en este entorno. La solicitud por correo está temporalmente deshabilitada; no se enviará un enlace ficticio.» | Correcto como control local, demasiado interno para público. | Rama `not available` deshabilita formulario. | «La plantilla no está disponible temporalmente. Vuelve a consultar esta página más adelante.» Conservar estado local hasta autorización. | P1 |
| UX01A-018 | Recurso / confirmación | `templates/lead_magnet/thanks.html` | «El backend de correo de este entorno aceptó el mensaje de prueba. Revisa el buzón de pruebas local para abrir tu enlace privado. Esto no confirma entrega a un correo real.» | Describe correctamente prueba local; sería impropio para público. | `claim.email_status == 'sent'` registra aceptación del backend, no entrega. | Local: conservar. Entorno real validado: «Aceptamos tu solicitud y enviamos el mensaje al servicio de correo. Revisa tu bandeja de entrada y correo no deseado.» Requiere condición y operación verificadas. | P1 |
| UX01A-019 | Home / CTA | `templates/home.html` hero | «Explorar el portal» | CTA genérico. | Ancla a `#explorar`. | «Explorar herramientas y recursos». | P2 |
| UX01A-020 | Calculadora / introducción | `templates/break_even.html` | «El cálculo se realiza en el servidor, sin cuenta ni descarga de Excel.» | Detalle técnico sin beneficio claro. | POST calcula sin cuenta ni archivo. | «Obtén el cálculo aquí, sin crear una cuenta ni descargar un archivo.» | P2 |
| UX01A-021 | Calculadora / alcance | `templates/break_even.html` | «Ingrese un precio esperado después de sus descuentos habituales y use importes sin impuestos trasladados.» | Cambia de trato de tú a usted. | El resto del formulario usa tú; D-04 conserva supuestos. | «Ingresa el precio esperado después de los descuentos habituales y usa importes sin impuestos trasladados.» | P2 |
| UX01A-022 | Check / formulario vencido | `templates/expired.html` | «Continúa la ejecución vigente en la otra pestaña o inicia un nuevo Check.» | «Ejecución vigente» es técnico. | D-02 y `diagnostics/views.py` detectan formulario anterior. | «Continúa el Check que tienes abierto en la otra pestaña o inicia uno nuevo.» | P2 |
| UX01A-023 | Contacto | `templates/contact.html` | «Conversemos sobre tu mensaje.» | Encabezado poco informativo. | Formulario acepta comentario o solicitud. | «Envíanos un comentario o una solicitud.» | P2 |

| UX01A-024 | Acerca de / estado | `core/views.py` PAGES about status y note; `templates/section.html` | «Contenido editorial provisional»; «La presentación institucional definitiva está pendiente de revisión editorial para A-08.» | Referencia interna visible y presentación provisional. | `section.html` muestra estado y nota; revisión institucional pendiente. | «Conoce Método Productivo»; «Reunimos conocimientos y herramientas para apoyar decisiones de negocio.» Aplicar solo después de aprobar la presentación institucional. | P1 |

## 4. Glosario editorial

| Denominación | Uso y variantes |
|---|---|
| Check PyME | Nombre propio en menú, entrada y tarjeta; sustituye «Diagnóstico inicial» como título. «Diagnóstico de gestión» describe el informe, no evaluación crediticia. |
| Punto de equilibrio | Nombre de herramienta; «Punto de equilibrio mensual» para precisar periodo. Evitar plural «Calculadoras» mientras solo exista una. |
| Herramientas | Nombre de sección y menú; puede agrupar futuras herramientas sin afirmar que ya existen. |
| Mapa de Caja PyME | Nombre del Excel; «plantilla de flujo de efectivo de 13 semanas» como descripción. Sustituye títulos genéricos de recurso. |
| Recursos | Sección y menú; no garantiza descarga disponible. |
| Contenidos | Sección y menú; incluye artículos y videos cuando estén publicados. |
| Tienda | Etiqueta de navegación; «Tienda digital» puede describir el encabezado. Compra real permanece deshabilitada. |
| Orientación | Solicitud ligada al resultado del Check, sujeta a operación D-07; no prometer asesoría ni respuesta. |
| Contacto | Canal general de comentarios y solicitudes, distinto de orientación del Check. |

## 5. Textos condicionados y alcance de implementación

- **Excel presente:** «Solicita el Mapa de Caja PyME y recibe un enlace privado por correo.» Mostrar solo si archivo y entrega están habilitados. **Ausente:** «La plantilla no está disponible temporalmente. Vuelve a consultar esta página más adelante.» La página del recurso ya distingue archivo; Home y Recursos requieren datos y condiciones adicionales. La aceptación del correo no prueba entrega.
- **Artículos publicados:** «Explora los artículos publicados.» **Sin artículos:** «Todavía no hay artículos publicados.» Para categoría vacía: «Todavía no hay artículos publicados en esta categoría.» Videos: «Todavía no hay videos publicados.» El listado ya dispone de condiciones; Home necesita consulta adicional.
- **Productos publicados:** «Explora los productos digitales publicados. La compra en línea todavía no está habilitada.» **Sin productos:** «Todavía no hay productos digitales publicados. La compra en línea todavía no está habilitada.» El listado ya dispone de `products`. El enlace de prueba solo se muestra bajo sus controles y debe seguir identificado como prueba sin cargos ni entrega.
- **Orientación:** conservar confirmación local «Tu solicitud de orientación quedó registrada en la prueba local. No se ha enviado un correo.» La versión pública depende de atención, notificación y decisión operativa D-07.
- **Acceso al Excel:** conservar vigencia, límite, confirmación, fallo y reintentos existentes. El texto de éxito público depende de un proveedor real y no debe afirmar entrega confirmada por el buzón.

## 6. Paquetes de actualización

| Paquete | Archivos afectados | Tipo, dependencias y riesgos |
|---|---|---|
| A — Estados falsos u obsoletos | `home.html`, `resources.html`, `core/views.py`, `store/index.html`, `privacy.html` | 001–005 y 015: condiciones para Home/Recursos y tienda; revisar consultas, tiempos y estados vacíos. 005 requiere dictamen y mecanismo de baja, no simple edición. No retirar avisos de prueba. |
| B — Homologación | `home.html`, `tools.html`, `resources.html`, `blog.html`, `core/views.py`, `result.html`, `lead_magnet/resource.html`, `lead_magnet/thanks.html` | 006–018 y 024: mayormente texto; 016–018 dependen de operación, entorno y autorización. Mantener destinos y atributos de analítica O08-01; comprobar continuidad, consentimientos y mensajes de error. |
| C — Comunicación | `home.html`, `break_even.html`, `expired.html`, `contact.html` | 019–023 son textos; comprobar que CTA describe su ancla y que no se alteran supuestos, validación ni navegación. |

Ningún paquete autoriza reorganizar menú, modificar medición, implementar lógica o publicar. Las condiciones propuestas que no existen requieren incremento funcional separado.

## 7. Restricciones legales y operativas

Conservar en local el banner «Entorno de desarrollo · Usa datos ficticios», el estado provisional de privacidad y términos, la advertencia «BORRADOR — NO AUTORIZADO PARA PUBLICACIÓN», los consentimientos y avisos de formularios, y las limitaciones del Check y de la calculadora. No son textos comerciales para eliminar por estilo. `privacy.html` contiene borrador visible en local; fuera de local `core/views.py` presenta ubicación estructural, no aviso definitivo. Los mensajes internos en código no son necesariamente visibles: en particular `status` y `note` de PAGES tools/resources no aparecen en sus plantillas especializadas, mientras `page.intro` sí aparece. Las referencias internas en `section.html` pueden mostrarse en Acerca de y términos.

D-06 y su expediente exigen identidad, domicilio, canales, proveedores, revisión de modalidades y dictamen, además de resolver baja, retención, supresión y respaldos. La afirmación de baja en UX01A-005 contradice la ausencia del mecanismo y bloquea publicación; también deben revisarse las afirmaciones de entrega y atención frente a infraestructura real. El estado jurídico no queda aprobado por esta propuesta ni por completar configuración. Términos sigue provisional. No sustituir avisos por texto jurídico inventado.

## 8. Decisiones del promotor

1. Aprobar nombres, trato de tú, textos y prioridad de los paquetes, particularmente la denominación de la tarjeta del Check y el CTA principal.
2. Decidir cuándo se habilitarán y cómo se atenderán solicitudes de orientación conforme a D-07, sin prometer seguimiento antes de contar con operación.
3. Confirmar provisión del Excel y condiciones de correo, y autorizar estados públicos tras pruebas del entorno real.
4. Revisar presentación institucional de Acerca de y alcance del catálogo de contenidos y productos, sin presumir publicaciones.
5. Completar datos y obtener revisión jurídica de D-06, términos, baja y plazos; decidir implementación y verificación de mecanismos pendientes antes de publicar.

## 9. Implementación por incrementos

Primero aprobar la matriz y resolver bloqueos jurídicos y operativos; después aplicar A con condiciones comprobadas y pruebas de estados vacíos y disponibles. Aplicar B preservando rutas, consentimientos y eventos, con pruebas de recorridos de Check, correo y orientación. Aplicar C y revisar textos, metadatos, accesibilidad y presentación. Cada incremento requiere aprobación y evidencia propia; verificar PDF y pantalla juntos si se modifican mensajes compartidos. Esta auditoría no cambia el sitio ni acredita el gate de publicación.
