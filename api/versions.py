from rest_framework import viewsets, status, serializers, pagination
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import action
from rest_framework.response import Response
from records_versioning.models import RecordVersion
from records_versioning.services import revert_to_version
import logging

logger = logging.getLogger(__name__)

class RecordVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordVersion
        fields = ("version", "prev_version", "changed_at", "diff", "meta")


class VersionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request, resource_type: str | None = None, resource_id: str | None = None) -> Response:
        """
        لیستی از نسخه‌های یک منبع مشخص را بازمی‌گرداند.
        
        این متد رکوردهای مدل RecordVersion را با فیلتر resource_type و resource_id گرفته، بر اساس فیلد `version` به صورت صعودی مرتب می‌کند و یک پاسخ HTTP شامل لیستی از دیکشنری‌ها برمی‌گرداند. هر عنصر لیست شامل کلیدهای زیر است: `version` (شماره نسخه)، `prev_version` (نسخه قبلی در صورت وجود)، `changed_at` (زمان تغییر)، `diff` (تغییرات اعمال‌شده) و `meta` (متادیتای مرتبط). اگر هیچ نسخه‌ای پیدا نشود، یک لیست خالی بازگردانده می‌شود.
        
        Parameters:
            resource_type (str): نوع منبع برای فیلتر کردن نسخه‌ها (مثلاً نام مدل یا شناسه نوع).
            resource_id (str|int): شناسه منبع مشخص که نسخه‌های آن بازگردانده می‌شود.
        
        Returns:
            rest_framework.response.Response: پاسخ HTTP (وضعیت 200) حاوی لیست نسخه‌ها به صورت دیکشنری.
        """
        qs = RecordVersion.objects.filter(
        resource_type=resource_type, resource_id=resource_id).order_by('version')
        paginator = pagination.PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        ser = RecordVersionSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)


class VersionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    class _RevertSerializer(serializers.Serializer):
        target_version = serializers.IntegerField(min_value=1)

    @action(detail=False, methods=['post'])
    def revert(self, request, resource_type: str | None = None, resource_id: str | None = None) -> Response:
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
        
        ser = self._RevertSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target_version = ser.validated_data["target_version"]
        
        user = request.user if request.user.is_authenticated else None
        
        # وایت‌لیست resource_type
        from records_versioning.services import RESOURCE_MAP  # lazy import
        if resource_type not in RESOURCE_MAP:
            return Response({"error": "invalid resource_type"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            revert_to_version(resource_type, resource_id, target_version, user)
            return Response({"status": "ok", "reverted_to": target_version}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
-            logger.exception(
-                "revert failed",
-                extra={"resource_type": resource_type, "resource_id": str(resource_id)},
            logger.exception(
                "revert failed",
                extra={
                    "resource_type": resource_type,
                    "resource_id": str(resource_id),
                    "user_id": getattr(request.user, "pk", None),
                },
            )
            return Response({"error": "internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
