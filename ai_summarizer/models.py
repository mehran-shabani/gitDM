from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
import uuid


class AISummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def resource_type(self) -> str:
        """Backward-compatible property for admin display."""
        return self.content_type.model
    
    resource_type.fget.short_description = "Resource Type"  # type: ignore

    def clean(self) -> None:
        """
        اعتبارسنجی تطابق بیمار مرتبط: در صورتی که `content_object` تنظیم شده و دارای صفت `patient` باشد، بررسی می‌کند که همان بیمار با `self.patient` یکسان باشد.
        
        این متد برای اجرای اعتبارسنجی مدل (مثلاً هنگام فراخوانی `full_clean()` یا در فرم‌های ادمین) استفاده می‌شود و در صورت نابرابر بودن بیمار مرتبط، یک `ValidationError` برمی‌گرداند که به کلید فیلد `'patient'` اختصاص دارد.
        Raises:
            django.core.exceptions.ValidationError: وقتی بیمار مرتبط با `content_object` با `self.patient` همخوانی نداشته باشد (خطا برای فیلد `'patient'` گزارش می‌شود).
        """
        if self.content_object and hasattr(self.content_object, 'patient'):
            if self.content_object.patient != self.patient:
                raise ValidationError({
                    'patient': 'Patient mismatch: The selected patient must match the patient of the related object.'
                })

    def __str__(self) -> str:
from __future__ import annotations

    def resource_type(self: "AISummary") -> str:
        """
        نام مدل مرتبط از ContentType برای نمایش در رابط مدیریت (سازگاری عقب‌ماندگار).
        
        این پراپرتی نام مدل مرتبط با این نمونه AISummary را برمی‌گرداند (همان مقدار content_type.model)
        که برای ستون/نمایش در Django admin حفظ شده تا سازگاری با نسخه‌های قدیمی‌تر برقرار بماند.
        
        Returns:
        	str: نام مدل مرتبط (مقدار content_type.model).
        """
        return self.content_type.model

    def clean(self: "AISummary") -> None:
        """
        یک‌خطی: اعتبارسنجی می‌کند که در صورت وجود، شیٔ مرتبط (`content_object`) متعلق به همان بیمار (`patient`) باشد.
        
        توضیحات: اگر این نمونه دارای `content_object` باشد و آن شیٔ صفت `patient` داشته باشد، مقدار `patient` آن با `self.patient` مقایسه می‌شود. در صورت عدم مطابقت، یک `ValidationError` برای فیلد `patient` بالا می‌آورد تا از ذخیره‌سازی یا پاک‌سازی داده‌های ناسازگار جلوگیری شود.
        
        Raises:
            django.core.exceptions.ValidationError: وقتی `content_object.patient` با `self.patient` همخوانی نداشته باشد، یک خطای اعتبارسنجی برای کلید `'patient'` برمی‌گرداند.
        """
        if self.content_object and hasattr(self.content_object, 'patient'):
            if self.content_object.patient != self.patient:
                raise ValidationError({
                    'patient': 'Patient mismatch: The selected patient must match the patient of the related object.'
                })

    def __str__(self: "AISummary") -> str:
        """
        نمایش متنی شیء برای رابط ادمین: یک برچسب خوانا شامل نام کامل بیمار و نام مدل مرتبط.
        
        این متد یک رشته برمی‌گرداند که در رابط ادمین یا هنگام تبدیل شی به رشته نمایش داده می‌شود. قالب خروجی:
        "AI Summary for <patient.full_name> - <content_type.model>"
        
        Returns:
        	str: برچسب متنی برای نمایش، ساخته‌شده از فیلدهای `patient.full_name` و `content_type.model`.
        """
        return f"AI Summary for {self.patient.full_name} - {self.content_type.model}"


