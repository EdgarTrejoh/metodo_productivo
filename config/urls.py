from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django_otp.admin import OTPAdminSite
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django.contrib.auth.models import User,Group
from django.contrib.auth.admin import UserAdmin,GroupAdmin
from diagnostics import views
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
urlpatterns=[path('',lambda r:render(r,'home.html'),name='home'),path('health/',lambda r:JsonResponse({'status':'ok','mode':'development'})),path('backoffice/',site.urls),path('check-pyme/',views.entry,name='entry'),path('check-pyme/iniciar/',views.start,name='start'),path('check-pyme/pregunta/<int:number>/',views.question,name='question'),path('check-pyme/datos/',views.capture,name='capture'),path('check-pyme/resultado/',views.result,name='result'),path('check-pyme/informe.pdf',views.pdf,name='pdf'),path('check-pyme/orientacion/',views.orient,name='orient'),path('check-pyme/salir/',views.exit_check,name='exit')]
