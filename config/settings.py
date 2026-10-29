import os
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DJANGO_ENV = os.getenv('DJANGO_ENV', 'local')
if DJANGO_ENV not in ('local', 'staging'):
    raise ImproperlyConfigured('DJANGO_ENV debe ser local o staging.')

DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'
if DJANGO_ENV == 'local' and not DEBUG:
    raise ImproperlyConfigured('DJANGO_DEBUG=0 requiere DJANGO_ENV=staging y su configuración segura.')
if DJANGO_ENV == 'staging' and (DEBUG or os.getenv('DJANGO_DEBUG') != '0'):
    raise ImproperlyConfigured('Staging exige DJANGO_DEBUG=0 explícito.')

def required(name):
    value = os.getenv(name, '').strip()
    if not value or value.startswith('REEMPLAZAR_'):
        raise ImproperlyConfigured(f'Staging exige {name} configurado.')
    return value

if DJANGO_ENV == 'staging':
    SECRET_KEY = required('DJANGO_SECRET_KEY')
    if len(SECRET_KEY) < 50:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY debe tener al menos 50 caracteres en staging.')
    ALLOWED_HOSTS = [host.strip() for host in required('DJANGO_ALLOWED_HOSTS').split(',') if host.strip()]
    if not ALLOWED_HOSTS or any('*' in host or '/' in host or any(char.isspace() for char in host) for host in ALLOWED_HOSTS):
        raise ImproperlyConfigured('Staging exige DJANGO_ALLOWED_HOSTS específicos, sin comodín.')
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in required('DJANGO_CSRF_TRUSTED_ORIGINS').split(',') if origin.strip()]
    if not CSRF_TRUSTED_ORIGINS or any(
        (parts := urlsplit(origin)).scheme != 'https' or not parts.hostname
        or parts.username or parts.password or parts.path or parts.query or parts.fragment
        or '*' in origin
        for origin in CSRF_TRUSTED_ORIGINS
    ):
        raise ImproperlyConfigured('Staging exige orígenes CSRF HTTPS específicos, sin comodín.')
    if required('DB_ENGINE') != 'postgresql':
        raise ImproperlyConfigured('Staging exige DB_ENGINE=postgresql.')
    for name in ('PGDATABASE', 'PGUSER', 'PGPASSWORD', 'PGHOST'):
        required(name)
    required('DJANGO_EMAIL_BACKEND')
else:
    SECRET_KEY = os.getenv('DJANGO_SECRET_KEY') or secrets.token_urlsafe(48)
    ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')

STORE_TEST_CHECKOUT_ENABLED = os.getenv('STORE_TEST_CHECKOUT_ENABLED', '0') == '1'
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'django_otp', 'django_otp.plugins.otp_totp', 'leads', 'diagnostics', 'analytics', 'content', 'store']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django_otp.middleware.OTPMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware', 'core.middleware.CheckContextMiddleware']
if DJANGO_ENV == 'staging':
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
if os.getenv('DB_ENGINE') == 'postgresql':
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.environ['PGDATABASE'], 'USER': os.environ['PGUSER'], 'PASSWORD': os.environ['PGPASSWORD'], 'HOST': os.getenv('PGHOST', 'localhost'), 'PORT': os.getenv('PGPORT', '5432')}}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'dev.sqlite3'}}
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'local_media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
X_FRAME_OPTIONS = 'DENY'
CHECK_CONTEXT_TTL_SECONDS = 30 * 60
EMAIL_BACKEND = os.getenv('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend')
DEFAULT_FROM_EMAIL = 'notificaciones@localhost.invalid'
CONTACT_NOTIFICATION_EMAIL = os.getenv('CONTACT_NOTIFICATION_EMAIL', '').strip()
PRIVATE_RESOURCE_ROOT = Path(os.getenv('PRIVATE_RESOURCE_ROOT', BASE_DIR / 'private_resources')).resolve()

if DJANGO_ENV == 'staging':
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 3600
    # O-02 debe hacer que el proxy reemplace esta cabecera y bloquee acceso directo.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
    }
