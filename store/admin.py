from django.contrib import admin
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import path

from .models import DigitalProduct


class DigitalProductAdmin(admin.ModelAdmin):
    change_form_template = 'admin/store/digitalproduct/change_form.html'
    list_display = ('name', 'version', 'price', 'currency', 'status', 'published_at', 'updated_at')
    list_filter = ('status', 'currency', 'stripe_environment')
    search_fields = ('name', 'slug', 'summary', 'stripe_product_id')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('image',)
    readonly_fields = ('created_at', 'updated_at', 'published_at')
    fields = (
        'name', 'slug', 'summary', 'description', 'benefits', 'image', 'status',
        'version', 'software_requirements', 'contents', 'delivery_terms',
        'price', 'currency', 'private_file_key', 'stripe_environment',
        'stripe_product_id', 'stripe_price_id', 'stripe_test_payment_url',
        'published_at', 'created_at', 'updated_at',
    )
    actions = ('retire_selected',)

    def get_urls(self):
        custom = [path('<path:object_id>/preview/', self.admin_site.admin_view(self.preview), name='store_digitalproduct_preview')]
        return custom + super().get_urls()

    def preview(self, request, object_id):
        product = get_object_or_404(DigitalProduct.objects.select_related('image'), pk=object_id)
        if not self.has_view_or_change_permission(request, product):
            raise Http404
        response = render(request, 'store/detail.html', {'product': product, 'preview': True})
        response['Cache-Control'] = 'private, no-store'
        return response

    @admin.action(description='Retirar productos seleccionados', permissions=['change'])
    def retire_selected(self, request, queryset):
        for product in queryset:
            product.status = 'retired'
            product.save()
