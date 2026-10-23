from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice
from PIL import Image

from .models import Article, ArticleImageUsage, MediaAsset, PublicationStatus, Video, youtube_id
from .editorial import sanitize_article_html


VIDEO_ID = 'AbCdEf12345'


class EditorialTableTests(TestCase):
    def test_editor_nonbreaking_spaces_are_normalized(self):
        cleaned, _ = sanitize_article_html('<p>Las&nbsp;decisiones&#160;financieras\u00a0importan.</p>')
        self.assertEqual(cleaned, '<p>Las decisiones financieras importan.</p>')

    def test_legacy_editor_spaces_render_normally_without_rewriting_stored_body(self):
        article = Article.objects.create(
            title='Artículo de prueba', slug='espacios-de-prueba', summary='Resumen de prueba',
            body='<p>Texto de prueba.</p>', category=Article.Category.DATA,
            cta_target=Article.Cta.TOOLS, status=PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        Article.objects.filter(pk=article.pk).update(body='<p>Las&nbsp;decisiones&nbsp;importan.</p>')
        response = self.client.get(reverse('article_detail', args=[article.slug]))
        self.assertContains(response, '<p>Las decisiones importan.</p>', html=True)
        self.assertIn('&nbsp;', Article.objects.get(pk=article.pk).body)

    def test_table_structure_alignment_and_safe_attributes_survive(self):
        source = (
            '<table class="ql-table-better" style="background:url(javascript:bad)">'
            '<thead><tr><th data-row="row-abc1" scope="col"><p class="ql-table-block" data-cell="cell-abc1">Mes</p></th>'
            '<th scope="col">Pedidos</th></tr></thead>'
            '<tbody><tr><td data-row="row-abc2"><p>Enero</p></td>'
            '<td><p class="ql-table-block ql-align-right" data-cell="cell-abc2">80</p></td></tr></tbody>'
            '</table><script>alert(1)</script><p onclick="alert(2)">Texto legible.</p>'
        )
        cleaned, _ = sanitize_article_html(source)
        for fragment in ('<table', '<thead>', '<tbody>', '<th', 'Mes', 'Pedidos', 'Enero', '80', 'ql-align-right', 'Texto legible.'):
            self.assertIn(fragment, cleaned)
        for fragment in ('javascript:', 'onclick', '<script', 'alert(', 'style='):
            self.assertNotIn(fragment, cleaned)

    def test_invalid_table_metadata_is_removed(self):
        cleaned, _ = sanitize_article_html(
            '<table class="unsafe"><tr><td data-row="row-!" colspan="999" style="color:red">'
            '<p class="ql-table-block unsafe" data-cell="bad">Dato</p></td></tr></table>'
        )
        self.assertIn('<table>', cleaned)
        self.assertIn('Dato', cleaned)
        for fragment in ('class="unsafe"', 'row-!', 'colspan', 'style=', 'data-cell="bad"'):
            self.assertNotIn(fragment, cleaned)


class EditorialTests(TestCase):
    def article(self, **overrides):
        values = {
            'title': 'Artículo sintético de prueba',
            'slug': 'articulo-sintetico',
            'summary': 'Resumen sintético sin datos reales.',
            'body': 'Primer párrafo de prueba.\n\nSegundo párrafo.',
            'category': Article.Category.FINANCE,
            'cta_target': Article.Cta.CALCULATOR,
        }
        values.update(overrides)
        return Article.objects.create(**values)

    def video(self, **overrides):
        values = {
            'title': 'Video sintético de prueba',
            'description': 'Descripción sintética.',
            'source': VIDEO_ID,
        }
        values.update(overrides)
        return Video.objects.create(**values)

    def test_empty_index_has_four_lines_and_no_fake_content(self):
        response = self.client.get(reverse('blog'))
        self.assertEqual(response.status_code, 200)
        for label in ('Finanzas', 'Negocios', 'Datos', 'Tecnología'):
            self.assertContains(response, label)
        self.assertContains(response, 'Todavía no hay artículos publicados')
        self.assertContains(response, 'Todavía no hay videos publicados')
        self.assertNotContains(response, 'aria-label="Filtrar artículos por categoría"')
        self.assertNotContains(response, 'Contenido editorial revisado y publicado.')
        self.assertNotContains(response, '<iframe')

    def test_draft_edit_publish_future_and_retire_article(self):
        article = self.article()
        url = reverse('article_detail', args=[article.slug])
        self.assertNotContains(self.client.get(reverse('blog')), article.title)
        self.assertEqual(self.client.get(url).status_code, 404)
        article.summary = 'Resumen revisado en borrador.'
        article.save()
        self.assertEqual(Article.objects.get(pk=article.pk).summary, article.summary)
        article.status = PublicationStatus.PUBLISHED
        article.published_at = timezone.now() + timedelta(days=1)
        article.save()
        self.assertEqual(self.client.get(url).status_code, 404)
        article.published_at = timezone.now() - timedelta(minutes=1)
        article.save()
        self.assertContains(self.client.get(reverse('blog')), article.title)
        self.assertContains(self.client.get(url), article.summary)
        article.status = PublicationStatus.RETIRED
        article.save()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_slug_category_seo_cta_and_escaped_content(self):
        article = self.article(
            status=PublicationStatus.PUBLISHED,
            seo_title='Título SEO sintético',
            seo_description='Descripción SEO sintética',
            body='<script>alert(1)</script>\nTexto visible.',
        )
        url = reverse('article_detail', args=[article.slug])
        response = self.client.get(url)
        self.assertContains(response, '<link rel="canonical" href="http://testserver/blog/articulo-sintetico/">')
        self.assertContains(response, '<meta property="og:type" content="article">')
        self.assertContains(response, 'Título SEO sintético')
        self.assertContains(response, 'Descripción SEO sintética')
        self.assertContains(response, reverse('break_even'))
        self.assertNotContains(response, 'alert(1)')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, 'aria-current="location">Contenidos</a>')
        self.assertEqual(len(Article.Category.choices), 4)
        with self.assertRaises(ValidationError):
            self.article(slug='articulo-sintetico')
        with self.assertRaises(ValidationError):
            self.article(slug='otro', category='otra')
        self.assertEqual(self.client.get(reverse('blog') + '?categoria=otra').status_code, 404)
        self.assertContains(self.client.get(reverse('blog') + '?categoria=finance'), article.title)
        self.assertNotContains(self.client.get(reverse('blog') + '?categoria=business'), article.title)

    def test_only_live_videos_and_validated_embed(self):
        video = self.video(status=PublicationStatus.PUBLISHED)
        draft = self.video(title='Borrador oculto', source='ZyXwVu98765')
        response = self.client.get(reverse('blog'))
        self.assertContains(response, video.title)
        self.assertNotContains(response, draft.title)
        self.assertNotContains(response, '<iframe')
        self.assertContains(response, f'data-video-id="{VIDEO_ID}"')
        self.assertContains(response, '/static/video_embed.js')
        self.assertContains(response, f'https://www.youtube.com/watch?v={VIDEO_ID}')
        article = self.article(status=PublicationStatus.PUBLISHED, featured_video=video)
        detail = self.client.get(reverse('article_detail', args=[article.slug]))
        self.assertContains(detail, video.title)
        video.status = PublicationStatus.RETIRED
        video.save()
        self.assertNotContains(self.client.get(reverse('blog')), video.title)
        self.assertNotContains(self.client.get(reverse('article_detail', args=[article.slug])), video.title)

    def test_youtube_source_validation(self):
        self.assertEqual(youtube_id(VIDEO_ID), VIDEO_ID)
        self.assertEqual(youtube_id(f'https://youtu.be/{VIDEO_ID}'), VIDEO_ID)
        self.assertEqual(youtube_id(f'https://www.youtube.com/watch?v={VIDEO_ID}'), VIDEO_ID)
        for source in (
            'https://youtube.com.ejemplo.invalid/watch?v=' + VIDEO_ID,
            'http://youtube.com/watch?v=' + VIDEO_ID,
            'https://www.youtube.com/watch?v=incorrecto',
            'https://youtu.be/' + VIDEO_ID + '/extra',
            '<iframe src="https://youtube.com"></iframe>',
        ):
            with self.subTest(source=source), self.assertRaises(ValidationError):
                self.video(source=source)
        with self.assertRaises(ValidationError):
            self.video(provider='otro')

    def test_video_scheduling_and_invalid_article_reference(self):
        video = self.video(status=PublicationStatus.PUBLISHED, published_at=timezone.now() + timedelta(days=1))
        article = self.article(status=PublicationStatus.PUBLISHED, featured_video=video)
        self.assertNotContains(self.client.get(reverse('blog')), video.title)
        self.assertNotContains(self.client.get(reverse('article_detail', args=[article.slug])), video.title)
        video.published_at = timezone.now() - timedelta(days=1)
        video.save()
        self.assertContains(self.client.get(reverse('blog')), video.title)

    def test_backoffice_requires_staff_and_otp_then_allows_editorial_work(self):
        user = get_user_model().objects.create_user('editorial', password='only-for-test', is_staff=True, is_superuser=True)
        add_url = reverse('otpadmin:content_article_add')
        self.assertEqual(self.client.get(add_url).status_code, 302)
        self.client.force_login(user)
        self.assertEqual(self.client.get(add_url).status_code, 302)
        device = TOTPDevice.objects.create(user=user, name='test', confirmed=True)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        self.assertEqual(self.client.get(add_url).status_code, 200)
        self.assertEqual(self.client.get(reverse('otpadmin:content_video_add')).status_code, 200)
        response = self.client.post(add_url, {
            'title': 'Borrador de administración', 'slug': 'borrador-admin',
            'summary': 'Resumen sintético', 'body': 'Texto sintético',
            'category': Article.Category.DATA, 'cta_target': Article.Cta.TOOLS,
            'status': PublicationStatus.DRAFT, 'seo_title': '', 'seo_description': '',
            'featured_video': '', 'published_at_0': '', 'published_at_1': '',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        article = Article.objects.get(slug='borrador-admin')
        self.assertEqual(article.status, PublicationStatus.DRAFT)
        change_url = reverse('otpadmin:content_article_change', args=[article.pk])
        response = self.client.post(change_url, {
            'title': article.title, 'slug': article.slug,
            'summary': 'Resumen modificado', 'body': article.body,
            'category': article.category, 'cta_target': article.cta_target,
            'status': PublicationStatus.PUBLISHED, 'seo_title': '', 'seo_description': '',
            'featured_video': '', 'published_at_0': '', 'published_at_1': '',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        article.refresh_from_db()
        self.assertEqual(article.summary, 'Resumen modificado')
        self.assertEqual(article.status, PublicationStatus.PUBLISHED)
        self.assertContains(self.client.get(reverse('blog')), article.title)

    def test_admin_actions_publish_and_retire_video(self):
        user = get_user_model().objects.create_user('video-editor', password='only-for-test', is_staff=True, is_superuser=True)
        self.client.force_login(user)
        device = TOTPDevice.objects.create(user=user, name='test', confirmed=True)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        add_url = reverse('otpadmin:content_video_add')
        response = self.client.post(add_url, {
            'title': 'Video de administración', 'description': 'Video sintético',
            'provider': Video.Provider.YOUTUBE, 'source': VIDEO_ID,
            'status': PublicationStatus.DRAFT, 'published_at_0': '', 'published_at_1': '',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        video = Video.objects.get(title='Video de administración')
        change_list = reverse('otpadmin:content_video_changelist')
        for action, status in (('publish_selected', PublicationStatus.PUBLISHED), ('retire_selected', PublicationStatus.RETIRED)):
            response = self.client.post(change_list, {
                'action': action, '_selected_action': str(video.pk), 'index': '0',
            })
            self.assertEqual(response.status_code, 302)
            video.refresh_from_db()
            self.assertEqual(video.status, status)
        self.assertNotContains(self.client.get(reverse('blog')), video.title)

    def test_staff_without_editorial_permission_cannot_manage_content(self):
        user = get_user_model().objects.create_user('staff-no-content', password='only-for-test', is_staff=True)
        self.client.force_login(user)
        device = TOTPDevice.objects.create(user=user, name='test', confirmed=True)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        self.assertIn(self.client.get(reverse('otpadmin:content_article_add')).status_code, (302, 403))
        self.assertIn(self.client.get(reverse('otpadmin:content_video_add')).status_code, (302, 403))


class MediaEditorialTests(TestCase):
    @staticmethod
    def close_stream_file(response):
        # Response.close() emits request_finished, which closes TestCase's PostgreSQL transaction.
        while response._resource_closers:
            response._resource_closers.pop()()

    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        media_setting = override_settings(MEDIA_ROOT=self.folder.name)
        media_setting.enable()
        self.addCleanup(media_setting.disable)

    def upload(self, filename='imagen.png', content=None):
        if content is None:
            buffer = BytesIO()
            Image.new('RGB', (100, 60), '#16786e').save(buffer, format='PNG')
            content = buffer.getvalue()
        return SimpleUploadedFile(filename, content, content_type='image/png')

    def media(self, **overrides):
        values = {'name': 'Imagen sintética', 'alt_text': 'Gráfica sintética', 'description': 'Solo prueba', 'image': self.upload()}
        values.update(overrides)
        return MediaAsset.objects.create(**values)

    def article(self, **overrides):
        values = {
            'title': 'Artículo con imagen de prueba', 'slug': 'articulo-con-imagen',
            'summary': 'Resumen sintético', 'body': '<h2>Subtítulo</h2><p>Texto <strong>útil</strong>.</p>',
            'category': Article.Category.DATA, 'cta_target': Article.Cta.TOOLS,
        }
        values.update(overrides)
        return Article.objects.create(**values)

    def verified_admin(self):
        user = get_user_model().objects.create_user('editor-media', password='only-for-test', is_staff=True, is_superuser=True)
        self.client.force_login(user)
        device = TOTPDevice.objects.create(user=user, name='test', confirmed=True)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        return user

    def test_image_file_validation_and_thumbnail(self):
        asset = self.media()
        self.assertTrue(asset.image.name.endswith('.png'))
        self.assertTrue(asset.thumbnail.name.endswith('.webp'))
        with asset.thumbnail.open('rb') as file:
            self.assertEqual(Image.open(file).format, 'WEBP')
        for upload in (
            self.upload('imagen.svg'),
            self.upload('imagen.jpg'),
            self.upload('imagen.png', b'not an image'),
            self.upload('imagen.png', b'x' * (5 * 1024 * 1024 + 1)),
        ):
            with self.subTest(name=upload.name), self.assertRaises(ValidationError):
                self.media(image=upload)
        for image_format, extension in (('JPEG', 'jpg'), ('WEBP', 'webp')):
            buffer = BytesIO()
            Image.new('RGB', (100, 60), '#16786e').save(buffer, format=image_format)
            with self.subTest(image_format=image_format):
                supported = self.media(image=self.upload(f'imagen.{extension}', buffer.getvalue()))
                with supported.image.open('rb') as file:
                    self.assertEqual(Image.open(file).format, image_format)

    def test_sanitizer_authorized_images_and_protected_reuse(self):
        image = self.media()
        article = self.article(body=f'<h2>Título</h2><p><img src="{image.public_url}" alt="Gráfica sintética" onerror="alert(1)"></p><script>alert(2)</script><a href="javascript:alert(3)">malo</a>')
        self.assertEqual(ArticleImageUsage.objects.filter(article=article, image=image).count(), 1)
        self.assertNotIn('onerror', article.body)
        self.assertNotIn('alert(', article.body)
        self.assertEqual(self.client.get(image.public_url).status_code, 404)
        with self.assertRaises(ProtectedError):
            image.delete()
        second = self.article(slug='articulo-reutiliza-imagen', featured_image=image)
        article.status = PublicationStatus.PUBLISHED
        article.save()
        image_response = self.client.get(image.public_url)
        try:
            self.assertEqual(image_response.status_code, 200)
        finally:
            self.close_stream_file(image_response)
        self.assertContains(self.client.get(reverse('article_detail', args=[article.slug])), 'Gráfica sintética')
        article.body = '<p>Imagen retirada del cuerpo.</p>'
        article.save()
        self.assertFalse(ArticleImageUsage.objects.filter(article=article).exists())
        with self.assertRaises(ProtectedError):
            image.delete()
        second.delete()
        image.delete()
        self.assertFalse(MediaAsset.objects.filter(pk=image.pk).exists())
        with self.assertRaises(ValidationError):
            self.article(slug='externa', body='<p><img src="https://example.com/a.png" alt="externa"></p>')
        with self.assertRaises(ValidationError):
            self.article(slug='sin-alt', body=f'<p><img src="{self.media().public_url}"></p>')
        with self.assertRaises(ValidationError):
            self.article(slug='desconocida', body='<p><img src="/editorial/media/00000000-0000-0000-0000-000000000000/" alt="x"></p>')

    def test_admin_create_draft_preview_publish_edit_retire(self):
        user = self.verified_admin()
        media_add = reverse('otpadmin:content_mediaasset_add')
        self.assertEqual(self.client.get(media_add).status_code, 200)
        response = self.client.post(media_add, {
            'name': 'Imagen de administración', 'alt_text': 'Imagen de prueba',
            'description': 'Sintética', 'image': self.upload(), '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        image = MediaAsset.objects.get(name='Imagen de administración')
        library = reverse('otpadmin:content_article_media_library')
        self.assertEqual(self.client.get(library).json()['images'][0]['url'], image.public_url)
        add = reverse('otpadmin:content_article_add')
        self.assertContains(self.client.get(add), 'vendor/quill/quill.js')
        data = {
            'title': 'Borrador visual', 'slug': 'borrador-visual', 'summary': 'Resumen sintético',
            'body': f'<h2>Sección</h2><p><img src="{image.public_url}" alt="Imagen de prueba"></p>',
            'category': Article.Category.FINANCE, 'cta_target': Article.Cta.TOOLS,
            'featured_image': str(image.pk), 'featured_video': '',
            'seo_title': '', 'seo_description': '', 'status': PublicationStatus.DRAFT,
            'published_at_0': '', 'published_at_1': '', '_save': 'Guardar',
        }
        self.assertEqual(self.client.post(add, data).status_code, 302)
        article = Article.objects.get(slug='borrador-visual')
        public = reverse('article_detail', args=[article.slug])
        preview = reverse('otpadmin:content_article_preview', args=[article.pk])
        self.assertEqual(self.client.get(public).status_code, 404)
        self.assertContains(self.client.get(preview), 'Vista previa editorial')
        self.assertContains(self.client.get(preview), 'noindex,nofollow')
        image_response = self.client.get(image.public_url)
        try:
            self.assertEqual(image_response.status_code, 200)
        finally:
            self.close_stream_file(image_response)
        change = reverse('otpadmin:content_article_change', args=[article.pk])
        data['status'] = PublicationStatus.PUBLISHED
        self.assertEqual(self.client.post(change, data).status_code, 302)
        self.assertContains(self.client.get(public), 'Imagen de prueba')
        data['summary'] = 'Resumen revisado'
        self.assertEqual(self.client.post(change, data).status_code, 302)
        self.assertContains(self.client.get(public), 'Resumen revisado')
        data['status'] = PublicationStatus.RETIRED
        self.assertEqual(self.client.post(change, data).status_code, 302)
        self.assertEqual(self.client.get(public).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(preview).status_code, 302)
        self.assertEqual(self.client.get(image.public_url).status_code, 404)
        self.assertTrue(user.has_perm('content.change_article'))

    def test_media_permissions_and_unsafe_urls(self):
        image = self.media()
        library = reverse('otpadmin:content_article_media_library')
        self.assertEqual(self.client.get(library).status_code, 302)
        user = get_user_model().objects.create_user('staff-media', password='only-for-test', is_staff=True)
        self.client.force_login(user)
        device = TOTPDevice.objects.create(user=user, name='test', confirmed=True)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        self.assertEqual(self.client.get(library).status_code, 404)
        self.assertIn(self.client.get(reverse('otpadmin:content_mediaasset_add')).status_code, (302, 403))
        self.assertEqual(self.client.get(image.public_url).status_code, 404)
        article = self.article(body='<p><a href="javascript:alert(1)" onclick="alert(2)">inseguro</a><a href="http://example.com">sin cifrar</a><a href="https://example.com">seguro</a></p>')
        self.assertNotIn('javascript:', article.body)
        self.assertNotIn('http://', article.body)
        self.assertNotIn('onclick', article.body)
        self.assertIn('https://example.com', article.body)
