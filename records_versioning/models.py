from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
import uuid


class RecordVersion(models.Model):
    id = models.BigAutoField(primary_key=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    version = models.PositiveIntegerField()
    prev_version = models.PositiveIntegerField(null=True, blank=True)
    snapshot = models.JSONField()
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content_type.model} {self.object_id} v{self.version}"