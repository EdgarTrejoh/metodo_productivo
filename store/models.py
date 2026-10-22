import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from content.models import MediaAsset, PublicationStatus


TEST_PAYMENT_LINK = re.compile(r'https://buy\.stripe\.com/test_[A-Za-z0-9]+\Z')


class DigitalProduct(models.Model):
    class StripeEnvironment(models.TextChoices):
        TEST = 'test', 'TEST'
        LIVE = 'live', 'LIVE'

    name = models.CharField('nombre', max_length=180)
    slug = models.SlugField('slug', max_length=180, unique=True)
    summary = models.CharField('resumen', max_length=360, blank=True)
    description = models.TextField('descripción', blank=True)
    benefits = models.TextField('beneficios', blank=True, help_text='Un beneficio comprobable por línea. Se muestra como texto, sin HTML.')
    image = models.ForeignKey(MediaAsset, verbose_name='imagen', null=True, blank=True, on_delete=models.PROTECT, related_name='store_products')
    status = models.CharField('estado', max_length=12, choices=PublicationStatus.choices, default=PublicationStatus.DRAFT)
    version = models.CharField('versión visible', max_length=40, blank=True)
    software_requirements = models.TextField('requisitos de software', blank=True)
    contents = models.TextField('contenido del producto', blank=True)
    delivery_terms = models.TextField('condiciones de entrega', blank=True)
    price = models.DecimalField('precio', max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField('moneda ISO 4217', max_length=3, default='MXN')
    stripe_environment = models.CharField('entorno Stripe', max_length=4, choices=StripeEnvironment.choices, blank=True)
    stripe_product_id = models.CharField('Stripe Product ID', max_length=100, blank=True)
    stripe_price_id = models.CharField('Stripe Price ID', max_length=100, blank=True)
    stripe_test_payment_url = models.URLField(
        'Enlace de pago Stripe TEST', max_length=500, blank=True,
        help_text='Solo para el piloto local. Usa un Payment Link HTTPS de buy.stripe.com/test_; no habilita ventas reales ni entrega archivos.',
    )
    private_file_key = models.SlugField('identificador lógico del archivo privado', max_length=180, blank=True)
    created_at = models.DateTimeField('creado', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado', auto_now=True)
    published_at = models.DateTimeField('publicado', null=True, blank=True)

    class Meta:
        ordering = ['-published_at', '-pk']
        verbose_name = 'producto digital'
        verbose_name_plural = 'productos digitales'

    def clean(self):
        super().clean()
        errors = {}
        self.currency = (self.currency or '').upper()
        if not re.fullmatch(r'[A-Z]{3}', self.currency):
            errors['currency'] = 'Indica una moneda con tres letras ISO, por ejemplo MXN.'
        if self.price is not None and self.price <= 0:
            errors['price'] = 'El precio debe ser mayor que cero.'
        if self.stripe_product_id and not re.fullmatch(r'prod_[A-Za-z0-9]+', self.stripe_product_id):
            errors['stripe_product_id'] = 'Indica un ID de producto Stripe válido.'
        if self.stripe_price_id and not re.fullmatch(r'price_[A-Za-z0-9]+', self.stripe_price_id):
            errors['stripe_price_id'] = 'Indica un ID de precio Stripe válido.'
        if (self.stripe_product_id or self.stripe_price_id) and not self.stripe_environment:
            errors['stripe_environment'] = 'Identifica si las referencias son TEST o LIVE.'
        if self.stripe_test_payment_url:
            if not TEST_PAYMENT_LINK.fullmatch(self.stripe_test_payment_url):
                errors['stripe_test_payment_url'] = 'Usa exclusivamente un Payment Link HTTPS de buy.stripe.com/test_.'
            if self.stripe_environment != self.StripeEnvironment.TEST:
                errors['stripe_environment'] = 'Un enlace de pago de prueba requiere el entorno TEST.'
        if self.status == PublicationStatus.PUBLISHED:
            for field in ('summary', 'description', 'benefits', 'version', 'software_requirements', 'contents', 'delivery_terms', 'private_file_key'):
                if not getattr(self, field).strip():
                    errors[field] = 'Completa este campo antes de publicar.'
            if self.price is None:
                errors['price'] = 'Indica el precio antes de publicar.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status == PublicationStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @classmethod
    def live(cls):
        return cls.objects.filter(status=PublicationStatus.PUBLISHED, published_at__lte=timezone.now())

    def __str__(self):
        return self.name

    @property
    def has_valid_test_payment_url(self):
        return bool(
            self.stripe_environment == self.StripeEnvironment.TEST
            and TEST_PAYMENT_LINK.fullmatch(self.stripe_test_payment_url or '')
        )
