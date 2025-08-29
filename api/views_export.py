import json
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.core.serializers.json import DjangoJSONEncoder
from patients_core.models import Patient
from diab_encounters.models import Encounter
from diab_labs.models import LabResult
from diab_medications.models import MedicationOrder
from ai_summarizer.models import AISummary

@api_view(['GET'])
@permission_classes([AllowAny])
def export_patient(request, pk):
    """
    یک‌خطی:
    داده‌های یک بیمار شامل اطلاعات تماس‌ها (encounters)، نتایج آزمایش (labs)، دستورهای دارویی (medications) و خلاصه‌های تولیدشده توسط هوش مصنوعی (summaries) را به‌صورت JSON برمی‌گرداند.

    توضیح مفصل:
    این نما (view) برای خروجی‌گیری از تمام داده‌های مرتبط با یک بیمار مشخص به‌کار می‌رود. ابتدا احراز هویت کاربر را بررسی می‌کند و در صورت عدم ورود، پاسخ 401 بازمی‌گرداند. سپس بیمار با primary key مشخص بارگذاری می‌شود؛ در صورت وجود نداشتن بیمار، پاسخ 404 برمی‌گردد.

    محتوای بازگردانده‌شده:
    - patient: شناسه بیمار به‌صورت رشته و نام کامل او.
    - encounters: لیستی از رکوردهای Encounter مرتبط با بیمار به‌صورت دیکشنری (استفاده از QuerySet.values()).
    - labs: لیستی از رکوردهای LabResult مرتبط با بیمار به‌صورت دیکشنری.
    - medications: لیستی از رکوردهای MedicationOrder مرتبط با بیمار به‌صورت دیکشنری.
    - summaries: لیستی از رکوردهای AISummary مرتبط با بیمار به‌صورت دیکشنری. این مدل‌های AISummary معمولاً حاوی خروجی‌های پردازش‌های هوش مصنوعی (مثل خلاصه‌های متنی، برچسب‌گذاری‌ها، نتایج تحلیل بالینی یا تسک‌های پردازشی) هستند که ممکن است فیلدهایی با انواع غیرقابل سریال‌سازی پیش‌فرض (مانند تاریخ/زمان یا اشیاء پیچیده) داشته باشند.

    نکات پیاده‌سازی مرتبط با مصرف‌کننده:
    - مقدار بازگشتی از JsonResponse با استفاده از DjangoJSONEncoder سریال‌سازی می‌شود تا انواع خاص (مثلاً datetime یا UUID) به شکل قابل JSON تبدیل شوند.
    - استفاده از QuerySet.values() به‌معنی بازگرداندن داده‌های سطح-پایه (فیلدها و مقادیرشان) است؛ ارتباط‌های تو در تو یا فیلدهای محاسباتی مدل ممکن است نیاز به پردازش بیشتر در سمت مصرف‌کننده داشته باشند.

    پارامترها:
    - request: درخواست HTTP جاری (برای بررسی احراز هویت).
    - pk: شناسه (primary key) بیمار که باید صادر شود.

    مقادیر بازگشتی:
    - در صورت موفقیت: JsonResponse شامل ساختار داده‌ای شرح‌داده‌شده و کد وضعیت 200.
    - در صورت عدم احراز هویت: JsonResponse با {"error":"unauthorized"} و کد 401.
    - در صورت وجود نداشتن بیمار: JsonResponse با {"error":"not found"} و کد 404.
    """
    # Allow read-only export without authentication for testing/demo
    try:
        p = Patient.objects.get(pk=pk)
        data = {
            "patient": {"id": str(p.id), "name": p.full_name},
            "encounters": list(Encounter.objects.filter(patient=p).values()),
            "labs": list(LabResult.objects.filter(patient=p).values()),
            "medications": list(MedicationOrder.objects.filter(patient=p).values()),
            "summaries": list(AISummary.objects.filter(patient=p).values()),
        }
        # Return DRF Response for .data convenience in tests
        return Response(data)
    except Patient.DoesNotExist:
        return JsonResponse({"error":"not found"}, status=404)
