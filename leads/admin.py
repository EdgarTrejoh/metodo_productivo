from django.contrib import admin
from django.utils.html import format_html

from .models import ContactSubmission


class ContactSubmissionAdmin(admin.ModelAdmin):
    change_list_template = 'admin/leads/contactsubmission/change_list.html'
    list_display = ('sender', 'status', 'category', 'created_at')
    list_display_links = ('sender', 'created_at')
    list_filter = ('category', 'status')
    search_fields = ('message', 'name', 'email')
    readonly_fields = ('category', 'message', 'name', 'email', 'reply_requested', 'notification_status', 'created_at', 'updated_at')
    fields = ('category', 'message', 'name', 'email', 'reply_requested', 'created_at', 'notification_status', 'status', 'internal_note', 'updated_at')

    @admin.display(description='Remitente')
    def sender(self, obj):
        return format_html(
            '{}<br><small>{}</small>',
            obj.name or 'Sin nombre registrado',
            obj.email or 'Sin correo registrado',
        )

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data') and response.status_code == 200:
            submissions = self.get_queryset(request)
            response.context_data['contact_summary'] = {
                'received': submissions.count(),
                'pending': submissions.filter(status__in=(
                    ContactSubmission.Status.NEW,
                    ContactSubmission.Status.REVIEWING,
                )).count(),
            }
        return response

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
