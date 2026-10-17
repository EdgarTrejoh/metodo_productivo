import uuid
from django.db import models
from leads.models import Lead
class Diagnostic(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    execution=models.UUIDField(unique=True)
    lead=models.ForeignKey(Lead,on_delete=models.CASCADE)
    contact=models.JSONField()
    answers=models.JSONField()
    result=models.JSONField()
    finalized_at=models.DateTimeField(auto_now_add=True)
    retention_until=models.DateTimeField()
class Orientation(models.Model):
    diagnostic=models.OneToOneField(Diagnostic,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=20,default='new',choices=[('new','Nuevo'),('contacted','Contactado'),('closed','Cerrado')])
