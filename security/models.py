from django.db import models
import uuid

class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField(null=True, blank=True)
    path = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

class Role(models.Model):
    ADMIN = 'admin'
    DOCTOR = 'doctor'
    VIEWER = 'viewer'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (DOCTOR, 'Doctor'),
        (VIEWER, 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)