from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from .models import Article, MediaAsset, PublicationStatus, Video
from store.models import DigitalProduct


def index(request):
    category = request.GET.get('categoria', '')
    valid_categories = {choice.value for choice in Article.Category}
    if category and category not in valid_categories:
        raise Http404('Categoría no encontrada.')
    has_live_articles = Article.live().exists()
    articles = Article.live().select_related('featured_image')
    if category:
        articles = articles.filter(category=category)
    page = Paginator(articles, 9).get_page(request.GET.get('pagina'))
    return render(request, 'blog.html', {
        'articles': page,
        'has_live_articles': has_live_articles,
        'videos': Video.live()[:3],
        'categories': Article.Category.choices,
        'selected_category': category,
    })


def detail(request, slug):
    article = get_object_or_404(Article.live().select_related('featured_video', 'featured_image'), slug=slug)
    video = article.featured_video
    if video and (video.status != PublicationStatus.PUBLISHED or video.published_at is None or video.published_at > timezone.now()):
        video = None
    return render(request, 'article_detail.html', {
        'article': article,
        'video': video,
        'canonical_url': request.build_absolute_uri(reverse('article_detail', args=[article.slug])),
    })


def editorial_image(request, image_id):
    image = get_object_or_404(MediaAsset, pk=image_id)
    authorized_editor = (
        request.user.is_authenticated and request.user.is_staff
        and getattr(request.user, 'is_verified', lambda: False)()
        and request.user.has_perm('content.view_mediaasset')
    )
    publicly_used = Article.live().filter(
        Q(featured_image=image) | Q(inline_image_usages__image=image)
    ).exists() or DigitalProduct.live().filter(image=image).exists()
    if not authorized_editor and not publicly_used:
        raise Http404('Imagen no disponible.')
    thumbnail = request.GET.get('thumb') == '1'
    field = image.thumbnail if thumbnail else image.image
    response = FileResponse(field.open('rb'), content_type='image/webp' if thumbnail else {
        '.jpg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
    }[field.name[field.name.rfind('.'):].lower()])
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store' if not publicly_used else 'public, max-age=3600'
    return response
