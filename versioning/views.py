from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist

from .models import RecordVersion
from .services import revert_to_version


def check_user_access(user, resource_type, resource_id):
    """
    Check if user has access to the specified resource.
    Returns True if user has access, False otherwise.
    """
    if user.is_superuser:
        return True
    
    # Map resource types to their models and access rules
    resource_access_rules = {
        'patientprofile': {
            'model': 'gitdm.PatientProfile',
            'access_field': 'primary_doctor'
        },
        'encounter': {
            'model': 'encounters.Encounter',
            'access_through': 'patient__primary_doctor'
        },
        'labresult': {
            'model': 'laboratory.LabResult',
            'access_through': 'patient__primary_doctor'
        },
        'medicationorder': {
            'model': 'pharmacy.MedicationOrder',
            'access_through': 'patient__primary_doctor'
        },
        'aisummary': {
            'model': 'intelligence.AISummary',
            'access_through': 'patient__primary_doctor'
        }
    }
    
    resource_type_lower = resource_type.lower()
    
    if resource_type_lower not in resource_access_rules:
        return False
    
    rule = resource_access_rules[resource_type_lower]
    
    try:
        model = apps.get_model(rule['model'])
        obj = model.objects.get(pk=resource_id)
        
        if 'access_field' in rule:
            # Direct access check
            return getattr(obj, rule['access_field']) == user
        elif 'access_through' in rule:
            # Access through related field
            fields = rule['access_through'].split('__')
            current_obj = obj
            for field in fields[:-1]:
                current_obj = getattr(current_obj, field)
            return getattr(current_obj, fields[-1]) == user
            
    except (ObjectDoesNotExist, AttributeError):
        return False
    
    return False


# Create your views here.


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def versions_list(request, resource_type: str, resource_id: str):
    # Check user access to the resource
    if not check_user_access(request.user, resource_type, resource_id):
        return Response({"detail": "You do not have permission to view versions of this resource."}, 
                       status=status.HTTP_403_FORBIDDEN)
    
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
    # Check user access to the resource
    if not check_user_access(request.user, resource_type, resource_id):
        return Response({"detail": "You do not have permission to revert this resource."}, 
                       status=status.HTTP_403_FORBIDDEN)
    
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
