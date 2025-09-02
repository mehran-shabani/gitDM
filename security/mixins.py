from typing import Any
from django.db.models import QuerySet


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

