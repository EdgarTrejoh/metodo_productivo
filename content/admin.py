from django.contrib import admin
from django import forms
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Article, MediaAsset, PublicationStatus, Video


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'
        widgets = {'body': forms.Textarea(attrs={'rows': 18})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].widget.attrs['data-media-library-url'] = reverse('otpadmin:content_article_media_library')
        self.fields['body'].widget.attrs['data-media-add-url'] = reverse('otpadmin:content_mediaasset_add')


class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('preview', 'name', 'alt_text', 'created_at')
    search_fields = ('name', 'alt_text', 'description')
    readonly_fields = ('preview', 'thumbnail', 'created_at')
    fields = ('name', 'alt_text', 'description', 'image', 'preview', 'created_at')

    @admin.display(description='Miniatura')
    def preview(self, obj):
        if not obj.pk or not obj.thumbnail:
            return '—'
        return format_html('<img src="{}" alt="" width="120" height="80" style="object-fit:contain">', obj.thumbnail_url)


class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    change_form_template = 'admin/content/article/change_form.html'
    list_display = ('title', 'category', 'status', 'published_at', 'updated_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'summary', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('featured_video', 'featured_image')
    actions = ('publish_selected', 'retire_selected')

    class Media:
        css = {'all': ('vendor/quill/quill.snow.css', 'vendor/quill-table-better/quill-table-better.css', 'content/editor.css')}
        js = ('vendor/quill/quill.js', 'vendor/quill-table-better/quill-table-better.js', 'content/editor.js')

    def get_urls(self):
        custom = [
            path('media-library/', self.admin_site.admin_view(self.media_library), name='content_article_media_library'),
            path('<path:object_id>/preview/', self.admin_site.admin_view(self.preview), name='content_article_preview'),
        ]
        return custom + super().get_urls()

    def media_library(self, request):
        if not request.user.has_perm('content.view_mediaasset'):
            raise Http404
        assets = MediaAsset.objects.all()[:100]
        return JsonResponse({'images': [
            {'url': asset.public_url, 'thumbnail': asset.thumbnail_url, 'name': asset.name, 'alt': asset.alt_text}
            for asset in assets
        ]})

    def preview(self, request, object_id):
        article = get_object_or_404(Article.objects.select_related('featured_image', 'featured_video'), pk=object_id)
        if not self.has_view_or_change_permission(request, article):
            raise Http404
        video = article.featured_video
        if video and video.status != PublicationStatus.PUBLISHED:
            video = None
        return render(request, 'article_detail.html', {
            'article': article, 'video': video, 'preview': True,
        })

    @admin.action(description='Publicar artículos seleccionados', permissions=['change'])
    def publish_selected(self, request, queryset):
        for article in queryset:
            article.status = PublicationStatus.PUBLISHED
            article.save()

    @admin.action(description='Retirar artículos seleccionados', permissions=['change'])
    def retire_selected(self, request, queryset):
        for article in queryset:
            article.status = PublicationStatus.RETIRED
            article.save()


class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'status', 'published_at', 'updated_at')
    list_filter = ('status', 'provider')
    search_fields = ('title', 'description', 'source')
    readonly_fields = ('video_id', 'created_at', 'updated_at')
    actions = ('publish_selected', 'retire_selected')

    @admin.action(description='Publicar videos seleccionados', permissions=['change'])
    def publish_selected(self, request, queryset):
        for video in queryset:
            video.status = PublicationStatus.PUBLISHED
            video.save()

    @admin.action(description='Retirar videos seleccionados', permissions=['change'])
    def retire_selected(self, request, queryset):
        for video in queryset:
            video.status = PublicationStatus.RETIRED
            video.save()
