from __future__ import annotations

import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if not password:
            raise ValueError("Password must be provided")
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        return self._create_user(email=email, password=password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Single user model. A user may be a doctor, a patient, or both.
    """
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=32, blank=True)

    # Role flags (flexible: a user can have either or both)
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["date_joined"]),
            models.Index(fields=["is_doctor", "is_patient"]),
        ]

    def __str__(self) -> str:
        return self.full_name or self.email

    def get_full_name(self) -> str:
        return self.full_name or self.email

    def get_short_name(self) -> str:
        return (self.full_name.split()[0] if self.full_name else self.email.split("@")[0])


class DoctorProfile(models.Model):
    """
    Extra fields for doctors (optional; exists only if user.is_doctor=True).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
    )
    medical_code = models.CharField(max_length=32, blank=True, db_index=True)
    specialty = models.CharField(max_length=120, blank=True)

    class Meta:
        verbose_name = "Doctor Profile"
        verbose_name_plural = "Doctor Profiles"
        indexes = [
            models.Index(fields=["medical_code"]),
            models.Index(fields=["specialty"]),
        ]

    def __str__(self) -> str:
        return f"Dr. {self.user.get_full_name()}"

    def clean(self):
        if not getattr(self.user, "is_doctor", False):
            raise ValidationError("Connected user must have is_doctor=True for DoctorProfile.")


class PatientProfile(models.Model):
    """
    Extra fields for patients (optional; exists only if user.is_patient=True).
    """
    class Sex(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
        null=True,
        blank=True,
    )

    full_name = models.CharField(max_length=120, blank=True, default="")

    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, choices=Sex.choices, null=True, blank=True)

    # Assign primary doctor by referencing User (limited to is_doctor=True)
    primary_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="patients",
        null=True,
        blank=True,
        limit_choices_to=Q(is_doctor=True),
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Patient Profile"
        verbose_name_plural = "Patient Profiles"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["national_id"]),
        ]

    def __str__(self) -> str:
        if self.full_name:
            return self.full_name
        if self.user:
            return self.user.get_full_name() or self.user.email
        return "Patient"

    @property
    def age(self):
        if self.dob:
            today = timezone.now().date()
            return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return None

    def clean(self):
        # Patient’s user must actually be a patient
        if self.user and not getattr(self.user, "is_patient", False):
            raise ValidationError("Connected user must have is_patient=True for PatientProfile.")
        # Primary doctor consistency
        if self.primary_doctor:
            if not getattr(self.primary_doctor, "is_doctor", False):
                raise ValidationError("primary_doctor must be a user with is_doctor=True.")
            if self.user_id and self.primary_doctor_id == self.user_id:
                raise ValidationError("A patient cannot assign themselves as their doctor.")