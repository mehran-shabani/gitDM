from django.db.models import QuerySet
from rest_framework.exceptions import PermissionDenied


class OwnedByCurrentDoctorQuerysetMixin:
    """
    Scope queryset to records owned by current doctor via patient.primary_doctor.

    Assumes model has a FK field named `patient` pointing to an object with
    `primary_doctor` attribute. Superusers are exempt.
    """

    def get_queryset(self) -> QuerySet:  # type: ignore[override]
        base_qs: QuerySet = super().get_queryset()  # type: ignore[misc]
        user = getattr(self.request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return base_qs.none()
        if getattr(user, "is_superuser", False):
            return base_qs
        # The related lookup path patient__primary_doctor matches models in this project
        return base_qs.filter(patient__primary_doctor=user)

    def enforce_patient_ownership(self, serializer, msg: str | None = None) -> None:
        """Raise PermissionDenied if serializer.patient is not owned by current user."""
        patient = serializer.validated_data.get("patient")
        if patient is not None and getattr(patient, "primary_doctor", None) != self.request.user:
            raise PermissionDenied(msg or "You do not have permission to modify records for this patient.")

