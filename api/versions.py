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
        
        # Validate input
        if not resource_type or not resource_id:
            return Response(
                {"error": "Missing required fields: resource_type and resource_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_version = int(request.data.get('target_version'))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid or missing 'target_version'"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user from authenticated request, not from request body
        user = request.user if request.user.is_authenticated else None
        
        try:
            revert_to_version(resource_type, resource_id, target_version, user)
            return Response({"status":"ok","reverted_to": target_version}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)