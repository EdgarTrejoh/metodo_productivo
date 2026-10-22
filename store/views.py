from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .models import DigitalProduct


def index(request):
    return render(request, 'store/index.html', {'products': DigitalProduct.live().select_related('image')})


def detail(request, slug):
    product = get_object_or_404(DigitalProduct.live().select_related('image'), slug=slug)
    return render(request, 'store/detail.html', {
        'product': product,
        'show_test_checkout': bool(
            settings.DEBUG and settings.STORE_TEST_CHECKOUT_ENABLED
            and product.has_valid_test_payment_url
        ),
    })
