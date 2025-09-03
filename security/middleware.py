import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import AuditLog, SecurityEvent

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware برای ثبت خودکار فعالیت‌های کاربران
    """
    
    # Actions که نیاز به audit logging دارند
    AUDITABLE_ACTIONS = {
        'POST': AuditLog.ActionType.CREATE,
        'PUT': AuditLog.ActionType.UPDATE,
        'PATCH': AuditLog.ActionType.UPDATE,
        'DELETE': AuditLog.ActionType.DELETE,
    }
    
    # Resources که باید audit شوند
    AUDITABLE_RESOURCES = [
        'patients', 'encounters', 'labs', 'meds', 'ai-summaries', 'refs'
    ]
    
    def process_response(self, request, response):
        """
        پردازش response و ثبت audit log در صورت نیاز
        """
        # فقط برای کاربران احراز هویت شده
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return response
        
        # فقط برای درخواست‌های API
        if not request.path.startswith('/api/'):
            return response
        
        # فقط برای actions قابل audit
        if request.method not in self.AUDITABLE_ACTIONS:
            return response
        
        # فقط برای response های موفق
        if not (200 <= response.status_code < 300):
            return response
        
        try:
            # استخراج اطلاعات از URL
            resolved = resolve(request.path)
            url_name = resolved.url_name
            
            # بررسی اینکه آیا resource قابل audit است
            resource_type = None
            for resource in self.AUDITABLE_RESOURCES:
                if resource in request.path:
                    resource_type = resource
                    break
            
            if not resource_type:
                return response
            
            # استخراج resource_id از URL
            resource_id = resolved.kwargs.get('pk') or resolved.kwargs.get('id')
            
            # استخراج patient_id
            patient_id = self._extract_patient_id(request, response, resource_type)
            
            # ثبت audit log
            action = self.AUDITABLE_ACTIONS[request.method]
            
            old_values = None
            new_values = None
            
            # برای UPDATE، سعی در استخراج داده‌های قدیم و جدید
            if action == AuditLog.ActionType.UPDATE and hasattr(request, '_cached_old_data'):
                old_values = request._cached_old_data
                
            if hasattr(response, 'data') and response.data:
                new_values = response.data
            
            AuditLog.log_action(
                user=request.user,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                patient_id=patient_id,
                old_values=old_values,
                new_values=new_values,
                request=request,
                notes=f"API call: {request.method} {request.path}"
            )
            
        except Exception as e:
            # Log error اما response را block نکن
            logger.error(f"Audit logging failed: {str(e)}")
        
        return response
    
    def _extract_patient_id(self, request, response, resource_type):
        """
        استخراج patient_id از request یا response
        """
        # اگر resource خود patient است
        if resource_type == 'patients':
            if hasattr(response, 'data') and 'id' in response.data:
                return response.data['id']
        
        # برای سایر resources، patient_id را از request body یا response جستجو کن
        if hasattr(request, 'data') and 'patient' in request.data:
            return request.data['patient']
        
        if hasattr(response, 'data') and 'patient' in response.data:
            return response.data['patient']
        
        return None


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware برای تشخیص و ثبت رویدادهای امنیتی
    """
    
    def process_request(self, request):
        """
        بررسی درخواست برای تشخیص فعالیت‌های مشکوک
        """
        # بررسی تعداد درخواست‌های زیاد از یک IP
        ip_address = self._get_client_ip(request)
        
        # اینجا می‌توان logic های پیچیده‌تری برای تشخیص تهدیدات اضافه کرد
        # مثل rate limiting، pattern recognition، etc.
        
        return None
    
    def process_response(self, request, response):
        """
        بررسی response برای تشخیص مسائل امنیتی
        """
        # ثبت failed login attempts
        if (request.path == '/api/token/' and 
            request.method == 'POST' and 
            response.status_code == 401):
            
            try:
                SecurityEvent.objects.create(
                    event_type=SecurityEvent.EventType.FAILED_LOGIN,
                    user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'path': request.path, 'method': request.method},
                    severity='MEDIUM'
                )
            except Exception as e:
                logger.error(f"Security event logging failed: {str(e)}")
        
        return response
    
    def _get_client_ip(self, request):
        """
        استخراج IP واقعی کلاینت
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')