# کدهای الزامی – Versioning

## records_versioning/models.py (به‌روزرسانی)
from django.db import models
from django.utils import timezone

class RecordVersion(models.Model):
    id = models.BigAutoField(primary_key=True)
    resource_type = models.CharField(max_length=48)  # 'Patient','Encounter','LabResult','MedicationOrder'
    resource_id = models.UUIDField()
    version = models.PositiveIntegerField()
    prev_version = models.PositiveIntegerField(null=True, blank=True)
    snapshot = models.JSONField()
    diff = models.JSONField(null=True, blank=True)  # تغییرات خلاصه
    meta = models.JSONField(default=dict, blank=True)
    changed_by = models.UUIDField()
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("resource_type", "resource_id", "version")
        indexes = [
            models.Index(fields=["resource_type", "resource_id", "version"]),
            models.Index(fields=["changed_at"]),
        ]

## records_versioning/apps.py (جدید)
from django.apps import AppConfig

class RecordsVersioningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'records_versioning'

    def ready(self):
        from . import signals  # noqa

## records_versioning/__init__.py (جدید)
default_app_config = 'records_versioning.apps.RecordsVersioningConfig'

## records_versioning/services.py (جدید)
import threading
from django.db import transaction
from django.forms.models import model_to_dict
from django.apps import apps
from .models import RecordVersion

_thread_state = threading.local()

IGNORE_FIELDS = {"id", "pk", "created_at", "updated_at"}

RESOURCE_MAP = {
    'Patient': ('patients_core', 'Patient'),
    'Encounter': ('diab_encounters', 'Encounter'),
    'LabResult': ('diab_labs', 'LabResult'),
    'MedicationOrder': ('diab_medications', 'MedicationOrder'),
}

def _compute_snapshot(instance):
    d = model_to_dict(instance)
    return d

def _compute_diff(prev, curr):
    if not prev:
        return None
    keys = set(prev.keys()) | set(curr.keys())
    delta = {}
    for k in keys:
        if k in IGNORE_FIELDS:
            continue
        pv, cv = prev.get(k), curr.get(k)
        if pv != cv:
            delta[k] = {"from": pv, "to": cv}
    return delta or None

@transaction.atomic
def save_with_version(instance, user_id, reason=""):
    if getattr(_thread_state, 'in_version', False):
        return
    _thread_state.in_version = True
    try:
        rtype = instance.__class__.__name__
        rid = getattr(instance, 'id')
        curr = _compute_snapshot(instance)
        last = (RecordVersion.objects
                .filter(resource_type=rtype, resource_id=rid)
                .order_by('-version')
                .first())
        next_ver = 1 if not last else last.version + 1
        prev_snap = None if not last else last.snapshot
        diff = _compute_diff(prev_snap, curr)
        RecordVersion.objects.create(
            resource_type=rtype,
            resource_id=rid,
            version=next_ver,
            prev_version=None if not last else last.version,
            snapshot=curr,
            diff=diff,
            meta={"reason": reason},
            changed_by=user_id,
        )
    finally:
        _thread_state.in_version = False

@transaction.atomic
def revert_to_version(resource_type: str, resource_id, target_version: int, user_id, reason="revert"):
    Model = apps.get_model(*RESOURCE_MAP[resource_type])
    obj = Model.objects.get(id=resource_id)
    target = RecordVersion.objects.get(resource_type=resource_type, resource_id=resource_id, version=target_version)
    # اعمال snapshot بر روی شیء
    for k, v in target.snapshot.items():
        if k in IGNORE_FIELDS:
            continue
        setattr(obj, k, v)
    obj.save(update_fields=[k for k in target.snapshot.keys() if k not in IGNORE_FIELDS])
    # ثبت نسخهٔ جدید پس از بازگردانی
    save_with_version(obj, user_id, reason=f"{reason}: to v{target_version}")
    return obj

## records_versioning/signals.py (جدید)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.apps import apps
from .services import save_with_version

WATCH = [
    ('patients_core', 'Patient'),
    ('diab_encounters', 'Encounter'),
    ('diab_labs', 'LabResult'),
    ('diab_medications', 'MedicationOrder'),
]

for app_label, model_name in WATCH:
    Model = apps.get_model(app_label, model_name)

    @receiver(post_save, sender=Model)
    def _on_saved(sender, instance, created, **kwargs):
        user_id = getattr(instance, 'created_by', None) or getattr(instance, 'updated_by', None) or getattr(settings, 'SYSTEM_USER_ID', None)
        if user_id is None:
            # در این فاز در نبود user، یک UUID ثابت سیستم استفاده شود
            import uuid
            user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        save_with_version(instance, user_id, reason='auto-signal')

## api/versions.py (جدید)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from records_versioning.models import RecordVersion
from records_versioning.services import revert_to_version

class VersionViewSet(viewsets.ViewSet):
    def list(self, request, resource_type=None, resource_id=None):
        qs = RecordVersion.objects.filter(resource_type=resource_type, resource_id=resource_id).order_by('version')
        data = [{
            "version": v.version,
            "prev_version": v.prev_version,
            "changed_at": v.changed_at,
            "diff": v.diff,
            "meta": v.meta,
        } for v in qs]
        return Response(data)

    @action(detail=False, methods=['post'])
    def revert(self, request):
        resource_type = request.data.get('resource_type')
        resource_id = request.data.get('resource_id')
        target_version = int(request.data.get('target_version'))
        user_id = request.data.get('user_id')
        revert_to_version(resource_type, resource_id, target_version, user_id)
        return Response({"status":"ok","reverted_to": target_version}, status=status.HTTP_200_OK)

## config/urls.py (افزودن مسیرهای نسخه)
from django.urls import path
from api.versions import VersionViewSet

version_list = VersionViewSet.as_view({'get':'list'})
version_revert = VersionViewSet.as_view({'post':'revert'})

urlpatterns += [
    path('api/versions/<str:resource_type>/<uuid:resource_id>/', version_list),
    path('api/versions/revert/', version_revert),
]