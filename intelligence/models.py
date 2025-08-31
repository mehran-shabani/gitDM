from __future__ import annotations
import uuid
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError


class AISummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('gitdm.PatientProfile', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.CharField(max_length=64, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    summary = models.TextField()
    references = models.ManyToManyField(
        'references.ClinicalReference',
        blank=True,
        help_text="Clinical references automatically linked based on summary content"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def resource_type(self: "AISummary") -> str:
        """
        نام مدل مرتبط با شیء پیوست‌شده را برمی‌گرداند (برای نمایش سازگار با نسخه‌های قبلی در پنل ادمین).

        این متد مقدار `content_type.model` را برمی‌گرداند که نام مدل مربوط به شیء مرتبط را نشان می‌دهد. برای نمایش کوتاه در پنل ادمین و نگه‌داشتن سازگاری با نسخه‌های قبلی کلاس به‌عنوان یک ویژگی بازگشتی استفاده می‌شود.

        Returns:
            str: نام مدل مرتبط (معمولاً به صورت حروف کوچک).
        """
        return self.content_type.model

    def clean(self: "AISummary") -> None:
        """
        یک‌خطی:
        اعتبارسنجی می‌کند که اگر شیء مرتبط (content_object) دارای فیلد patient باشد، همان بیمارِ AISummary باشد.

        توضیح تفصیلی:
        این متد هنگام اعتبارسنجی مدل اجرا می‌شود و در صورت وجود content_object و داشتن صفت `patient`، مقدار آن را با `self.patient` مقایسه می‌کند. در صورت ناهماهنگی بین بیماران، یک ValidationError برای فیلد `patient` بالا می‌برد تا از ذخیره‌سازی یا پردازش داده‌های نامتجانس جلوگیری کند.

        استثناها:
        - ValidationError: زمانی که patient مربوط به content_object با patient این AISummary مطابقت نداشته باشد.
        """
        if self.content_object and hasattr(self.content_object, 'patient'):
            if self.content_object.patient != self.patient:
                raise ValidationError({
                    'patient': 'Patient mismatch: The selected patient must match the patient of the related object.'
                })

    def __str__(self: "AISummary") -> str:
        """
        رشته‌نمایشی مدل برای نمایش در ادمین: یک برچسب قابل خواندن که خلاصهٔ هوش‌مصنوعی را به صورت "AI Summary for <نام کامل بیمار> - <نام مدل مرتبط>" برمی‌گرداند.

        این مقدار برای نمایش در لیست‌ها و صفحات ادمین استفاده می‌شود و از فیلدهای `patient.full_name` و `content_type.model` برای ساخت رشته استفاده می‌کند.
        """

        return f"AI Summary for {self.patient.full_name} - {self.content_type.model}"