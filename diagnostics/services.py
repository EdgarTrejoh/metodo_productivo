import calendar
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from leads.models import Lead,Consent
from analytics.models import ProductEvent
from .models import Diagnostic
from .domain import score_answers

def plus_year(value):
    # 12 meses calendario, incluye 29 de febrero.
    return value.replace(year=value.year+1,day=min(value.day,calendar.monthrange(value.year+1,value.month)[1]))
@transaction.atomic
def finalize(execution,options,data):
    existing=Diagnostic.objects.filter(execution=execution).first()
    if existing:return existing
    result=score_answers(options)
    lead,new=Lead.objects.get_or_create(email=data['email'])
    # Bloqueo del lead serializa envíos concurrentes de esa ejecución en PostgreSQL.
    lead=Lead.objects.select_for_update().get(pk=lead.pk)
    existing=Diagnostic.objects.filter(execution=execution).first()
    if existing:return existing
    d=Diagnostic.objects.create(execution=execution,lead=lead,contact={k:data[k] for k in ('name','email','company','whatsapp')},answers=options,result=result,retention_until=plus_year(timezone.now()))
    for purpose,value in [('service',True),('commercial',data['commercial'])]:
        Consent.objects.create(lead=lead,execution=execution,purpose=purpose,granted=value,text_version='demo-local-v0.1-no-legal')
    for kind in ['CHECK_CONTACT_SUBMITTED','DIAGNOSIS_RELEASED']+(['LEAD_CREATED'] if new else []):
        ProductEvent.objects.get_or_create(kind=kind,execution=execution)
    return d
