import logging
from typing import Any, ClassVar, Sequence, Type
from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticated, BasePermission, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ObjectDoesNotExist
from records_versioning.models import RecordVersion
from records_versioning.services import revert_to_version, RESOURCE_MAP

logger = logging.getLogger(__name__)


class RecordVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordVersion
        fields = ("version", "prev_version", "changed_at", "diff", "meta")


class VersionViewSet(viewsets.GenericViewSet):
    # Allow anonymous read-only access for listing versions
    permission_classes: ClassVar[Sequence[Type[BasePermission]]] = [AllowAny]
    serializer_class = RecordVersionSerializer
    pagination_class = PageNumberPagination

    def list(self, request: Request, resource_type: str, resource_id: Any) -> Response:
        """
        Returns a list of versions for a specific resource.
        Filters RecordVersion records by resource_type and resource_id,
        orders them by 'version' ascending, and returns a paginated HTTP response.
        """
        qs = RecordVersion.objects.filter(
            resource_type=resource_type, resource_id=str(resource_id)
        ).order_by('version')
        
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    class _RevertSerializer(serializers.Serializer):
        target_version = serializers.IntegerField(min_value=1)

    @action(detail=False, methods=['post'], url_path='revert')
    def revert(self, request: Request, resource_type: str, resource_id: Any) -> Response:
        """
        Processes a request to revert a specific resource to a historical version.
        """
        if not resource_type or not resource_id:
            return Response(
                {"error": "Missing required URL parameters: resource_type and resource_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self._RevertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_version = serializer.validated_data["target_version"]

        if resource_type not in RESOURCE_MAP:
            return Response({"error": "invalid resource_type"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            revert_to_version(resource_type, resource_id, target_version, request.user)
            return Response({"status": "ok", "reverted_to": target_version}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception(
                "revert failed",
                extra={
                    "resource_type": resource_type,
                    "resource_id": str(resource_id),
                    "user_id": getattr(request.user, "pk", None),
                },
            )
            return Response({"error": "internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
