from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice

from analytics.models import ProductEvent
from .models import Consent, ContactSubmission, Lead


class ContactTests(TestCase):
    def payload(self, category='comment', **overrides):
        data = {'category': category, 'message': 'Mensaje sintético.', 'name': 'Persona de prueba', 'email': 'persona@example.invalid'}
        data.update(overrides)
        return data

    def test_name_and_email_required_for_both_categories(self):
        for category in ('comment', 'request'):
            for field, error in (('name', 'Escribe tu nombre.'), ('email', 'Escribe tu correo electrónico.')):
                with self.subTest(category=category, field=field):
                    response = self.client.post(reverse('contact'), self.payload(category, **{field: ''}))
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, error)
                    self.assertContains(response, 'Mensaje sintético.')
                    self.assertContains(response, 'persona@example.invalid' if field == 'name' else 'Persona de prueba')
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_invalid_email_is_rejected_for_both_categories(self):
        for category in ('comment', 'request'):
            with self.subTest(category=category):
                response = self.client.post(reverse('contact'), self.payload(category, email='no-es-correo'))
                self.assertContains(response, 'Escribe un correo electrónico válido.')
                self.assertContains(response, 'value="no-es-correo"')
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_message_limit_and_removed_checkbox_are_enforced(self):
        response = self.client.post(reverse('contact'), self.payload(message='x' * 3001))
        self.assertContains(response, 'El mensaje no debe superar 3000 caracteres.')
        self.assertEqual(ContactSubmission.objects.count(), 0)
        self.client.post(reverse('contact'), self.payload(reply_requested='on'))
        self.assertFalse(ContactSubmission.objects.get().reply_requested)

    def test_valid_comment_and_request_are_saved_and_confirmed(self):
        for category, reply_requested in (('comment', False), ('request', True)):
            with self.subTest(category=category):
                response = self.client.post(reverse('contact'), self.payload(category), follow=True)
                self.assertRedirects(response, reverse('contact'))
                self.assertContains(response, 'Recibimos tu mensaje')
                item = ContactSubmission.objects.filter(category=category).get()
                self.assertEqual(item.status, ContactSubmission.Status.NEW)
                self.assertEqual(item.notification_status, ContactSubmission.NotificationStatus.PENDING)
                self.assertEqual(item.name, 'Persona de prueba')
                self.assertEqual(item.email, 'persona@example.invalid')
                self.assertEqual(item.reply_requested, reply_requested)
                self.assertEqual(ProductEvent.objects.filter(kind='FORM_SUBMITTED', execution=item.event_id).count(), 1)
                self.assertNotContains(self.client.get(reverse('contact')), 'Recibimos tu mensaje')
        self.assertEqual(ContactSubmission.objects.count(), 2)
        self.assertEqual(Lead.objects.count(), 0)
        self.assertEqual(Consent.objects.count(), 0)
        self.assertNotContains(self.client.get(reverse('contact')), 'reply_requested')

    def test_historical_record_without_contact_remains_accessible(self):
        legacy = ContactSubmission.objects.create(category='comment', message='Registro histórico sintético.', name='', email='')
        self.assertEqual(ContactSubmission.objects.get(pk=legacy.pk).name, '')
        self.assertEqual(ContactSubmission.objects.get(pk=legacy.pk).email, '')

    def test_required_fields_and_category_are_validated(self):
        response = self.client.post(reverse('contact'), {'category': 'invalid', 'message': ' '})
        self.assertContains(response, 'Selecciona una categoría válida')
        self.assertContains(response, 'Escribe tu mensaje')
        self.assertEqual(ContactSubmission.objects.count(), 0)

    @override_settings(CONTACT_NOTIFICATION_EMAIL='operacion@example.invalid')
    def test_notification_contains_no_personal_or_message_content(self):
        response = self.client.post(reverse('contact'), {
            'category': 'request', 'message': 'Contenido privado sintético',
            'name': 'Persona de prueba', 'email': 'persona@example.invalid',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn('Contenido privado', mail.outbox[0].body)
        self.assertNotIn('persona@example', mail.outbox[0].body)
        item = ContactSubmission.objects.get()
        self.assertEqual(item.notification_status, ContactSubmission.NotificationStatus.SENT)
        self.assertTrue(item.reply_requested)

    @override_settings(CONTACT_NOTIFICATION_EMAIL='operacion@example.invalid')
    @patch('leads.notifications.send_mail', side_effect=RuntimeError('fallo sintético'))
    def test_mail_failure_preserves_submission_and_marks_failure(self, _):
        response = self.client.post(reverse('contact'), self.payload(), follow=True)
        self.assertContains(response, 'Recibimos tu mensaje')
        item = ContactSubmission.objects.get()
        self.assertEqual(item.notification_status, ContactSubmission.NotificationStatus.FAILED)
        self.assertEqual(ProductEvent.objects.filter(kind='EMAIL_FAILED', execution=item.event_id).count(), 1)

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse('contact'), self.payload())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_admin_requires_otp_and_authorized_permission(self):
        item = ContactSubmission.objects.create(category='comment', message='Mensaje completo de prueba')
        url = reverse('otpadmin:leads_contactsubmission_change', args=[item.pk])
        inbox = reverse('otpadmin:leads_contactsubmission_changelist')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.get(inbox).status_code, 302)
        user = get_user_model().objects.create_user('staff-contact', password='prueba-no-real', is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(url).status_code, 302)
        device = TOTPDevice.objects.create(user=user, name='prueba', confirmed=True)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        self.assertIn(self.client.get(url).status_code, (403, 404))
        self.assertIn(self.client.get(inbox).status_code, (403, 404))
        user.user_permissions.add(*Permission.objects.filter(codename__in=['view_contactsubmission', 'change_contactsubmission']))
        ContactSubmission.objects.create(category='comment', message='Otro comentario sintético', name='Remitente sintético', email='remitente@example.invalid')
        ContactSubmission.objects.create(category='request', message='Solicitud ya cerrada', name='Otra persona sintética', email='otra@example.invalid', status=ContactSubmission.Status.CLOSED)
        listing = self.client.get(inbox)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.context_data['contact_summary'], {'received': 3, 'pending': 2})
        self.assertContains(listing, 'Remitente sintético')
        self.assertContains(listing, 'remitente@example.invalid')
        self.assertContains(listing, 'Pendientes')
        self.assertContains(listing, 'category__exact=comment')
        self.assertContains(listing, 'status__exact=new')
        filtered = self.client.get(inbox, {'category__exact': 'request'})
        self.assertContains(filtered, 'Otra persona sintética')
        self.assertNotContains(filtered, 'Remitente sintético')
        self.assertEqual(filtered.context_data['contact_summary'], {'received': 3, 'pending': 2})
        filtered_status = self.client.get(inbox, {'status__exact': 'closed'})
        self.assertContains(filtered_status, 'Otra persona sintética')
        self.assertNotContains(filtered_status, 'Remitente sintético')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mensaje completo de prueba')
        response = self.client.post(url, {'status': 'reviewing', 'internal_note': 'Seguimiento sintético', '_save': 'Guardar'})
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, ContactSubmission.Status.REVIEWING)
        self.assertEqual(item.internal_note, 'Seguimiento sintético')
        self.assertEqual(self.client.get(inbox).context_data['contact_summary']['pending'], 2)
        self.client.post(url, {'status': 'closed', 'internal_note': 'Cerrado sintético', '_save': 'Guardar'})
        self.assertEqual(self.client.get(inbox).context_data['contact_summary']['pending'], 1)
        self.assertNotContains(self.client.get(reverse('contact')), 'Otro comentario sintético')

    def test_empty_inbox_shows_zero_counts(self):
        user = get_user_model().objects.create_user('inbox-empty-qa', password='solo-prueba', is_staff=True, is_superuser=True)
        self.client.force_login(user)
        device = TOTPDevice.objects.create(user=user, name='prueba', confirmed=True)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        response = self.client.get(reverse('otpadmin:leads_contactsubmission_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['contact_summary'], {'received': 0, 'pending': 0})
