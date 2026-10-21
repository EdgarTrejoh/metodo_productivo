import uuid

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


class ContactSubmission(models.Model):
    class Category(models.TextChoices):
        COMMENT = 'comment', 'Comentario'
        REQUEST = 'request', 'Solicitud'

    class Status(models.TextChoices):
        NEW = 'new', 'Nuevo'
        REVIEWING = 'reviewing', 'En seguimiento'
        CLOSED = 'closed', 'Cerrado'

    class NotificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pendiente de configuración'
        SENT = 'sent', 'Enviada'
        FAILED = 'failed', 'Fallida'

    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    category = models.CharField('categoría', max_length=12, choices=Category.choices)
    message = models.TextField('contenido', max_length=3000)
    name = models.CharField('nombre', max_length=120, blank=True)
    email = models.EmailField('correo electrónico', blank=True)
    reply_requested = models.BooleanField('solicita respuesta', default=False)
    status = models.CharField('estado', max_length=12, choices=Status.choices, default=Status.NEW)
    internal_note = models.TextField('nota interna', blank=True)
    notification_status = models.CharField('notificación interna', max_length=12, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    created_at = models.DateTimeField('recibido', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'comentario o solicitud'
        verbose_name_plural = 'comentarios y solicitudes'

    def __str__(self):
        return f'{self.get_category_display()} #{self.pk}'
