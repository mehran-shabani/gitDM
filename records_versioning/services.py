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
    # Convert UUIDs to strings for JSON serialization
    for key, value in d.items():
        if hasattr(value, 'hex'):  # UUID objects have hex attribute
            d[key] = str(value)
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
def save_with_version(instance, user, reason=""):
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
            changed_by=user,
        )
    finally:
        _thread_state.in_version = False

@transaction.atomic
def revert_to_version(resource_type: str, resource_id, target_version: int, user, reason="revert"):
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
    save_with_version(obj, user, reason=f"{reason}: to v{target_version}")
    return obj