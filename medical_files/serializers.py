from rest_framework import serializers
from .models import MedicalFile, FileAccessLog
from django.core.files.base import ContentFile
import base64


class MedicalFileSerializer(serializers.ModelSerializer):
    """Serializer for MedicalFile model."""
    file_size_display = serializers.ReadOnlyField()
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.get_full_name',
        read_only=True
    )
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalFile
        fields = [
            'id', 'patient', 'title', 'description', 'file_type',
            'file', 'file_url', 'file_size', 'file_size_display',
            'mime_type', 'uploaded_by', 'uploaded_by_name',
            'encounter', 'is_sensitive', 'uploaded_at', 'updated_at'
        ]
        read_only_fields = [
            'file_size', 'mime_type', 'uploaded_at', 'updated_at',
            'uploaded_by'
        ]
    
    def get_file_url(self, obj):
        """Get full URL for file."""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def create(self, validated_data):
        """Set uploaded_by to current user."""
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class MedicalFileUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading medical files with base64 support."""
    file_base64 = serializers.CharField(
        write_only=True,
        required=False,
        help_text='Base64 encoded file content'
    )
    file_name = serializers.CharField(
        write_only=True,
        required=False,
        help_text='Original filename when using base64 upload'
    )
    
    class Meta:
        model = MedicalFile
        fields = [
            'patient', 'title', 'description', 'file_type',
            'file', 'file_base64', 'file_name', 'encounter',
            'is_sensitive'
        ]
    
    def validate(self, attrs):
        """Ensure either file or file_base64 is provided."""
        if not attrs.get('file') and not attrs.get('file_base64'):
            raise serializers.ValidationError(
                "Either 'file' or 'file_base64' must be provided."
            )
        return attrs
    
    def create(self, validated_data):
        """Handle base64 file upload if provided."""
        file_base64 = validated_data.pop('file_base64', None)
        file_name = validated_data.pop('file_name', 'upload.bin')
        
        if file_base64:
            # Decode base64 and create file
            try:
                file_data = base64.b64decode(file_base64)
                validated_data['file'] = ContentFile(file_data, name=file_name)
            except Exception as e:
                raise serializers.ValidationError(
                    f"Invalid base64 file data: {str(e)}"
                )
        
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class FileAccessLogSerializer(serializers.ModelSerializer):
    """Serializer for FileAccessLog model."""
    accessed_by_name = serializers.CharField(
        source='accessed_by.get_full_name',
        read_only=True
    )
    file_title = serializers.CharField(
        source='medical_file.title',
        read_only=True
    )
    
    class Meta:
        model = FileAccessLog
        fields = [
            'id', 'medical_file', 'file_title', 'accessed_by',
            'accessed_by_name', 'access_type', 'accessed_at',
            'ip_address', 'user_agent'
        ]
        read_only_fields = ['accessed_at']