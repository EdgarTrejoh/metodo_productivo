import uuid,time,io
from xml.sax.saxutils import escape
from django.conf import settings
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .forms import QuestionForm,CaptureForm,QUESTIONS
from .models import Diagnostic,Orientation
from .services import finalize
from analytics.models import ProductEvent

def current(request):
    context=request.session.get('check')
    if not context:return None
    if time.time()-context.get('last_activity',context['started'])>=settings.CHECK_CONTEXT_TTL_SECONDS:
        request.session.pop('check',None);return None
    return context

def touch(request,context):
    context['last_activity']=time.time()
    request.session['check']=context

def stale_form(request,context):
    return request.POST.get('execution')!=context['execution']

def stale_response(request):
    return render(request,'expired.html',{'stale':True},status=409)

def entry(request):return render(request,'entry.html')
@require_POST
def start(request):
    execution=str(uuid.uuid4())
    now=time.time()
    request.session['check']={'execution':execution,'answers':{},'started':now,'last_activity':now}
    ProductEvent.objects.create(kind='CHECK_STARTED',execution=execution)
    return redirect('question',number=1)

def question(request,number):
    ctx=current(request)
    if not ctx:return redirect('entry')
    if request.method=='POST' and stale_form(request,ctx):return stale_response(request)
    if 'diagnostic' in ctx:return redirect('result')
    if not 1<=number<=8:return redirect('entry')
    for n in range(1,number):
        if str(n) not in ctx['answers']:return redirect('question',number=n)
    form=QuestionForm(request.POST if request.method=='POST' else None,number=number,initial={'answer':ctx['answers'].get(str(number))})
    if request.method=='POST' and form.is_valid():
        ctx['answers'][str(number)]=form.cleaned_data['answer'];touch(request,ctx)
        if number==8:
            ProductEvent.objects.get_or_create(kind='CHECK_COMPLETED',execution=ctx['execution'])
            return redirect('capture')
        return redirect('question',number=number+1)
    if request.method=='GET':touch(request,ctx)
    return render(request,'question.html',{'form':form,'number':number,'previous':number-1,'execution':ctx['execution']})

def capture(request):
    ctx=current(request)
    if not ctx:return redirect('entry')
    if request.method=='POST' and stale_form(request,ctx):return stale_response(request)
    if 'diagnostic' in ctx:return redirect('result')
    for n in range(1,9):
        if str(n) not in ctx['answers']:return redirect('question',number=n)
    form=CaptureForm(request.POST if request.method=='POST' else None)
    if request.method=='POST' and form.is_valid():
        options=[int(ctx['answers'][str(i)]) if i<8 else ctx['answers']['8'] for i in range(1,9)]
        d=finalize(ctx['execution'],options,form.cleaned_data)
        ctx['diagnostic']=str(d.pk);touch(request,ctx)
        return redirect('result')
    if request.method=='GET':touch(request,ctx)
    return render(request,'capture.html',{'form':form,'execution':ctx['execution']})

def active_diagnostic(request,renew=False):
    ctx=current(request)
    if not ctx or 'diagnostic' not in ctx:return None
    diagnostic=Diagnostic.objects.filter(pk=ctx['diagnostic'],execution=ctx['execution']).first()
    if diagnostic and renew:touch(request,ctx)
    return diagnostic

def presentation(d):
    r=d.result
    return {'d':d,'rows':[{'dimension':q['dimension'],'score':r['scores'][i]} for i,q in enumerate(QUESTIONS)],'strengths':[QUESTIONS[i-1]['dimension'] for i in r['strengths']],'gaps':[QUESTIONS[i-1]['dimension'] for i in r['gaps']]}

def result(request):
    d=active_diagnostic(request,renew=True)
    if not d:return render(request,'expired.html',status=410)
    context=presentation(d);context['oriented']=Orientation.objects.filter(diagnostic=d).exists()
    return render(request,'result.html',context)

def pdf(request):
    d=active_diagnostic(request,renew=True)
    if not d:return render(request,'expired.html',status=410)
    context=presentation(d);styles=getSampleStyleSheet();content=[]
    def p(value,style='Normal'):content.extend([Paragraph(escape(str(value)),styles[style]),Spacer(1,10)])
    p('Método Productivo | Check PyME','Title');p('PRUEBA LOCAL - datos sintéticos')
    p(d.contact['company'],'Heading2');p(f"{d.result['score']}/100 | {d.result['level']} | {d.result['raw_score']}/16")
    for row in context['rows']:p(f"{row['dimension']}: {row['score']}/2")
    p('Fortalezas','Heading2');p('; '.join(context['strengths']) or 'No se identifican fortalezas consolidadas.')
    p('Brechas','Heading2');p('; '.join(context['gaps']) or 'No se identifican brechas en las prácticas evaluadas; esto no implica ausencia de riesgos.')
    p('Tres acciones para 30 días','Heading2')
    for a in d.result['actions']:p(a['action']);p('Entregable sugerido: '+a['completion_evidence'])
    p('No inventar datos ni calcular participaciones con total cero. Guarda el PDF; no se recupera al salir. Diagnóstico de prácticas declaradas, no calificación crediticia ni dictamen financiero.')
    p(f"Check {d.result['check_version']} | Catálogo {d.result['catalog_version']} | Selección {d.result['selection_version']}")
    stream=io.BytesIO();SimpleDocTemplate(stream).build(content)
    # No registrar PDF_DOWNLOADED: generar bytes no demuestra recepción completa.
    response=HttpResponse(stream.getvalue(),content_type='application/pdf')
    response['Content-Disposition']='attachment; filename="check-pyme.pdf"'
    return response
@require_POST
def orient(request):
    ctx=current(request)
    if not ctx:return render(request,'expired.html',status=410)
    if stale_form(request,ctx):return stale_response(request)
    d=active_diagnostic(request)
    if not d:return render(request,'expired.html',status=410)
    Orientation.objects.get_or_create(diagnostic=d)
    ProductEvent.objects.get_or_create(kind='ORIENTATION_REQUESTED',execution=d.execution)
    touch(request,ctx)
    return redirect('result')
@require_POST
def exit_check(request):
    ctx=current(request)
    if not ctx:return render(request,'expired.html',status=410)
    if stale_form(request,ctx):return stale_response(request)
    request.session.pop('check',None)
    return redirect('entry')
