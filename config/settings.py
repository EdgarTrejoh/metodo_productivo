import os,secrets
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
BASE_DIR=Path(__file__).resolve().parent.parent
DEBUG=os.getenv('DJANGO_DEBUG','1')=='1'
# Esta entrega es exclusivamente de desarrollo. Evita una publicación accidental.
if not DEBUG:
    raise ImproperlyConfigured('Bloque inicial no habilitado para producción. Revisar docs/ESTADO.md.')
SECRET_KEY=os.getenv('DJANGO_SECRET_KEY') or secrets.token_urlsafe(48)
ALLOWED_HOSTS=os.getenv('DJANGO_ALLOWED_HOSTS','localhost,127.0.0.1,testserver').split(',')
INSTALLED_APPS=['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','django_otp','django_otp.plugins.otp_totp','leads','diagnostics','analytics','content']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django_otp.middleware.OTPMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware','core.middleware.CheckContextMiddleware']
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='config.wsgi.application'
if os.getenv('DB_ENGINE')=='postgresql':
    DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':os.environ['PGDATABASE'],'USER':os.environ['PGUSER'],'PASSWORD':os.environ['PGPASSWORD'],'HOST':os.getenv('PGHOST','localhost'),'PORT':os.getenv('PGPORT','5432')}}
else:
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'dev.sqlite3'}}
LANGUAGE_CODE='es-mx'
TIME_ZONE='America/Mexico_City'
USE_I18N=True
USE_TZ=True
STATIC_URL='static/'
STATICFILES_DIRS=[BASE_DIR/'static']
MEDIA_ROOT=BASE_DIR/'local_media'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE=True
X_FRAME_OPTIONS='DENY'
CHECK_CONTEXT_TTL_SECONDS=int(os.getenv('CHECK_CONTEXT_TTL_SECONDS','1800'))
if not 60<=CHECK_CONTEXT_TTL_SECONDS<=86400:
    raise ImproperlyConfigured('TTL de desarrollo inválido')
EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
