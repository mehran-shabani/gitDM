from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class ClinicalReference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    source = models.CharField(max_length=120)
    year = models.PositiveIntegerField(validators=[MinValueValidator(1900)])
    url = models.URLField(blank=True)
    topic = models.CharField(max_length=80)

    class Meta:
        ordering = ["-year", "title"]
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["year"]),
            models.Index(fields=["topic"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["title", "source", "year"],
                name="uniq_clinref_title_source_year",
            ),
        ]

    def clean(self) -> None:
        """
        بررسی و اعتبارسنجی فیلد `year` مدل: اطمینان می‌دهد مقدار سال بیشتر از یک سال جلوتر از سال جاری نباشد.
        
        اگر مقدار `year` بزرگ‌تر از (سال جاری + 1) باشد، یک `ValidationError` برگردانده می‌شود که به صورت ساختاری برای فیلد `'year'` پیام خطا شامل حداکثر سال مجاز را فراهم می‌کند. مقایسه براساس زمان منطقه‌ای سرور با استفاده از `timezone.now().year` انجام می‌شود.
        """
        if self.year > timezone.now().year + 1:
            raise ValidationError({
                'year': f'Year cannot be more than one year in the future. Maximum allowed: {timezone.now().year + 1}'
            })

    def __str__(self) -> str:
        """
        رشتهٔ نمایشی نمونه ClinicalReference را برمی‌گرداند.
        
        این متد یک نمایش کوتاه و خوانا برای نمونهٔ مدل فراهم می‌کند که معمولاً در رابط مدیریت Django، خروجی تعاملی (shell) و هرجایی که نمونه به رشته تبدیل می‌شود نمایش داده می‌شود. قالب خروجی دقیقا به صورت "<عنوان> (<سال>)" است؛ عنوان از فیلد title و سال از فیلد year گرفته می‌شود.
        
        Returns:
            str: رشته‌ای حاوی عنوان و سال به قالب "<عنوان> (<سال>)".
        """
        return f"{self.title} ({self.year})"

