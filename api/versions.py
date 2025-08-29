from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from records_versioning.models import RecordVersion
from records_versioning.services import revert_to_version

class VersionViewSet(viewsets.ViewSet):
    def list(self, request, resource_type=None, resource_id=None):
        """
        لیستی از نسخه‌های یک منبع مشخص را بازمی‌گرداند.
        
        این متد رکوردهای مدل RecordVersion را با فیلتر resource_type و resource_id گرفته، بر اساس فیلد `version` به صورت صعودی مرتب می‌کند و یک پاسخ HTTP شامل لیستی از دیکشنری‌ها برمی‌گرداند. هر عنصر لیست شامل کلیدهای زیر است: `version` (شماره نسخه)، `prev_version` (نسخه قبلی در صورت وجود)، `changed_at` (زمان تغییر)، `diff` (تغییرات اعمال‌شده) و `meta` (متادیتای مرتبط). اگر هیچ نسخه‌ای پیدا نشود، یک لیست خالی بازگردانده می‌شود.
        
        Parameters:
            resource_type (str): نوع منبع برای فیلتر کردن نسخه‌ها (مثلاً نام مدل یا شناسه نوع).
            resource_id (str|int): شناسه منبع مشخص که نسخه‌های آن بازگردانده می‌شود.
        
        Returns:
            rest_framework.response.Response: پاسخ HTTP (وضعیت 200) حاوی لیست نسخه‌ها به صورت دیکشنری.
        """
        qs = RecordVersion.objects.filter(resource_type=resource_type, resource_id=resource_id).order_by('version')
        data = [{
            "version": v.version,
            "prev_version": v.prev_version,
            "changed_at": v.changed_at,
            "diff": v.diff,
            "meta": v.meta,
        } for v in qs]
        return Response(data)

    @action(detail=False, methods=['post'])
    def revert(self, request, resource_type=None, resource_id=None):
        # Get resource identifiers from URL parameters
        """
        درخواست بازگردانی (revert) یک منبع به یک نسخهٔ مشخص را پردازش می‌کند.
        
        جزئیات:
        - از پارامترهای URL انتظار دارد `resource_type` و `resource_id` مشخص شده باشند؛ در غیر این صورت پاسخ 400 برمی‌گرداند.
        - مقدار هدف برای بازگردانی باید در بدنهٔ درخواست تحت کلید `target_version` قرار داشته و قابل تبدیل به عدد صحیح باشد؛ در صورت نبود یا نامعتبر بودن، پاسخ 400 برمی‌گرداند.
        - کاربر انجام‌دهندهٔ عملیات از `request.user` گرفته می‌شود و تنها در صورت احراز هویت استفاده می‌شود؛ در غیر این صورت مقدار `None` به تابع سرویس ارسال می‌شود.
        - عملیات بازگردانی با فراخوانی سرویس `revert_to_version(resource_type, resource_id, target_version, user)` انجام می‌شود. در صورت موفقیت پاسخ 200 با بدنهٔ `{"status":"ok","reverted_to": target_version}` بازمی‌گردد.
        - هر استثنایی که از سرویس بالا بیرون بیاید در این سطح گرفته شده و به صورت پاسخ 400 همراه با پیام خطا (`{"error": "<message>"}`) بازگردانده می‌شود.
        
        پارامترها:
        - resource_type (str): نوع منبعی که باید بازگردانی شود (مثلاً نام مدل یا شناسهٔ منطقی منبع).
        - resource_id (str|int): شناسهٔ منبع هدف در سیستم.
        
        بازگشت:
        - شیء `Response` از Django REST Framework که وضعیت عملیات و در صورت خطا پیغام مناسب را شامل می‌شود.
        """
        if not resource_type or not resource_id:
            return Response(
                {"error": "Missing required URL parameters: resource_type and resource_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get target version from request body
        try:
            target_version = int(request.data.get('target_version'))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid or missing 'target_version' in request body"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user from authenticated request, not from request body
        user = request.user if request.user.is_authenticated else None
        
        try:
            revert_to_version(resource_type, resource_id, target_version, user)
            return Response({"status":"ok","reverted_to": target_version}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)