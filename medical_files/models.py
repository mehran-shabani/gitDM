from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import os
import uuid


def medical_file_path(instance, filename):
    """
    Generate file path for medical files.
    Format: medical_files/patient_<id>/<year>/<month>/<uuid>_<filename>
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}_{filename}"
    return os.path.join(
        'medical_files',
        f'patient_{instance.patient.id}',
        timezone.now().strftime('%Y'),
        timezone.now().strftime('%m'),
        filename
    )


class MedicalFile(models.Model):
    """
    Model for storing medical files (images, PDFs, etc.) for patients.
    """
    class FileType(models.TextChoices):
        LAB_REPORT = 'LAB_REPORT', 'Lab Report'
        XRAY = 'XRAY', 'X-Ray'
        CT_SCAN = 'CT_SCAN', 'CT Scan'
        MRI = 'MRI', 'MRI'
        ULTRASOUND = 'ULTRASOUND', 'Ultrasound'
        ECG = 'ECG', 'ECG'
        PRESCRIPTION = 'PRESCRIPTION', 'Prescription'
        MEDICAL_HISTORY = 'MEDICAL_HISTORY', 'Medical History'
        OTHER = 'OTHER', 'Other'
    
    # Relations
    patient = models.ForeignKey(
        'gitdm.PatientProfile',
        on_delete=models.CASCADE,
        related_name='medical_files'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_medical_files'
    )
    encounter = models.ForeignKey(
        'encounters.Encounter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_files',
        help_text='Optional: Link to related encounter'
    )
    
    # File information
    file = models.FileField(
        upload_to=medical_file_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'gif', 'dcm', 'dicom']
            )
        ]
    )
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER
    )
    
    # Metadata
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file_size = models.PositiveIntegerField(
        help_text='File size in bytes',
        editable=False
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        editable=False
    )
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Privacy and security
    is_sensitive = models.BooleanField(
        default=False,
        help_text='Mark if file contains sensitive information'
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['patient', 'file_type']),
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['encounter']),
        ]
    
    def __str__(self):
        return f"{self.get_file_type_display()} - {self.title} ({self.patient})"
    
    def save(self, *args, **kwargs):
        """Override save to set file size and mime type."""
        if self.file:
            self.file_size = self.file.size
            # Simple mime type detection based on extension
            ext = self.file.name.split('.')[-1].lower()
            mime_types = {
                'pdf': 'application/pdf',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'dcm': 'application/dicom',
                'dicom': 'application/dicom',
            }
            self.mime_type = mime_types.get(ext, 'application/octet-stream')
        
        super().save(*args, **kwargs)
    
    @property
    def file_size_display(self):
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class FileAccessLog(models.Model):
    """
    Log access to medical files for audit purposes.
    """
    medical_file = models.ForeignKey(
        MedicalFile,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    accessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('VIEW', 'View'),
            ('DOWNLOAD', 'Download'),
            ('UPDATE', 'Update'),
            ('DELETE', 'Delete'),
        ]
    )
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['medical_file', 'accessed_at']),
            models.Index(fields=['accessed_by', 'accessed_at']),
        ]
    
    def __str__(self):
        return f"{self.accessed_by} - {self.access_type} - {self.medical_file.title}"