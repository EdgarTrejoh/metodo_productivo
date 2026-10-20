import re

from django import template
from django.utils.safestring import mark_safe

from content.editorial import normalize_editor_spaces


register = template.Library()
TABLE = re.compile(r'<table\b[^>]*>.*?</table>', re.IGNORECASE | re.DOTALL)


@register.filter
def article_tables(body):
    """Envuelve el HTML previamente saneado para desplazar tablas anchas sin mover la página."""
    body = normalize_editor_spaces(body)
    return mark_safe(TABLE.sub(
        lambda match: '<div class="article-table-scroll" role="region" aria-label="Tabla de datos" tabindex="0">'
        + match.group(0) + '</div>',
        body,
    ))
