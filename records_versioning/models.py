from django.db import models
import uuid


class RecordVersion(models.Model):
    id = models.BigAutoField(primary_key=True)
    resource_type = models.CharField(max_length=32)
    resource_id = models.UUIDField()
    version = models.PositiveIntegerField()
    prev_version = models.PositiveIntegerField(null=True, blank=True)
    snapshot = models.JSONField()
    changed_by = models.UUIDField()
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resource_type} {self.resource_id} v{self.version}"