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
        """Validate that year is not in the future."""
        if self.year > timezone.now().year + 1:
            raise ValidationError({
                'year': f'Year cannot be more than one year in the future. Maximum allowed: {timezone.now().year + 1}'
            })

    def __str__(self) -> str:
        """
        نمایش خوانا برای نمونه ClinicalReference: عنوان و سال در قالب "عنوان (سال).
        
        این متد یک رشتهٔ قابلِ نمایش برای نمونهٔ مدل بازمی‌گرداند (مثلاً در رابط مدیریت Django، خروجی shell و نمایش‌های متنی)، به صورت "<title> (<year>)".
        
        Returns:
            str: رشته‌ای حاوی عنوان و سال به قالب "<عنوان> (<سال>)".
        """
        return f"{self.title} ({self.year})"

