from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid


class AISummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        نمایش متنی مختصر از نمونه AISummary.
        
        این متد یک رشتهٔ خوانا برای نمونهٔ مدل برمی‌گرداند به شکل:
        "AI Summary for {نام کامل بیمار} - {نوع محتوای مرتبط}".
        برای تولید این متن از self.patient.full_name و self.content_type.model استفاده می‌کند. هیچ اثر جانبی ندارد.
        """
        return f"AI Summary for {self.patient.full_name} - {self.content_type.model}"