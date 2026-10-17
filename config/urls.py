from django.urls import path
from django.http import JsonResponse
from django_otp.admin import OTPAdminSite
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django.contrib.auth.models import User,Group
from django.contrib.auth.admin import UserAdmin,GroupAdmin
from diagnostics import views
from core import views as portal_views
from diagnostics.models import Diagnostic,Orientation
from leads.models import Lead,Consent
from analytics.models import ProductEvent
from django.contrib import admin
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
urlpatterns = [
    path('', portal_views.home, name='home'),
    path('herramientas/', portal_views.section, {'page': 'tools'}, name='tools'),
    path('herramientas/punto-de-equilibrio/', portal_views.section, {'page': 'break_even'}, name='break_even'),
    path('recursos/', portal_views.section, {'page': 'resources'}, name='resources'),
    path('recursos/flujo-efectivo-13-semanas/', portal_views.section, {'page': 'cash_flow_resource'}, name='cash_flow_resource'),
    path('blog/', portal_views.section, {'page': 'blog'}, name='blog'),
    path('contacto/', portal_views.section, {'page': 'contact'}, name='contact'),
    path('acerca/', portal_views.section, {'page': 'about'}, name='about'),
    path('privacidad/', portal_views.section, {'page': 'privacy'}, name='privacy'),
    path('terminos/', portal_views.section, {'page': 'terms'}, name='terms'),
    path('health/', lambda r: JsonResponse({'status': 'ok', 'mode': 'development'})),
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
