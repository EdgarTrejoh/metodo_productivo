import re
import uuid
import warnings
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image, ImageOps
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from .editorial import sanitize_article_html


YOUTUBE_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
YOUTUBE_HOSTS = {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be', 'www.youtube-nocookie.com'}


def youtube_id(source):
    """Extrae solo un identificador validado; nunca se incorpora HTML del editor."""
    if YOUTUBE_ID.fullmatch(source):
        return source
    parsed = urlparse(source)
    if parsed.scheme != 'https' or parsed.hostname not in YOUTUBE_HOSTS or parsed.username or parsed.password or parsed.port:
        raise ValidationError('Usa un identificador de YouTube o una URL HTTPS válida de YouTube.')
    if parsed.hostname == 'youtu.be':
        candidate = parsed.path.removeprefix('/')
    elif parsed.path == '/watch':
        values = parse_qs(parsed.query).get('v', [])
        candidate = values[0] if len(values) == 1 else ''
    elif parsed.path.startswith('/embed/'):
        candidate = parsed.path.removeprefix('/embed/')
    else:
        candidate = ''
    if not YOUTUBE_ID.fullmatch(candidate):
        raise ValidationError('El enlace debe contener un identificador válido de YouTube.')
    return candidate


class PublicationStatus(models.TextChoices):
    DRAFT = 'draft', 'Borrador'
    PUBLISHED = 'published', 'Publicado'
    RETIRED = 'retired', 'Retirado'


def image_upload_path(instance, filename):
    return f'editorial/original/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'


def thumbnail_upload_path(instance, filename):
    return f'editorial/thumb/{uuid.uuid4().hex}.webp'


class MediaAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('nombre descriptivo', max_length=180)
    alt_text = models.CharField('texto alternativo', max_length=250)
    description = models.CharField('descripción', max_length=500, blank=True)
    image = models.ImageField('imagen', upload_to=image_upload_path)
    thumbnail = models.ImageField('miniatura', upload_to=thumbnail_upload_path, editable=False)
    created_at = models.DateTimeField('creado', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'imagen editorial'
        verbose_name_plural = 'imágenes editoriales'

    def clean(self):
        super().clean()
        if self.image and not self.image._committed:
            file = self.image.file
            if file.size > 5 * 1024 * 1024:
                raise ValidationError({'image': 'La imagen no debe superar 5 MB.'})
            extension = Path(self.image.name).suffix.lower()
            expected = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}.get(extension)
            if not expected:
                raise ValidationError({'image': 'Utiliza una imagen JPG, PNG o WebP.'})
            try:
                file.seek(0)
                with warnings.catch_warnings():
                    warnings.simplefilter('error', Image.DecompressionBombWarning)
                    with Image.open(file) as picture:
                        if picture.format != expected or picture.width * picture.height > 24_000_000:
                            raise ValueError('Formato o dimensiones no admitidos.')
                        picture.verify()
                file.seek(0)
            except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
                raise ValidationError({'image': 'El contenido de la imagen es inválido o excesivo.'}) from error

    def save(self, *args, **kwargs):
        prior = type(self).objects.filter(pk=self.pk).first() if self.pk else None
        self.full_clean()
        if self.image and not self.image._committed:
            with Image.open(self.image.file) as uploaded:
                picture = ImageOps.exif_transpose(uploaded)
                output_format = uploaded.format
                if output_format == 'JPEG':
                    picture = picture.convert('RGB')
                output = BytesIO()
                picture.save(output, format=output_format)
                extension = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}[output_format]
                self.image = ContentFile(output.getvalue(), name=f'{uuid.uuid4().hex}{extension}')
                preview = picture.copy()
                preview.thumbnail((360, 240))
                thumb = BytesIO()
                preview.save(thumb, format='WEBP', quality=80)
                self.thumbnail = ContentFile(thumb.getvalue(), name=f'{uuid.uuid4().hex}.webp')
        super().save(*args, **kwargs)
        if prior:
            for previous, current in ((prior.image, self.image), (prior.thumbnail, self.thumbnail)):
                if previous and previous.name != current.name:
                    transaction.on_commit(lambda storage=previous.storage, name=previous.name: storage.delete(name))

    @property
    def public_url(self):
        return reverse('editorial_image', args=[self.pk])

    @property
    def thumbnail_url(self):
        return f'{self.public_url}?thumb=1'

    def __str__(self):
        return self.name


class Video(models.Model):
    class Provider(models.TextChoices):
        YOUTUBE = 'youtube', 'YouTube'

    title = models.CharField('título', max_length=180)
    description = models.TextField('descripción', max_length=1000)
    provider = models.CharField('proveedor', max_length=20, choices=Provider.choices, default=Provider.YOUTUBE)
    source = models.CharField('ID o URL de YouTube', max_length=250)
    video_id = models.CharField('ID validado', max_length=11, editable=False)
    status = models.CharField('estado', max_length=12, choices=PublicationStatus.choices, default=PublicationStatus.DRAFT)
    published_at = models.DateTimeField('fecha de publicación', blank=True, null=True)
    created_at = models.DateTimeField('creado', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        ordering = ['-published_at', '-pk']
        verbose_name = 'video'
        verbose_name_plural = 'videos'

    def clean(self):
        super().clean()
        if self.provider != self.Provider.YOUTUBE:
            raise ValidationError({'provider': 'Proveedor no admitido.'})
        try:
            self.video_id = youtube_id(self.source)
        except ValidationError as error:
            raise ValidationError({'source': error.messages}) from error

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status == PublicationStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def external_url(self):
        return f'https://www.youtube.com/watch?v={self.video_id}'

    @classmethod
    def live(cls):
        return cls.objects.filter(status=PublicationStatus.PUBLISHED, published_at__lte=timezone.now())

    def __str__(self):
        return self.title


class Article(models.Model):
    class Category(models.TextChoices):
        FINANCE = 'finance', 'Finanzas'
        BUSINESS = 'business', 'Negocios'
        DATA = 'data', 'Datos'
        TECHNOLOGY = 'technology', 'Tecnología'

    class Cta(models.TextChoices):
        CHECK = 'entry', 'Check PyME'
        CALCULATOR = 'break_even', 'Calculadora de punto de equilibrio'
        TOOLS = 'tools', 'Herramientas'
        RESOURCES = 'resources', 'Recursos'

    title = models.CharField('título', max_length=180)
    slug = models.SlugField('slug', max_length=180, unique=True)
    summary = models.CharField('resumen', max_length=360)
    body = models.TextField('contenido editorial', help_text='Edita visualmente; el servidor limita etiquetas, enlaces e imágenes autorizadas.')
    category = models.CharField('categoría', max_length=20, choices=Category.choices)
    seo_title = models.CharField('título SEO', max_length=180, blank=True)
    seo_description = models.CharField('descripción SEO', max_length=300, blank=True)
    cta_target = models.CharField('CTA contextual', max_length=20, choices=Cta.choices, default=Cta.CHECK)
    featured_video = models.ForeignKey(Video, verbose_name='video relacionado', blank=True, null=True, on_delete=models.SET_NULL)
    featured_image = models.ForeignKey(MediaAsset, verbose_name='imagen destacada', blank=True, null=True, on_delete=models.PROTECT, related_name='featured_articles')
    status = models.CharField('estado', max_length=12, choices=PublicationStatus.choices, default=PublicationStatus.DRAFT)
    published_at = models.DateTimeField('fecha de publicación', blank=True, null=True)
    created_at = models.DateTimeField('creado', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        ordering = ['-published_at', '-pk']
        verbose_name = 'artículo'
        verbose_name_plural = 'artículos'

    def clean(self):
        super().clean()
        try:
            self.body, image_ids = sanitize_article_html(self.body or '')
        except ValidationError as error:
            raise ValidationError({'body': error.messages}) from error
        if image_ids and MediaAsset.objects.filter(pk__in=image_ids).count() != len(image_ids):
            raise ValidationError({'body': 'Una imagen insertada ya no existe en la biblioteca.'})
        self._inline_image_ids = image_ids

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status == PublicationStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        with transaction.atomic():
            super().save(*args, **kwargs)
            ArticleImageUsage.objects.filter(article=self).exclude(image_id__in=self._inline_image_ids).delete()
            existing = set(ArticleImageUsage.objects.filter(article=self).values_list('image_id', flat=True))
            ArticleImageUsage.objects.bulk_create(
                ArticleImageUsage(article=self, image_id=image_id)
                for image_id in self._inline_image_ids - {str(value) for value in existing}
            )

    @classmethod
    def live(cls):
        return cls.objects.filter(status=PublicationStatus.PUBLISHED, published_at__lte=timezone.now())

    def __str__(self):
        return self.title


class ArticleImageUsage(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='inline_image_usages')
    image = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, related_name='inline_usages')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['article', 'image'], name='unique_article_inline_image')]


@receiver(post_delete, sender=MediaAsset)
def remove_unused_media_files(sender, instance, **kwargs):
    for file in (instance.image, instance.thumbnail):
        if file:
            transaction.on_commit(lambda storage=file.storage, name=file.name: storage.delete(name))
