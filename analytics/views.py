from django.http import HttpResponse
from django.views.decorators.http import require_POST

from .tracking import record_cta


@require_POST
def home_cta(request):
    if not record_cta(request, request.POST.get('cta'), request.POST.get('operation')):
        return HttpResponse(status=400)
    return HttpResponse(status=204)
