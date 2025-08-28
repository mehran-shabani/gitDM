from django.db import models
import uuid


class ClinicalReference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    source = models.CharField(max_length=120)
    year = models.PositiveIntegerField()
    url = models.URLField(blank=True)
    topic = models.CharField(max_length=80)

    def __str__(self):
        """
        نمایش رشته‌ای نمونه به صورت "عنوان (سال)".
        
        یک رشته بازمی‌گرداند که عنوان مرجع و سال آن را در قالب "title (year)" نمایش می‌دهد. این نمایش در رابط ادمین، هنگام لاگ‌گیری، و هر جایی که نمونه مدل به رشته تبدیل شود استفاده می‌شود.
        """
        return f"{self.title} ({self.year})"