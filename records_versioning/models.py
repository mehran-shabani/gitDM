from django.db import models
import uuid

class RecordVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource_type = models.CharField(max_length=50)
    resource_id = models.UUIDField()
    version_number = models.IntegerField()
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('resource_type', 'resource_id', 'version_number')

    def __str__(self):
        return f"{self.resource_type} {self.resource_id} v{self.version_number}"