import re
import uuid
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import connection, models, transaction
from django.db.models import Q
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


class ProtectedWriteQuerySet(models.QuerySet):
    protected_fields = frozenset()

    def update(self, **kwargs):
        if self.protected_fields.intersection(kwargs):
            raise ValidationError('Esta operación requiere el servicio transaccional.')
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if self.protected_fields.intersection(fields):
            raise ValidationError('Esta operación requiere el servicio transaccional.')
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, objs, *args, **kwargs):
        raise ValidationError('La creación masiva requiere un proceso transaccional auditado.')


class OrderQuerySet(ProtectedWriteQuerySet):
    protected_fields = frozenset((
        'public_id', 'creation_key', 'product', 'product_id', 'environment',
        'product_name_snapshot', 'product_version_snapshot', 'amount_minor', 'currency',
        'delivery_terms_snapshot', 'stripe_product_id_snapshot', 'stripe_price_id_snapshot',
        'file_key_snapshot', 'file_revision_snapshot', 'file_sha256_snapshot',
        'file_size_bytes_snapshot',
        'state', 'paid_at', 'closed_at', 'closed_reason',
    ))


class PaymentAttemptQuerySet(ProtectedWriteQuerySet):
    protected_fields = frozenset((
        'order', 'order_id', 'operation_id', 'request_idempotency_key', 'attempt_number',
        'provider', 'provider_account_id', 'environment', 'amount_minor', 'currency',
        'state', 'completed_at', 'result_code',
    ))


class AuditEventQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Los eventos de auditoría no pueden modificarse.')

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Los eventos de auditoría no pueden modificarse.')

    def delete(self):
        raise ValidationError('Los eventos de auditoría no pueden eliminarse.')

    def bulk_create(self, objs, *args, **kwargs):
        raise ValidationError('Los eventos de auditoría requieren inserción individual.')


class Order(models.Model):
    class State(models.TextChoices):
        CREATED = 'created', 'Creada'
        AWAITING_PAYMENT = 'awaiting_payment', 'En espera de pago'
        PAID = 'paid', 'Pagada'
        CLOSED_UNPAID = 'closed_unpaid', 'Cerrada sin pago'
        REVIEW = 'review', 'Revisión'

    IMMUTABLE_FIELDS = (
        'public_id', 'creation_key', 'product_id', 'environment', 'product_name_snapshot',
        'product_version_snapshot', 'amount_minor', 'currency',
        'delivery_terms_snapshot', 'stripe_product_id_snapshot',
        'stripe_price_id_snapshot', 'file_key_snapshot',
        'file_revision_snapshot', 'file_sha256_snapshot',
        'file_size_bytes_snapshot',
    )

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creation_key = models.UUIDField(unique=True, editable=False)
    product = models.ForeignKey(DigitalProduct, on_delete=models.PROTECT, related_name='orders')
    environment = models.CharField(max_length=4, choices=DigitalProduct.StripeEnvironment.choices)
    state = models.CharField(max_length=20, choices=State.choices, default=State.CREATED)
    product_name_snapshot = models.CharField(max_length=180)
    product_version_snapshot = models.CharField(max_length=40)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default='MXN')
    delivery_terms_snapshot = models.TextField()
    stripe_product_id_snapshot = models.CharField(max_length=100, blank=True)
    stripe_price_id_snapshot = models.CharField(max_length=100, blank=True)
    file_key_snapshot = models.CharField(max_length=180)
    # B-02A no dispone aún de un objeto privado versionado. Vacío significa no verificable.
    file_revision_snapshot = models.CharField(max_length=180, blank=True)
    file_sha256_snapshot = models.CharField(max_length=64, blank=True)
    # B-02B: los registros anteriores carecen de una versión privada verificable.
    file_size_bytes_snapshot = models.PositiveBigIntegerField(null=True, blank=True)
    buyer_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_reason = models.CharField(max_length=80, blank=True)
    objects = OrderQuerySet.as_manager()

    class Meta:
        indexes = [models.Index(fields=['state', 'created_at'], name='store_order_state_created_idx')]
        constraints = [
            models.CheckConstraint(condition=Q(amount_minor__gt=0), name='store_order_positive_amount'),
            models.CheckConstraint(condition=Q(currency='MXN'), name='store_order_mxn_only'),
            models.CheckConstraint(condition=Q(environment__in=['test', 'live']), name='store_order_valid_environment'),
            models.CheckConstraint(condition=Q(file_size_bytes_snapshot__isnull=True) | Q(file_size_bytes_snapshot__gt=0), name='store_order_file_size_positive'),
            models.CheckConstraint(condition=Q(state__in=['created', 'awaiting_payment', 'paid', 'closed_unpaid', 'review']), name='store_order_valid_state'),
            models.CheckConstraint(condition=~Q(state='paid') | Q(paid_at__isnull=False), name='store_order_paid_has_date'),
            models.CheckConstraint(condition=~Q(state='closed_unpaid') | Q(closed_at__isnull=False), name='store_order_closed_has_date'),
        ]

    def save(self, *args, **kwargs):
        creating = self._state.adding
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if any(getattr(self, field) != getattr(original, field) for field in self.IMMUTABLE_FIELDS):
                raise ValidationError('La fotografía comercial de la orden no puede modificarse.')
            if any(getattr(self, field) != getattr(original, field) for field in
                   ('state', 'paid_at', 'closed_at', 'closed_reason')):
                raise ValidationError('El estado de la orden requiere el servicio transaccional.')
        elif self.state != self.State.CREATED or self.paid_at or self.closed_at or self.closed_reason:
            raise ValidationError('B-02A solo permite crear órdenes en estado CREATED.')
        self.full_clean(validate_unique=False, validate_constraints=False)
        with transaction.atomic():
            super().save(*args, **kwargs)
            if creating and connection.vendor != 'postgresql':
                OrderAuditEvent.objects.create(
                    order=self, operation_id=uuid.uuid4(), subject=OrderAuditEvent.Subject.ORDER,
                    actor=OrderAuditEvent.Actor.SYSTEM, action='created',
                    to_state=self.State.CREATED, correlation_id=self.creation_key,
                )


class PaymentAttempt(models.Model):
    class State(models.TextChoices):
        PREPARED = 'prepared', 'Preparado'
        SESSION_OPEN = 'session_open', 'Sesión abierta'
        PROCESSING = 'processing', 'Procesando'
        SUCCEEDED = 'succeeded', 'Exitoso'
        FAILED = 'failed', 'Fallido'
        EXPIRED = 'expired', 'Vencido'
        REVIEW = 'review', 'Revisión'

    ACTIVE_STATES = (State.PREPARED, State.SESSION_OPEN, State.PROCESSING)

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='payment_attempts')
    operation_id = models.UUIDField(unique=True, editable=False)
    request_idempotency_key = models.UUIDField(editable=False)
    attempt_number = models.PositiveSmallIntegerField()
    provider = models.CharField(max_length=16, default='stripe')
    provider_account_id = models.CharField(max_length=100)
    environment = models.CharField(max_length=4, choices=DigitalProduct.StripeEnvironment.choices)
    state = models.CharField(max_length=16, choices=State.choices, default=State.PREPARED)
    checkout_session_id = models.CharField(max_length=255, blank=True)
    payment_intent_id = models.CharField(max_length=255, blank=True)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default='MXN')
    result_code = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    bound_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    objects = PaymentAttemptQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=['order', 'created_at'], name='store_att_order_created_idx'),
            models.Index(fields=['environment', 'state', 'created_at'], name='store_attempt_env_state_idx'),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(attempt_number__gt=0), name='store_attempt_positive_number'),
            models.CheckConstraint(condition=Q(amount_minor__gt=0), name='store_attempt_positive_amount'),
            models.CheckConstraint(condition=Q(currency='MXN'), name='store_attempt_mxn_only'),
            models.CheckConstraint(condition=Q(environment__in=['test', 'live']), name='store_attempt_valid_environment'),
            models.CheckConstraint(condition=Q(provider='stripe'), name='store_attempt_stripe_only'),
            models.CheckConstraint(condition=~Q(provider_account_id=''), name='store_attempt_has_account'),
            models.CheckConstraint(condition=Q(state__in=['prepared', 'session_open', 'processing', 'succeeded', 'failed', 'expired', 'review']), name='store_attempt_valid_state'),
            models.UniqueConstraint(fields=['order', 'attempt_number'], name='store_attempt_order_number_unique'),
            models.UniqueConstraint(fields=['provider', 'provider_account_id', 'environment', 'request_idempotency_key'], name='store_attempt_request_unique'),
            models.UniqueConstraint(fields=['provider', 'provider_account_id', 'environment', 'checkout_session_id'], condition=~Q(checkout_session_id=''), name='store_attempt_session_unique'),
            models.UniqueConstraint(fields=['provider', 'provider_account_id', 'environment', 'payment_intent_id'], condition=~Q(payment_intent_id=''), name='store_attempt_intent_unique'),
            models.UniqueConstraint(fields=['order'], condition=Q(state__in=['prepared', 'session_open', 'processing']), name='store_attempt_one_active'),
        ]

    def clean(self):
        super().clean()
        if self.order_id and (
            self.environment != self.order.environment
            or self.amount_minor != self.order.amount_minor
            or self.currency != self.order.currency
        ):
            raise ValidationError('El intento debe coincidir con el entorno, importe y moneda de la orden.')

    def save(self, *args, **kwargs):
        creating = self._state.adding
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if any(getattr(self, field) != getattr(original, field) for field in
                   ('order_id', 'operation_id', 'request_idempotency_key', 'attempt_number',
                    'provider', 'provider_account_id', 'environment', 'amount_minor',
                    'currency', 'state', 'completed_at', 'result_code')):
                raise ValidationError('El intento requiere el servicio transaccional.')
        elif (self.state != self.State.PREPARED or self.completed_at or self.result_code
              or self.checkout_session_id or self.payment_intent_id or self.bound_at):
            raise ValidationError('B-02A solo permite preparar intentos sin referencias externas.')
        if self.order_id and not self.pk and Order.objects.get(pk=self.order_id).state not in (
            Order.State.CREATED, Order.State.AWAITING_PAYMENT
        ):
            raise ValidationError('No se permiten intentos nuevos en una orden cerrada.')
        self.full_clean(validate_unique=False, validate_constraints=False)
        with transaction.atomic():
            super().save(*args, **kwargs)
            if creating and connection.vendor != 'postgresql':
                OrderAuditEvent.objects.create(
                    order=self.order, attempt=self, operation_id=uuid.uuid4(),
                    subject=OrderAuditEvent.Subject.ATTEMPT,
                    actor=OrderAuditEvent.Actor.SYSTEM, action='prepared',
                    to_state=self.State.PREPARED, correlation_id=self.operation_id,
                )


class OrderAuditEvent(models.Model):
    class Actor(models.TextChoices):
        SYSTEM = 'system', 'Sistema'
        ADMIN = 'admin', 'Administrador'

    class Subject(models.TextChoices):
        ORDER = 'order', 'Orden'
        ATTEMPT = 'attempt', 'Intento'

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='audit_events')
    attempt = models.ForeignKey(PaymentAttempt, null=True, blank=True, on_delete=models.PROTECT, related_name='audit_events')
    operation_id = models.UUIDField(unique=True, editable=False)
    subject = models.CharField(max_length=12, choices=Subject.choices)
    actor = models.CharField(max_length=12, choices=Actor.choices)
    actor_ref = models.CharField(max_length=80, blank=True)
    action = models.CharField(max_length=48)
    from_state = models.CharField(max_length=20, blank=True)
    to_state = models.CharField(max_length=20, blank=True)
    reason = models.CharField(max_length=200, blank=True)
    correlation_id = models.UUIDField(null=True, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)
    objects = AuditEventQuerySet.as_manager()

    class Meta:
        indexes = [models.Index(fields=['order', 'occurred_at'], name='store_audit_order_date_idx')]
        constraints = [
            models.CheckConstraint(condition=Q(actor__in=['system', 'admin']), name='store_audit_valid_actor'),
            models.CheckConstraint(condition=Q(subject__in=['order', 'attempt']), name='store_audit_valid_subject'),
            models.CheckConstraint(condition=Q(subject='order') | Q(attempt__isnull=False), name='store_audit_attempt_required'),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Los eventos de auditoría son inmutables.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Los eventos de auditoría no pueden eliminarse.')


class DeliveryEntitlementQuerySet(models.QuerySet):
    """B-02B solo define el derecho; sus cambios operativos llegan en B-03 a B-06."""

    def update(self, **kwargs):
        raise ValidationError('Los derechos todavía no admiten modificaciones operativas.')

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Los derechos todavía no admiten modificaciones operativas.')

    def bulk_create(self, objs, *args, **kwargs):
        raise ValidationError('Los derechos requieren una concesión transaccional auditada.')

    def delete(self):
        raise ValidationError('Los derechos no pueden eliminarse.')


class DeliveryEntitlement(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Activo'
        SUSPENDED = 'suspended', 'Suspendido'
        REVOKED = 'revoked', 'Revocado'

    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name='delivery_entitlement')
    source_attempt = models.OneToOneField(
        PaymentAttempt, on_delete=models.PROTECT, related_name='delivery_entitlement',
    )
    grant_correlation_id = models.UUIDField(unique=True, editable=False)
    environment = models.CharField(max_length=4, choices=DigitalProduct.StripeEnvironment.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    paid_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    file_object_identifier = models.CharField(max_length=180)
    file_version_id = models.CharField(max_length=180)
    file_sha256 = models.CharField(
        max_length=64, validators=[RegexValidator(r'\A[0-9a-f]{64}\Z', 'Indica un SHA-256 hexadecimal en minúsculas.')],
    )
    file_size_bytes = models.PositiveBigIntegerField()
    download_limit = models.PositiveSmallIntegerField(default=3)
    successful_downloads = models.PositiveSmallIntegerField(default=0)
    suspended_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    status_reason_code = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = DeliveryEntitlementQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=['environment', 'status', 'expires_at'], name='store_ent_env_status_exp_idx'),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(environment__in=['test', 'live']), name='store_ent_valid_environment'),
            models.CheckConstraint(condition=Q(status__in=['active', 'suspended', 'revoked']), name='store_ent_valid_status'),
            models.CheckConstraint(condition=Q(download_limit=3), name='store_ent_three_downloads'),
            models.CheckConstraint(condition=Q(successful_downloads__gte=0, successful_downloads__lte=3), name='store_ent_download_range'),
            models.CheckConstraint(condition=Q(file_size_bytes__gt=0), name='store_ent_positive_file_size'),
            models.CheckConstraint(condition=~Q(file_object_identifier=''), name='store_ent_has_object'),
            models.CheckConstraint(condition=~Q(file_version_id=''), name='store_ent_has_version'),
            models.CheckConstraint(condition=Q(file_sha256__regex=r'^[0-9a-f]{64}$'), name='store_ent_valid_sha256'),
            models.CheckConstraint(condition=Q(expires_at__gt=models.F('paid_at')), name='store_ent_positive_term'),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.order_id and self.source_attempt_id:
            order = self.order
            attempt = self.source_attempt
            if order.state != Order.State.PAID or order.paid_at is None:
                errors['order'] = 'El derecho requiere una orden pagada y verificada.'
            if attempt.order_id != order.pk or attempt.state != PaymentAttempt.State.SUCCEEDED:
                errors['source_attempt'] = 'El intento confirmado debe pertenecer a la orden.'
            if self.environment != order.environment or self.environment != attempt.environment:
                errors['environment'] = 'El entorno debe coincidir con orden e intento.'
            if self.paid_at != order.paid_at:
                errors['paid_at'] = 'La vigencia comienza en el pago efectivo de la orden.'
            if self.file_object_identifier != order.file_key_snapshot or not order.file_revision_snapshot:
                errors['file_object_identifier'] = 'La orden requiere un objeto privado versionado.'
            if self.file_version_id != order.file_revision_snapshot:
                errors['file_version_id'] = 'La versión debe coincidir con la orden.'
            if self.file_sha256 != order.file_sha256_snapshot:
                errors['file_sha256'] = 'El digest debe coincidir con la orden.'
            if self.file_size_bytes != order.file_size_bytes_snapshot:
                errors['file_size_bytes'] = 'El tamaño debe coincidir con la orden.'
        if self.paid_at and self.expires_at != self.paid_at + timedelta(hours=336):
            errors['expires_at'] = 'El vencimiento debe ser exactamente 336 horas después del pago.'
        if self._state.adding and (self.status != self.Status.ACTIVE or self.successful_downloads != 0
                                   or self.suspended_at or self.revoked_at or self.status_reason_code):
            errors['status'] = 'B-02B solo define el estado inicial sin operaciones administrativas.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Los derechos todavía no admiten modificaciones operativas.')
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Los derechos no pueden eliminarse.')
