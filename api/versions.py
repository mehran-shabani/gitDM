import logging
from typing import Any
from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.core.exceptions import ObjectDoesNotExist
from records_versioning.models import RecordVersion
from records_versioning.services import revert_to_version, RESOURCE_MAP

logger = logging.getLogger(__name__)


class RecordVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordVersion
        fields = ("version", "prev_version", "changed_at", "diff", "meta")


class VersionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RecordVersionSerializer

    def list(self, request: Request, resource_type: str | None = None, 
            resource_id: str | None = None) -> Response:
        """
        List versions for a specific resource.
        
        Filters RecordVersion by resource_type and resource_id,
        orders by version ascending, and returns paginated results.
        """
        qs = RecordVersion.objects.filter(
            resource_type=resource_type, 
            resource_id=resource_id
        ).order_by('version')
        
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    class _RevertSerializer(serializers.Serializer):
        target_version = serializers.IntegerField(min_value=1)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def revert(self, request: Request, resource_type: str | None = None, 
              resource_id: str | None = None) -> Response:
        """
        Revert a resource to a specific version.
        
        Expects resource_type and resource_id in URL parameters,
        and target_version in request body. Creates a new version
        representing the revert operation.
        """
        if not resource_type or not resource_id:
            return Response(
                {"error": "Missing required URL parameters: resource_type and resource_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate resource_type against whitelist
        if resource_type not in RESOURCE_MAP:
            return Response(
                {"error": "Invalid resource_type"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ser = self._RevertSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target_version = ser.validated_data["target_version"]
        
        try:
            revert_to_version(resource_type, resource_id, target_version, request.user)
            return Response(
                {"status": "ok", "reverted_to": target_version}, 
                status=status.HTTP_200_OK
            )
        except ObjectDoesNotExist as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            logger.exception(
                "revert failed",
                extra={
                    "resource_type": resource_type, 
                    "resource_id": str(resource_id),
                    "user_id": getattr(request.user, "pk", None),
                },
            )
            return Response(
                {"error": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )