from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import MedicalFile, FileAccessLog
from .serializers import (
    MedicalFileSerializer,
    MedicalFileUploadSerializer,
    FileAccessLogSerializer
)


class MedicalFileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing medical files.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return MedicalFileUploadSerializer
        return MedicalFileSerializer
    
    def get_queryset(self):
        """Return files accessible to the current user."""
        user = self.request.user
        
        if user.is_superuser:
            queryset = MedicalFile.objects.all()
        else:
            # User can see files for their patients (if they're a doctor)
            queryset = MedicalFile.objects.filter(
                Q(patient__primary_doctor=user) |
                Q(uploaded_by=user)
            ).distinct()
        
        # Filter by patient if specified
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        # Filter by file type
        file_type = self.request.query_params.get('file_type')
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        # Filter by encounter
        encounter_id = self.request.query_params.get('encounter_id')
        if encounter_id:
            queryset = queryset.filter(encounter_id=encounter_id)
        
        return queryset.select_related('patient', 'uploaded_by', 'encounter')
    
    def perform_create(self, serializer):
        """Ensure user has permission to upload for the patient."""
        patient = serializer.validated_data['patient']
        user = self.request.user
        
        # Check if user is the patient's doctor or superuser
        if not user.is_superuser and patient.primary_doctor != user:
            raise PermissionError("You don't have permission to upload files for this patient.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Log file deletion before destroying."""
        # Create access log for deletion
        self._create_access_log(instance, 'DELETE')
        
        # Delete the actual file from storage
        if instance.file:
            instance.file.delete()
        
        # Delete the database record
        instance.delete()
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a medical file with access logging."""
        medical_file = self.get_object()
        
        # Create access log
        self._create_access_log(medical_file, 'DOWNLOAD')
        
        try:
            # Return file response
            file_handle = medical_file.file.open()
            response = FileResponse(
                file_handle,
                content_type=medical_file.mime_type,
                as_attachment=True,
                filename=medical_file.title
            )
            return response
        except Exception:
            raise Http404("File not found")
    
    @action(detail=True, methods=['get'])
    def view(self, request, pk=None):
        """View a medical file inline (for images/PDFs) with access logging."""
        medical_file = self.get_object()
        
        # Create access log
        self._create_access_log(medical_file, 'VIEW')
        
        try:
            # Return file response for inline viewing
            file_handle = medical_file.file.open()
            response = FileResponse(
                file_handle,
                content_type=medical_file.mime_type,
                as_attachment=False
            )
            return response
        except Exception:
            raise Http404("File not found")
    
    @action(detail=True, methods=['get'])
    def access_logs(self, request, pk=None):
        """Get access logs for a specific file."""
        medical_file = self.get_object()
        
        # Only file owner or superuser can view access logs
        if not request.user.is_superuser and medical_file.uploaded_by != request.user:
            return Response(
                {"detail": "You don't have permission to view access logs for this file."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logs = FileAccessLog.objects.filter(medical_file=medical_file)
        serializer = FileAccessLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics about medical files."""
        queryset = self.get_queryset()
        
        stats = {
            'total_files': queryset.count(),
            'total_size': sum(f.file_size for f in queryset),
            'by_type': {}
        }
        
        # Count by file type
        for file_type, label in MedicalFile.FileType.choices:
            count = queryset.filter(file_type=file_type).count()
            if count > 0:
                stats['by_type'][label] = count
        
        # Format total size
        size = stats['total_size']
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                stats['total_size_display'] = f"{size:.1f} {unit}"
                break
            size /= 1024.0
        else:
            stats['total_size_display'] = f"{size:.1f} TB"
        
        return Response(stats)
    
    def _create_access_log(self, medical_file, access_type):
        """Create an access log entry."""
        FileAccessLog.objects.create(
            medical_file=medical_file,
            accessed_by=self.request.user,
            access_type=access_type,
            ip_address=self._get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _get_client_ip(self):
        """Get client IP address from request."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip