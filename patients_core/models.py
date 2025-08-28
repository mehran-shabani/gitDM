from django.db import models
import uuid


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=120)
    dob = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, null=True, blank=True)
    primary_doctor_id = models.UUIDField()  # doctor مالک
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name