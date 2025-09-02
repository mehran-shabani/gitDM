from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from gitdm.models import PatientProfile
from rest_framework.response import Response

from .models import RecordVersion
from .services import revert_to_version


# Create your views here.


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def versions_list(request, resource_type: str, resource_id: str):
    # Ownership check (only for Patient or resources tied to a patient)
    user = getattr(request, 'user', None)
    if not getattr(user, 'is_superuser', False):
        if resource_type == 'Patient':
            try:
                patient = PatientProfile.objects.only('id', 'primary_doctor_id').get(id=resource_id)
            except PatientProfile.DoesNotExist:
                # Empty history if resource not found
                return Response([], status=status.HTTP_200_OK)
            if patient.primary_doctor_id != user.id:
                raise PermissionDenied("You may only view versions for your own patients.")
        # For other resource types, optionally could resolve to patient and check ownership (left minimal here)

    qs = RecordVersion.objects.filter(resource_type=resource_type, resource_id=str(resource_id)).order_by("version")
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
    # Only superuser or owner doctor can revert Patient; for other types, align similarly if needed
    user = getattr(request, 'user', None)
    if not getattr(user, 'is_superuser', False):
        if resource_type == 'Patient':
            try:
                patient = PatientProfile.objects.only('id', 'primary_doctor_id').get(id=resource_id)
            except PatientProfile.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            if patient.primary_doctor_id != user.id:
                raise PermissionDenied("You may only revert versions for your own patients.")

    target_version = request.data.get("target_version")
    if target_version is None:
        return Response({"target_version": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    try:
        target_version_int = int(target_version)
    except Exception:
        return Response({"target_version": ["Must be an integer."]}, status=status.HTTP_400_BAD_REQUEST)

    user = getattr(request, "user", None)
    obj = revert_to_version(resource_type, resource_id, target_version_int, user)
    return Response({"ok": True, "id": obj.pk}, status=status.HTTP_200_OK)
