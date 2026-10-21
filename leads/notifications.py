from django.conf import settings
from django.core.mail import send_mail

from analytics.models import ProductEvent
from .models import ContactSubmission


def notify_contact(submission):
    """La solicitud ya está guardada; un fallo de correo nunca la revierte."""
    recipient = settings.CONTACT_NOTIFICATION_EMAIL
    if not recipient:
        return
    try:
        delivered = send_mail(
            subject=f'Método Productivo: nuevo contacto #{submission.pk}',
            message=f'Se recibió un contacto de tipo {submission.get_category_display()}.\nRevísalo en el backoffice: /backoffice/leads/contactsubmission/{submission.pk}/',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        if delivered != 1:
            raise RuntimeError('La notificación no fue aceptada por el backend de correo.')
    except Exception:
        # La información del fallo queda en el estado operativo, sin registrar datos personales.
        submission.notification_status = ContactSubmission.NotificationStatus.FAILED
        ProductEvent.objects.get_or_create(kind='EMAIL_FAILED', execution=submission.event_id)
    else:
        submission.notification_status = ContactSubmission.NotificationStatus.SENT
    submission.save(update_fields=['notification_status', 'updated_at'])
