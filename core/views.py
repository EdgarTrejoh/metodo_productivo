from uuid import UUID, uuid4

from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from analytics.models import ProductEvent
from leads.forms import ContactForm
from leads.notifications import notify_contact
from .break_even import BreakEvenForm, calculate


def home(request):
    return render(request, 'home.html')


# Estas páginas muestran las secciones de Fase A todavía pendientes.
PAGES = {
    'tools': {
        'template': 'tools.html',
        'eyebrow': 'Herramientas · Fase A',
        'title': 'Calculadoras para preguntas concretas.',
        'intro': 'Usa modelos sencillos para explorar decisiones de tu negocio. Comienza con el punto de equilibrio mensual.',
        'status': 'Calculadora funcional · A-02 aprobada con salvedades',
        'note': 'El cálculo de punto de equilibrio funciona en este entorno de desarrollo; la medición transversal O-08 sigue pendiente.',
        'cards': [
            {'title': 'Punto de equilibrio', 'text': 'Una vista mensual de costos, precio y margen para un producto o servicio.', 'url': 'break_even', 'label': 'Conocer la herramienta'},
            {'title': 'Check PyME', 'text': 'Ocho preguntas para obtener una primera lectura de tus prácticas de gestión.', 'url': 'entry', 'label': 'Abrir el Check disponible'},
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
    if page == 'privacy' and settings.DJANGO_ENV == 'local':
        return render(request, 'privacy.html', {'page': context})
    return render(request, context.get('template', 'section.html'), {'page': context})


@require_http_methods(['GET', 'POST'])
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            submission = form.save()
            ProductEvent.objects.get_or_create(kind='FORM_SUBMITTED', execution=submission.event_id)
            notify_contact(submission)
            messages.success(request, 'Recibimos tu mensaje. Gracias por escribirnos.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


def break_even(request):
    """POST de una interacción; el token de sesión evita reenvíos accidentales."""
    result = None
    if request.method == 'POST':
        submitted = request.POST.get('interaction', '')
        try:
            execution = UUID(submitted)
        except (ValueError, AttributeError, TypeError):
            execution = None
        if execution is None or submitted != request.session.get('break_even_interaction'):
            # El navegador puede reenviar un POST al actualizar. La interacción
            # ya consumida vuelve a un GET vacío sin duplicar los eventos.
            return redirect('break_even')
        else:
            # La siguiente operación recibe un identificador nuevo. Una recarga del
            # POST original no crea eventos adicionales ni guarda los importes.
            request.session['break_even_interaction'] = str(uuid4())
            ProductEvent.objects.get_or_create(kind='TOOL_STARTED', execution=execution)
            form = BreakEvenForm(request.POST)
            if form.is_valid():
                result = calculate(form.cleaned_data)
                ProductEvent.objects.get_or_create(kind='TOOL_COMPLETED', execution=execution)
    else:
        form = BreakEvenForm()
        request.session['break_even_interaction'] = str(uuid4())
    return render(request, 'break_even.html', {
        'form': form,
        'interaction': request.session['break_even_interaction'],
        'result': result,
    })
