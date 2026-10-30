"""Configuración administrativa local; todavía no publica el aviso legal."""

from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import EmailValidator, URLValidator


FIELDS = {
    'responsable': {'tipo', 'nombre_legal', 'nombre_comercial', 'domicilio'},
    'privacidad': {
        'correo_arco', 'responsable_atencion', 'canal_alternativo',
        'version_aviso', 'fecha_actualizacion', 'url_aviso_integral', 'proveedores',
    },
}
PROVIDER_FIELDS = {'alojamiento', 'correo'}
PROVIDER_DETAIL_FIELDS = {'nombre', 'ubicacion'}
REQUIRED_FOR_NOTICE = {
    'responsable': ('nombre_legal', 'domicilio'),
    'privacidad': ('correo_arco', 'responsable_atencion', 'version_aviso', 'fecha_actualizacion', 'url_aviso_integral'),
}


def load_site_config(path=None):
    """Lee una sola fuente. La ausencia permite desarrollo con aviso provisional."""
    source = Path(path if path is not None else settings.SITE_CONFIG_PATH)
    try:
        with source.open(encoding='utf-8') as stream:
            data = yaml.safe_load(stream)
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ImproperlyConfigured('No se pudo leer SITE_CONFIG_PATH como YAML válido.') from exc

    if not isinstance(data, dict) or set(data) != set(FIELDS):
        raise ImproperlyConfigured('La configuración administrativa requiere responsable y privacidad.')
    for section, fields in FIELDS.items():
        values = data[section]
        if not isinstance(values, dict) or set(values) != fields:
            raise ImproperlyConfigured(f'La sección {section} tiene campos faltantes o no permitidos.')
        for field, value in values.items():
            if section == 'privacidad' and field == 'proveedores':
                if not isinstance(value, dict) or set(value) != PROVIDER_FIELDS:
                    raise ImproperlyConfigured('privacidad.proveedores requiere alojamiento y correo.')
                for provider, details in value.items():
                    if (not isinstance(details, dict) or set(details) != PROVIDER_DETAIL_FIELDS
                            or any(not isinstance(item, str) for item in details.values())):
                        raise ImproperlyConfigured(f'privacidad.proveedores.{provider} requiere nombre y ubicación de texto.')
                continue
            if not isinstance(value, str):
                raise ImproperlyConfigured(f'{section}.{field} debe ser texto.')
    if data['responsable']['tipo'] != 'persona_fisica':
        raise ImproperlyConfigured('responsable.tipo debe ser persona_fisica.')
    if data['responsable']['nombre_comercial'] != 'Método Productivo':
        raise ImproperlyConfigured('responsable.nombre_comercial debe ser Método Productivo.')

    email = data['privacidad']['correo_arco'].strip()
    if email:
        try:
            EmailValidator()(email)
        except ValidationError as exc:
            raise ImproperlyConfigured('privacidad.correo_arco tiene un formato inválido.') from exc
    updated = data['privacidad']['fecha_actualizacion'].strip()
    if updated:
        try:
            if date.fromisoformat(updated).isoformat() != updated:
                raise ValueError
        except ValueError as exc:
            raise ImproperlyConfigured('privacidad.fecha_actualizacion debe usar AAAA-MM-DD.') from exc
    notice_url = data['privacidad']['url_aviso_integral'].strip()
    if notice_url and notice_url != '/privacidad/':
        parsed = urlsplit(notice_url)
        try:
            URLValidator(schemes=['https'])(notice_url)
        except ValidationError as exc:
            raise ImproperlyConfigured('privacidad.url_aviso_integral debe ser /privacidad/ o una URL HTTPS válida.') from exc
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment):
            raise ImproperlyConfigured('privacidad.url_aviso_integral debe ser /privacidad/ o una URL HTTPS segura.')
    return data


def notice_config_complete(data):
    """Condición necesaria, no aprobación jurídica ni activación del aviso."""
    return data is not None and all(
        data[section][field].strip()
        for section, fields in REQUIRED_FOR_NOTICE.items()
        for field in fields
    ) and all(details['nombre'].strip() and details['ubicacion'].strip()
              for details in data['privacidad']['proveedores'].values())


def require_complete_notice_config(path=None):
    """Punto de control para una futura publicación de C-06/A-08."""
    data = load_site_config(path)
    if not notice_config_complete(data):
        raise ImproperlyConfigured('El aviso definitivo requiere configuración administrativa completa.')
    return data
