from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import RecordVersion
from .services import revert_to_version


# Create your views here.


@api_view(["GET"])
@permission_classes([AllowAny])
def versions_list(request, resource_type: str, resource_id: str):
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
@permission_classes([AllowAny])
def versions_revert(request, resource_type: str, resource_id: str):
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
