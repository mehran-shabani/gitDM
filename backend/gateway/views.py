from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.http import require_safe
from django.views.decorators.cache import never_cache


@require_safe
@never_cache
def health(request):
    if request.method not in ("GET", "HEAD"):
        return HttpResponseNotAllowed(["GET", "HEAD"])
    res = JsonResponse({"status": "ok"})
    res["Pragma"] = "no-cache"
    return res
