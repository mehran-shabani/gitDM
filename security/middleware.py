from .models import AuditLog

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            AuditLog.objects.create(
                user_id=getattr(request.user,'id',None),
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                meta={"remote_addr": request.META.get('REMOTE_ADDR')}
            )
        except Exception:
            pass
        return response