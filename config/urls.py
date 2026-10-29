from django.urls import path
from django.http import JsonResponse
from django.conf import settings
from django_otp.admin import OTPAdminSite
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django.contrib.auth.models import User,Group
from django.contrib.auth.admin import UserAdmin,GroupAdmin
from diagnostics import views
from core import views as portal_views
from diagnostics.models import Diagnostic,Orientation
from leads.models import Lead,Consent,ContactSubmission
from leads.admin import ContactSubmissionAdmin
from leads import views as lead_views
from analytics.models import ProductEvent
from content.admin import ArticleAdmin, MediaAssetAdmin, VideoAdmin
from content.models import Article, MediaAsset, Video
from content import views as content_views
from store.admin import DigitalProductAdmin
from store.models import DigitalProduct
from store import views as store_views
from django.contrib import admin
from django.views.generic import RedirectView
site=OTPAdminSite(name='otpadmin')
site.register(User,UserAdmin);site.register(Group,GroupAdmin);site.register(TOTPDevice,TOTPDeviceAdmin)
# Solo lectura en registros del resultado; no editar silenciosamente informes.
class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
for model in (Diagnostic,Lead,Consent,ProductEvent):site.register(model,ReadOnlyAdmin)
class OrientationAdmin(admin.ModelAdmin):
    readonly_fields=('diagnostic','created_at')
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False
site.register(Orientation,OrientationAdmin)
site.register(Article, ArticleAdmin)
site.register(MediaAsset, MediaAssetAdmin)
site.register(Video, VideoAdmin)
site.register(DigitalProduct, DigitalProductAdmin)
site.register(ContactSubmission, ContactSubmissionAdmin)
urlpatterns = [
    path('', portal_views.home, name='home'),
    path('herramientas/', portal_views.section, {'page': 'tools'}, name='tools'),
    path('herramientas/punto-de-equilibrio/', portal_views.break_even, name='break_even'),
    path('recursos/', portal_views.section, {'page': 'resources'}, name='resources'),
    path('recursos/mapa-de-caja-pyme/', lead_views.resource, name='lead_magnet_resource'),
    path('recursos/mapa-de-caja-pyme/gracias/', lead_views.thanks, name='lead_magnet_thanks'),
    path('recursos/mapa-de-caja-pyme/acceso/<str:token>/', lead_views.access, name='lead_magnet_access'),
    path('recursos/flujo-efectivo-13-semanas/', RedirectView.as_view(pattern_name='lead_magnet_resource', permanent=False), name='cash_flow_resource'),
    path('blog/', content_views.index, name='blog'),
    path('blog/<slug:slug>/', content_views.detail, name='article_detail'),
    path('tienda/', store_views.index, name='store'),
    path('tienda/<slug:slug>/', store_views.detail, name='store_detail'),
    path('editorial/media/<uuid:image_id>/', content_views.editorial_image, name='editorial_image'),
    path('contacto/', portal_views.contact, name='contact'),
    path('acerca/', portal_views.section, {'page': 'about'}, name='about'),
    path('privacidad/', portal_views.section, {'page': 'privacy'}, name='privacy'),
    path('terminos/', portal_views.section, {'page': 'terms'}, name='terms'),
    path('health/', lambda r: JsonResponse({'status': 'ok', 'mode': settings.DJANGO_ENV})),
    path('backoffice/', site.urls),
    path('check-pyme/', views.entry, name='entry'),
    path('check-pyme/iniciar/', views.start, name='start'),
    path('check-pyme/pregunta/<int:number>/', views.question, name='question'),
    path('check-pyme/datos/', views.capture, name='capture'),
    path('check-pyme/resultado/', views.result, name='result'),
    path('check-pyme/informe.pdf', views.pdf, name='pdf'),
    path('check-pyme/orientacion/', views.orient, name='orient'),
    path('check-pyme/salir/', views.exit_check, name='exit'),
]
