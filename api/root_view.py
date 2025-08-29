from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    نمای API ریشه برای سامانه مدیریت دیابت.
    
    این تابع یک پاسخ ثابت (JSON-like) بازمی‌گرداند که اطلاعات کشف سرویس را شامل پیام خلاصه، تنظیمات احراز هویت مبتنی بر JWT (نقاط گرفتن/رفرش توکن و فرمت هدر)، سیاست مدیریت کاربران (ثبت‌نام فقط از طریق پنل ادمین)، آدرس‌های مطلق برای نقاط انتهایی اصلی (patients، encounters، labs، meds، refs) و آدرس‌های مرتبط با مستندات و اسکیمای API ارائه می‌دهد. آدرس‌ها با استفاده از request.build_absolute_uri از مسیرهای نسبی ساخته می‌شوند تا URLهای کامل برگردانده شوند.
    
    Parameters:
        request (Request): شیٔ درخواستی DRF/Django که برای ساخت URLهای مطلق استفاده می‌شود.
    
    Returns:
        Response: شیٔ rest_framework.response.Response که حاوی دیکشنری کشف سرویس ذکرشده است.
    
    نکات:
    - همهٔ نقاط انتهایی API به‌جز مسیرهای مربوط به دریافت/رفرش توکن از طریق JWT محافظت می‌شوند.
    - ایجاد حساب کاربری به‌صورت عمومی مجاز نیست و باید از طریق پنل ادمین انجام شود.
    - این تابع هیچ خطای خاصی را صریحاً پرتاب نمی‌کند؛ خطاهای مربوط به ساخت URL یا محیط وب توسط لایه‌های بالاتر مدیریت می‌شوند.
    """
    return Response({
        'message': 'Diabetes Management System API',
        'authentication': {
            'type': 'JWT (JSON Web Token)',
            'obtain_token': request.build_absolute_uri('/api/token/'),
            'refresh_token': request.build_absolute_uri('/api/token/refresh/'),
            'header_format': 'Authorization: Bearer <token>',
        },
        'user_management': {
            'registration': 'Admin panel only - no public registration',
            'admin_url': request.build_absolute_uri('/admin/'),
            'note': 'Contact system administrator for user account creation',
        },
        'endpoints': {
            'patients': request.build_absolute_uri('/api/patients/'),
            'encounters': request.build_absolute_uri('/api/encounters/'),
            'labs': request.build_absolute_uri('/api/labs/'),
            'medications': request.build_absolute_uri('/api/meds/'),
            'references': request.build_absolute_uri('/api/refs/'),
        },
        'documentation': {
            'schema': request.build_absolute_uri('/api/schema/'),
            'swagger': request.build_absolute_uri('/api/docs/'),
        }
    })