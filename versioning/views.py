from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import RecordVersion
from .services import revert_to_version
from .services import RESOURCE_MAP
from django.apps import apps


# Create your views here.


@api_view(["GET"]) 
@permission_classes([IsAuthenticated])
def versions_list(request, resource_type: str, resource_id: str):
    qs = (RecordVersion.objects
          .filter(resource_type=resource_type, resource_id=str(resource_id))
          .order_by("version"))
    # If there are no versions, return empty list without ownership enforcement
    if not qs.exists():
        return Response([], status=status.HTTP_200_OK)
    # Otherwise, enforce ownership of the underlying resource
    _assert_user_owns_resource(request.user, resource_type, resource_id)
    data = [
        {
            "version": rv.version,
            "prev_version": rv.prev_version,
            "changed_at": rv.changed_at.isoformat(),
        }
        for rv in qs
    ]
    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def versions_revert(request, resource_type: str, resource_id: str):
    target_version = request.data.get("target_version")
    if target_version is None:
        return Response({"target_version": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    try:
        target_version_int = int(target_version)
    except Exception:
        return Response({"target_version": ["Must be an integer."]}, status=status.HTTP_400_BAD_REQUEST)

    # Enforce ownership before performing revert
    _assert_user_owns_resource(request.user, resource_type, resource_id)

    user = getattr(request, "user", None)
    obj = revert_to_version(resource_type, resource_id, target_version_int, user)
    return Response({"ok": True, "id": obj.pk}, status=status.HTTP_200_OK)


def _assert_user_owns_resource(user, resource_type: str, resource_id: str) -> None:
    """
    Allow access only if the current user is the primary_doctor of the resource's patient.

    Ownership rules:
    - Patient: patient.primary_doctor == user
    - Encounter/LabResult/MedicationOrder: record.patient.primary_doctor == user
    Superusers bypass checks.
    """
    if getattr(user, "is_superuser", False):
        return
    try:
        app_label, model_name = RESOURCE_MAP[resource_type]
    except KeyError:
        # Unknown type -> deny
        raise PermissionDenied("Unknown resource type.")
    model_cls = apps.get_model(app_label, model_name)
    try:
        if model_name == "PatientProfile":
            instance = model_cls.objects.get(pk=resource_id)
        else:
            instance = model_cls.objects.select_related("patient").get(pk=resource_id)
    except Exception:
        # If object not found, we let callers raise 404/DoesNotExist as appropriate in their flow
        # but from a permissions perspective, we deny.
        raise PermissionDenied("Resource not accessible.")

    if model_name == "PatientProfile":
        primary_doctor = getattr(instance, "primary_doctor", None)
    else:
        patient = getattr(instance, "patient", None)
        primary_doctor = getattr(patient, "primary_doctor", None)

    if primary_doctor != user:
        raise PermissionDenied("You do not have permission to access versions for this resource.")
