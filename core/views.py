from django.shortcuts import render


def home(request):
    return render(request, 'home.html')


# Estas páginas muestran la estructura de Fase A durante el desarrollo. No
# incluyen formularios ni entregas de las actividades funcionales pendientes.
PAGES = {
    'tools': {
        'template': 'tools.html',
        'eyebrow': 'Herramientas · Fase A',
        'title': 'Calculadoras para preguntas concretas.',
        'intro': 'Usa modelos sencillos para explorar decisiones de tu negocio. La primera calculadora será la de punto de equilibrio mensual.',
        'status': 'Estructura en desarrollo',
        'note': 'La calculadora todavía no realiza cálculos. Su funcionamiento se incorporará en A-02.',
        'cards': [
            {'title': 'Punto de equilibrio', 'text': 'Una vista mensual de costos, precio y margen para un producto o servicio.', 'url': 'break_even', 'label': 'Conocer la herramienta'},
            {'title': 'Check PyME', 'text': 'Ocho preguntas para obtener una primera lectura de tus prácticas de gestión.', 'url': 'entry', 'label': 'Abrir el Check disponible'},
        ],
    },
    'break_even': {
        'eyebrow': 'Herramientas · Punto de equilibrio',
        'title': 'Entiende cuántas unidades necesitas vender para cubrir costos.',
        'intro': 'La calculadora de punto de equilibrio mensual utilizará costos fijos, precio unitario y costo variable unitario. El cálculo y sus resultados aún no están disponibles en esta entrega.',
        'status': 'Calculadora pendiente · A-02',
        'note': 'Vista de desarrollo. No captures importes aquí: todavía no existe un formulario funcional.',
        'section_heading': 'Los datos que usará',
        'cards': [
            {'title': 'Costos fijos mensuales', 'text': 'Gastos relativamente constantes dentro del volumen de operación considerado.'},
            {'title': 'Precio por unidad', 'text': 'Importe del mismo producto o servicio que se evaluará.'},
            {'title': 'Costo variable por unidad', 'text': 'Costo asociado a cada unidad vendida.'},
        ],
    },
    'resources': {
        'template': 'resources.html',
        'eyebrow': 'Recursos · Fase A',
        'title': 'Materiales para trabajar a tu ritmo.',
        'intro': 'Recursos prácticos que podrás llevar a tu operación. El primero será una plantilla Excel de flujo de efectivo de 13 semanas.',
        'status': 'Estructura en desarrollo',
        'note': 'La captura y entrega del primer recurso aún no están operativas. Se implementarán en A-03.',
        'cards': [
            {'title': 'Flujo de efectivo de 13 semanas', 'text': 'Plantilla Excel gratuita prevista para observar entradas y salidas de efectivo por semana.', 'url': 'cash_flow_resource', 'label': 'Conocer el recurso'},
        ],
    },
    'cash_flow_resource': {
        'eyebrow': 'Recursos · Flujo de efectivo',
        'title': 'Una plantilla para mirar trece semanas hacia adelante.',
        'intro': 'El primer recurso gratuito será una plantilla Excel de flujo de efectivo de 13 semanas. El archivo definitivo se proporcionará externamente durante A-03.',
        'status': 'Descarga pendiente · A-03',
        'note': 'Vista de desarrollo. Todavía no solicitamos datos ni enviamos el archivo.',
        'section_heading': 'Qué se está preparando',
        'cards': [
            {'title': 'Propósito', 'text': 'Organizar una vista semanal de entradas y salidas previstas.'},
            {'title': 'Entrega futura', 'text': 'La solicitud y el acceso al archivo tendrán su propio recorrido cuando A-03 esté implementada.'},
        ],
    },
    'blog': {
        'template': 'blog.html',
        'eyebrow': 'Contenido · Blog',
        'title': 'Ideas para gestionar con más claridad.',
        'intro': 'El contenido editorial se organizará alrededor de finanzas, negocios, datos y tecnología aplicados a proyectos, trabajo y negocios.',
        'status': 'Artículos pendientes · A-05',
        'note': 'Aún no hay artículos publicados en esta versión de desarrollo. No se muestran publicaciones de ejemplo como si fueran reales.',
        'cards': [
            {'title': 'Finanzas con Método', 'text': 'Lecturas para ordenar decisiones financieras.'},
            {'title': 'Negocios con Método', 'text': 'Prácticas para mejorar la operación y los márgenes.'},
            {'title': 'Datos y Tecnología', 'text': 'Uso práctico de indicadores y herramientas digitales.'},
        ],
    },
    'contact': {
        'template': 'contact.html',
        'eyebrow': 'Contacto',
        'title': 'Un canal para conversar.',
        'intro': 'Aquí podrás compartir comentarios sobre el portal o enviar solicitudes cuando el formulario esté disponible.',
        'status': 'Formulario pendiente · A-07',
        'note': 'Vista de desarrollo. Esta página todavía no recibe ni envía mensajes. La orientación asociada al Check se solicita dentro de su resultado activo.',
        'cards': [
            {'title': 'Comentarios', 'text': 'Observaciones sobre los contenidos y herramientas del portal.'},
            {'title': 'Solicitudes', 'text': 'Consultas que requieran seguimiento desde la operación del portal.'},
        ],
    },
    'about': {
        'eyebrow': 'Método Productivo',
        'title': 'Productividad con sentido.',
        'intro': 'Método Productivo reúne conocimiento práctico de finanzas, negocios, datos y tecnología. Sus contenidos y herramientas ayudan a entender opciones y tomar decisiones; el Check PyME se enfoca en prácticas empresariales.',
        'status': 'Contenido editorial provisional',
        'note': 'La presentación institucional definitiva está pendiente de revisión editorial para A-08.',
        'section_heading': 'Qué encontrarás aquí',
        'cards': [
            {'title': 'Aprender', 'text': 'Contenido claro para entender decisiones financieras y empresariales.'},
            {'title': 'Aplicar', 'text': 'Herramientas prácticas y recursos para pasar a la acción.'},
            {'title': 'Orientarse', 'text': 'Un Check inicial que puede abrir una conversación sobre los siguientes pasos.'},
        ],
    },
    'privacy': {
        'eyebrow': 'Privacidad',
        'title': 'Aviso de privacidad en preparación.',
        'intro': 'El aviso integral definitivo requiere los datos reales del responsable, canales de derechos ARCO y revisión jurídica antes de publicarse.',
        'status': 'Texto legal no publicable',
        'note': 'Esta página es solo una ubicación estructural en desarrollo. No constituye un aviso de privacidad ni reemplaza los textos definitivos de D-06.',
        'legal': True,
        'cards': [],
    },
    'terms': {
        'eyebrow': 'Términos',
        'title': 'Términos de uso en preparación.',
        'intro': 'Las condiciones de uso y los avisos aplicables al portal se incorporarán tras su revisión editorial y jurídica.',
        'status': 'Texto legal no publicable',
        'note': 'Esta página es solo una ubicación estructural en desarrollo. No constituye términos definitivos.',
        'legal': True,
        'cards': [],
    },
}


def section(request, page):
    context = PAGES[page]
    return render(request, context.get('template', 'section.html'), {'page': context})
