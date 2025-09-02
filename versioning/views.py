from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import RecordVersion
from .services import revert_to_version


# Create your views here.


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def versions_list(request, resource_type: str, resource_id: str):
    qs = RecordVersion.objects.filter(resource_type=resource_type, resource_id=str(resource_id)).order_by("version")
    # Ownership check: if not superuser, ensure user is primary_doctor for the resource when applicable
    user = getattr(request, 'user', None)
    if not getattr(user, 'is_superuser', False):
        from django.apps import apps
        from .services import RESOURCE_MAP
        if resource_type in RESOURCE_MAP:
            app_label, model_name = RESOURCE_MAP[resource_type]
            model_cls = apps.get_model(app_label, model_name)
            try:
                obj = model_cls.objects.get(id=resource_id)
            except model_cls.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)
            # For models that have patient linkage, resolve to patient
            patient = getattr(obj, 'patient', None)
            if patient is not None:
                if getattr(patient, 'primary_doctor_id', None) != user.id:
                    raise PermissionDenied("You do not have permission to view versions for this resource.")
            elif hasattr(obj, 'primary_doctor_id'):
                if getattr(obj, 'primary_doctor_id', None) != user.id:
                    raise PermissionDenied("You do not have permission to view versions for this resource.")
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

    # Ownership check similar to versions_list
    user = getattr(request, "user", None)
    if not getattr(user, 'is_superuser', False):
        from django.apps import apps
        from .services import RESOURCE_MAP
        if resource_type in RESOURCE_MAP:
            app_label, model_name = RESOURCE_MAP[resource_type]
            model_cls = apps.get_model(app_label, model_name)
            try:
                obj = model_cls.objects.get(id=resource_id)
            except model_cls.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            patient = getattr(obj, 'patient', None)
            if patient is not None:
                if getattr(patient, 'primary_doctor_id', None) != user.id:
                    raise PermissionDenied("You do not have permission to revert versions for this resource.")
            elif hasattr(obj, 'primary_doctor_id'):
                if getattr(obj, 'primary_doctor_id', None) != user.id:
                    raise PermissionDenied("You do not have permission to revert versions for this resource.")
    obj = revert_to_version(resource_type, resource_id, target_version_int, user)
    return Response({"ok": True, "id": obj.pk}, status=status.HTTP_200_OK)
