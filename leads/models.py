from django.db import models
class Lead(models.Model):
    email=models.EmailField(unique=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):return str(self.pk)
class Consent(models.Model):
    lead=models.ForeignKey(Lead,on_delete=models.CASCADE)
    execution=models.UUIDField()
    purpose=models.CharField(max_length=20,choices=[('service','Servicio'),('commercial','Comercial')])
    granted=models.BooleanField()
    text_version=models.CharField(max_length=40)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['execution','purpose'],name='consent_execution_purpose')]
