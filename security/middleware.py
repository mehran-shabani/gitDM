from .models import AuditLog
import uuid

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            # Convert integer user ID to UUID format for auditing
            user_id = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                # Create a deterministic UUID from user ID for auditing purposes
                user_id = uuid.uuid5(uuid.NAMESPACE_DNS, f'user-{request.user.id}')
            
            AuditLog.objects.create(
                user_id=user_id,
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                meta={"remote_addr": request.META.get('REMOTE_ADDR')}
            )
        except Exception:
            pass
        return response