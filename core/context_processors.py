"""Prepara los datos administrativos solo en el contexto de Privacidad."""

from .site_config import load_site_config, notice_config_complete


def privacy_administration(request):
    if not request.resolver_match or request.resolver_match.url_name != 'privacy':
        return {}
    data = load_site_config()
    return {
        'site_admin_config': data,
        'site_admin_config_ready': notice_config_complete(data),
    }
