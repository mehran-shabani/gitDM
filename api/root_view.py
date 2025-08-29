from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    نمای کلی API ریشه برای سیستم مدیریت دیابت.
    
    این نما (GET) یک پاسخ JSON بازمی‌گرداند که به‌صورت یک «مانیفست اکتشافی» شامل متادیتا و آدرس‌های مطلق نقاط انتهایی و مستندات سرویس است. ورودی request برای ساخت URLهای مطلق با request.build_absolute_uri استفاده می‌شود. ساختار پاسخ شامل بخش‌های زیر است: پیام کوتاه، اطلاعات احراز هویت (نوع: JWT و مسیرهای دریافت/رفرش توکن و قالب هدر)، مدیریت کاربران (ثبت‌نام فقط از طریق پنل ادمین)، لیست نقاط انتهایی اصلی (patients, encounters, labs, medications, references) و لینک‌های مستندات (schema و swagger).
    
    دسترسی: خودِ این نما به‌طور عمومی در دسترس است (AllowAny)؛ اما اکثر نقاط انتهایی API طبق سیاست سامانه با JWT محافظت می‌شوند و توکن‌ها از مسیرهای ذکرشده دریافت/رفرش می‌شوند.
    
    مقدار بازگشتی:
        یک نمونهٔ rest_framework.response.Response شامل یک دیکشنری JSON با ساختار توضیح‌داده‌شده که همهٔ آدرس‌ها بصورت URL مطلق بر پایهٔ request ساخته شده‌اند.
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
            'redoc': request.build_absolute_uri('/api/redoc/'),
            'rapidoc': request.build_absolute_uri('/api/rapidoc/'),
        }
    })
