from django.db import models
from django.utils import timezone
from django.conf import settings

class RecordVersion(models.Model):
    id = models.BigAutoField(primary_key=True)
    resource_type = models.CharField(max_length=48)  # 'Patient','Encounter','LabResult','MedicationOrder'

    resource_id = models.PositiveIntegerField()
    version = models.PositiveIntegerField()
    prev_version = models.PositiveIntegerField(null=True, blank=True)
    snapshot = models.JSONField()
    diff = models.JSONField(null=True, blank=True)  # تغییرات خلاصه
    meta = models.JSONField(default=dict, blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("resource_type", "resource_id", "version")
        indexes = [
            models.Index(fields=["resource_type", "resource_id", "version"]),
            models.Index(fields=["changed_at"]),
        ]
