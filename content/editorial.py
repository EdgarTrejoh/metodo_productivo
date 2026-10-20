import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

import nh3
from django.core.exceptions import ValidationError


IMAGE_URL = re.compile(r'^/editorial/media/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$')
ALLOWED_TAGS = {
    'p', 'h2', 'h3', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'img', 'br', 'blockquote',
    'table', 'caption', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
}
TABLE_ID = re.compile(r'^(?:row|cell)-[a-zA-Z0-9]{1,24}$')
TABLE_ALIGN = {'ql-align-left', 'ql-align-center', 'ql-align-right'}
NONBREAKING_SPACE = re.compile(r'&nbsp;|&#0*160;|&#x0*a0;|\u00a0', re.IGNORECASE)


def normalize_editor_spaces(source):
    """Quill puede emitir espacios no separables entre palabras comunes."""
    return NONBREAKING_SPACE.sub(' ', source)


class ImageReferences(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        if tag != 'img':
            return
        values = dict(attrs)
        match = IMAGE_URL.fullmatch(values.get('src') or '')
        if not match:
            raise ValidationError('Solo se permiten imágenes de la biblioteca editorial.')
        if not (values.get('alt') or '').strip():
            raise ValidationError('Cada imagen insertada necesita texto alternativo.')
        self.ids.add(match.group(1))


def safe_link(value):
    value = value.strip()
    if not value or '\\' in value or any(character.isspace() or ord(character) < 32 for character in value):
        return None
    if value.startswith('/') and not value.startswith('//'):
        return value
    parsed = urlsplit(value)
    if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password:
        return value
    if parsed.scheme == 'mailto' and parsed.path and not parsed.netloc:
        return value
    return None


def sanitize_article_html(source):
    source = normalize_editor_spaces(source)
    if len(source) > 100_000:
        raise ValidationError('El contenido del artículo es demasiado extenso.')
    references = ImageReferences()
    references.feed(source)
    references.close()

    def keep_attribute(tag, attribute, value):
        if tag == 'a' and attribute == 'href':
            return safe_link(value)
        if tag == 'a' and attribute == 'title':
            return value[:200]
        if tag == 'img' and attribute == 'src':
            return value if IMAGE_URL.fullmatch(value) else None
        if tag == 'img' and attribute == 'alt':
            return value[:250] if value.strip() else None
        if tag == 'table' and attribute == 'class':
            return value if value == 'ql-table-better' else None
        if tag == 'p' and attribute == 'class':
            classes = set(value.split())
            if classes and classes <= ({'ql-table-block'} | TABLE_ALIGN):
                return ' '.join(name for name in ('ql-table-block', 'ql-align-left', 'ql-align-center', 'ql-align-right') if name in classes)
            return None
        if tag in {'th', 'td'} and attribute == 'data-row':
            return value if TABLE_ID.fullmatch(value) and value.startswith('row-') else None
        if tag == 'p' and attribute == 'data-cell':
            return value if TABLE_ID.fullmatch(value) and value.startswith('cell-') else None
        if tag in {'th', 'td'} and attribute in {'colspan', 'rowspan'}:
            return value if value.isascii() and value.isdecimal() and 1 <= int(value) <= 20 else None
        if tag == 'th' and attribute == 'scope':
            return value if value in {'col', 'row'} else None
        return None

    cleaned = nh3.clean(
        source,
        tags=ALLOWED_TAGS,
        clean_content_tags={'script', 'style', 'iframe', 'object', 'svg', 'form'},
        attributes={
            'a': {'href', 'title'}, 'img': {'src', 'alt'}, 'table': {'class'},
            'p': {'class', 'data-cell'}, 'th': {'data-row', 'colspan', 'rowspan', 'scope'},
            'td': {'data-row', 'colspan', 'rowspan'},
        },
        attribute_filter=keep_attribute,
        url_schemes={'https', 'mailto'},
        link_rel='noopener noreferrer',
    )
    return cleaned, references.ids
