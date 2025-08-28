from django.db import models
from django.db.models import Q, F
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings


class RecordVersion(models.Model):
    id = models.BigAutoField(primary_key=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    version = models.PositiveIntegerField()
    prev_version = models.PositiveIntegerField(null=True, blank=True)
    snapshot = models.JSONField(default=dict)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="record_versions",
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-changed_at", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "version"],
                name="uniq_record_version",
            ),
            models.CheckConstraint(
                check=(Q(prev_version__lt=F("version")) | Q(prev_version__isnull=True)),
                name="prev_lt_version_or_null",
            ),
            models.CheckConstraint(
                check=Q(version__gte=1),
                name="version_gte_1",
            ),
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"], name="idx_ct_obj"),
            models.Index(fields=["content_type", "object_id", "-version"], name="idx_ct_obj_version_desc"),
        ]

    def __str__(self) -> str:
        """
        نمایش متنی خوانا برای نمونه RecordVersion.
        
        برمی‌گرداند یک رشته مختصر که نوع مدل مرتبط، شناسه شیء و شماره نسخه را به صورت "<model> <object_id> v<version>" نمایش می‌دهد. این مقدار برای نمایش در پنل ادمین، لاگ‌ها و خروجی‌های متنی مفید است.
        """
        return f"{self.content_type.app_label}.{self.content_type.model} {self.object_id} v{self.version}"