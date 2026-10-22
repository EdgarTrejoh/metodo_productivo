from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import ProtectedError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice
from PIL import Image

from content.models import Article, MediaAsset, PublicationStatus
from .models import DigitalProduct


TEST_LINK = 'https://buy.stripe.com/test_AbC123456789'


class StoreTests(TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        media_setting = override_settings(MEDIA_ROOT=folder.name)
        media_setting.enable()
        self.addCleanup(media_setting.disable)

    def image(self):
        buffer = BytesIO()
        Image.new('RGB', (100, 60), '#16786e').save(buffer, format='PNG')
        return MediaAsset.objects.create(
            name='Imagen sintética', alt_text='Imagen de prueba',
            image=SimpleUploadedFile('prueba.png', buffer.getvalue(), content_type='image/png'),
        )

    def data(self, slug='producto-de-prueba', **overrides):
        values = {
            'name': 'Producto sintético', 'slug': slug, 'summary': 'Resumen sintético',
            'description': 'Descripción de prueba.', 'benefits': 'Beneficio de prueba.',
            'version': '0.1', 'software_requirements': 'Software de prueba.',
            'contents': 'Archivo de prueba.', 'delivery_terms': 'Entrega de prueba.',
            'price': '499.00', 'currency': 'MXN', 'private_file_key': 'archivo-de-prueba',
            'status': PublicationStatus.DRAFT,
        }
        values.update(overrides)
        return values

    def verified_admin(self):
        user = get_user_model().objects.create_user('admin-tienda-prueba', password='only-for-test', is_staff=True, is_superuser=True)
        self.client.force_login(user)
        device = TOTPDevice.objects.create(user=user, name='test', confirmed=True)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        return user

    def test_empty_and_draft_are_not_public(self):
        self.assertContains(self.client.get(reverse('store')), 'Todavía no hay productos digitales publicados')
        product = DigitalProduct.objects.create(name='Borrador', slug='borrador')
        self.assertNotContains(self.client.get(reverse('store')), 'Borrador')
        self.assertEqual(self.client.get(reverse('store_detail', args=[product.slug])).status_code, 404)
        self.assertEqual(self.client.get(reverse('otpadmin:store_digitalproduct_preview', args=[product.pk])).status_code, 302)

    def test_publishing_requires_complete_data_and_rejects_bad_references(self):
        with self.assertRaises(ValidationError):
            DigitalProduct.objects.create(name='Incompleto', slug='incompleto', status=PublicationStatus.PUBLISHED)
        with self.assertRaises(ValidationError):
            DigitalProduct.objects.create(**self.data(stripe_product_id='prod_test', stripe_price_id='price_test'))
        product = DigitalProduct.objects.create(**self.data())
        product.private_file_key = ''
        product.status = PublicationStatus.PUBLISHED
        with self.assertRaises(ValidationError):
            product.save()

    def test_admin_creates_second_product_without_route_or_template_change(self):
        self.verified_admin()
        add = reverse('otpadmin:store_digitalproduct_add')
        image = self.image()
        first = self.data(image=image.pk)
        second = self.data('segundo-producto', name='Segundo producto sintético', image=image.pk)
        for values in (first, second):
            response = self.client.post(add, values)
            self.assertEqual(response.status_code, 302, response.context)
        self.assertEqual(DigitalProduct.objects.count(), 2)
        second_product = DigitalProduct.objects.get(slug='segundo-producto')
        preview = reverse('otpadmin:store_digitalproduct_preview', args=[second_product.pk])
        self.assertContains(self.client.get(preview), 'Segundo producto sintético')
        self.assertContains(self.client.get(preview), 'noindex,nofollow')
        self.assertEqual(self.client.get(reverse('store_detail', args=[second_product.slug])).status_code, 404)
        self.assertEqual(Client().get(image.public_url).status_code, 404)
        with self.assertRaises(ProtectedError):
            image.delete()
        change = reverse('otpadmin:store_digitalproduct_change', args=[second_product.pk])
        second['status'] = PublicationStatus.PUBLISHED
        self.assertEqual(self.client.post(change, second).status_code, 302)
        self.assertContains(self.client.get(reverse('store')), 'Segundo producto sintético')
        self.assertContains(self.client.get(reverse('store_detail', args=[second_product.slug])), '499.00 MXN')
        image_response = self.client.get(image.public_url)
        try:
            self.assertEqual(image_response.status_code, 200)
        finally:
            image_response.close()
        second['summary'] = 'Resumen editado desde Admin'
        self.assertEqual(self.client.post(change, second).status_code, 302)
        self.assertContains(self.client.get(reverse('store_detail', args=[second_product.slug])), second['summary'])
        second['status'] = PublicationStatus.RETIRED
        self.assertEqual(self.client.post(change, second).status_code, 302)
        self.assertEqual(self.client.get(reverse('store_detail', args=[second_product.slug])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('store')), 'Segundo producto sintético')
        self.assertEqual(Client().get(image.public_url).status_code, 404)
        self.assertTrue(DigitalProduct.objects.filter(pk=second_product.pk, status=PublicationStatus.RETIRED).exists())

    def test_preview_requires_otp_and_model_permission(self):
        product = DigitalProduct.objects.create(**self.data())
        preview = reverse('otpadmin:store_digitalproduct_preview', args=[product.pk])
        user = get_user_model().objects.create_user('sin-otp', password='only-for-test', is_staff=True, is_superuser=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(preview).status_code, 302)
        device = TOTPDevice.objects.create(user=user, name='test', confirmed=True)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        self.assertEqual(self.client.get(preview).status_code, 200)
        self.client.logout()
        restricted = get_user_model().objects.create_user('sin-permiso', password='only-for-test', is_staff=True)
        self.client.force_login(restricted)
        device = TOTPDevice.objects.create(user=restricted, name='test', confirmed=True)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        self.assertEqual(self.client.get(preview).status_code, 404)

    def test_future_publication_and_blog_image_behavior(self):
        image = self.image()
        product = DigitalProduct.objects.create(**self.data(image=image, status=PublicationStatus.PUBLISHED, published_at=timezone.now()))
        response = self.client.get(image.public_url)
        try:
            self.assertEqual(response.status_code, 200)
        finally:
            response.close()
        product.published_at = timezone.now() + timedelta(days=1)
        product.save()
        self.assertEqual(self.client.get(image.public_url).status_code, 404)
        self.assertEqual(self.client.get(reverse('store_detail', args=[product.slug])).status_code, 404)
        Article.objects.create(
            title='Artículo sintético', slug='articulo-sintetico', summary='Resumen', body='<p>Contenido</p>',
            category=Article.Category.DATA, cta_target=Article.Cta.TOOLS,
            featured_image=image, status=PublicationStatus.PUBLISHED, published_at=timezone.now(),
        )
        response = self.client.get(image.public_url)
        try:
            self.assertEqual(response.status_code, 200)
        finally:
            response.close()

    def test_test_payment_link_is_validated_and_labeled_in_admin(self):
        for url in (
            'http://buy.stripe.com/test_AbC123',
            'https://evil.buy.stripe.com/test_AbC123',
            'https://buy.stripe.com/live_AbC123',
            'https://buy.stripe.com/test_AbC123?next=example',
            'https://buy.stripe.com/test_AbC123/',
        ):
            with self.subTest(url=url), self.assertRaises(ValidationError):
                DigitalProduct.objects.create(**self.data(
                    stripe_environment='test', stripe_test_payment_url=url,
                ))
        with self.assertRaises(ValidationError):
            DigitalProduct.objects.create(**self.data(
                stripe_environment='live', stripe_test_payment_url=TEST_LINK,
            ))
        self.verified_admin()
        response = self.client.get(reverse('otpadmin:store_digitalproduct_add'))
        self.assertContains(response, 'Enlace de pago Stripe TEST')
        self.assertContains(response, 'Solo para el piloto local')

    def test_test_checkout_requires_all_conditions_and_does_not_attach_to_demo(self):
        demo = DigitalProduct.objects.create(**self.data(
            slug='demo-299', name='DEMO sintético', price='299.00',
            status=PublicationStatus.PUBLISHED,
        ))
        product = DigitalProduct.objects.create(**self.data(
            slug='producto-test-499', status=PublicationStatus.PUBLISHED,
            stripe_environment='test', stripe_test_payment_url=TEST_LINK,
        ))
        product_url = reverse('store_detail', args=[product.slug])
        demo_url = reverse('store_detail', args=[demo.slug])
        with override_settings(DEBUG=True, STORE_TEST_CHECKOUT_ENABLED=True):
            response = self.client.get(product_url)
            self.assertContains(response, f'href="{TEST_LINK}"')
            self.assertContains(response, 'Probar compra en Stripe')
            self.assertContains(response, 'Pago de prueba. No se realizan cargos reales ni se entregan archivos.')
            self.assertNotContains(self.client.get(demo_url), 'Probar compra en Stripe')
            product.status = PublicationStatus.DRAFT
            product.save()
            self.assertEqual(self.client.get(product_url).status_code, 404)
            product.status = PublicationStatus.PUBLISHED
            product.save()
            with override_settings(DEBUG=False):
                self.assertNotContains(self.client.get(product_url), 'Probar compra en Stripe')
            DigitalProduct.objects.filter(pk=product.pk).update(stripe_test_payment_url='https://example.com/test_invalid')
            self.assertNotContains(self.client.get(product_url), 'Probar compra en Stripe')
        with override_settings(STORE_TEST_CHECKOUT_ENABLED=False):
            self.assertNotContains(self.client.get(product_url), 'Probar compra en Stripe')
