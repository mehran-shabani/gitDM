from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.http import HttpRequest
from typing import Any
from .models import Role

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        """
        بررسی می‌کند که کاربر درخواست‌دهنده نقش (role) برابر با 'admin' دارد یا خیر.
        
        این متد برای استفاده در کلاس‌های اجازه (DRF Permission) طراحی شده و مقدار True بازمی‌گرداند اگر:
        - شیء request دارای صفت `user` باشد و
        - آن `user` دارای صفت `role` باشد و
        - مقدار رشته‌ای `request.user.role.role` برابر `'admin'` باشد.
        
        در غیر این صورت False برمی‌گرداند.
        
        Parameters:
            request: شیء HTTP request (برای دسترسی به request.user).
            view: نمای (view) فعلی — در این متد استفاده‌ای از آن نمی‌شود اما توسط واسط DRF ارسال می‌شود.
        
        Returns:
            bool: True در صورت داشتن نقش ادمین، در غیر این صورت False.
        
        Notes:
            اگر `request.user.role` موجود باشد اما برابر None یا شی‌ای بدون صفت `role` باشد، دسترسی به `request.user.role.role` ممکن است AttributeError تولید کند.
        """
        role_obj = getattr(request.user, 'role', None)
        return getattr(role_obj, 'role', None) == Role.ADMIN

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        """
        بررسی می‌کند که کاربر درخواست‌دهنده نقش (role) برابر با 'doctor' دارد.
        
        تابع یک مقدار بولی بازمی‌گرداند: True اگر شیء request.user دارای صفت `role` بوده و مقدار `request.user.role.role` دقیقاً برابر رشته `'doctor'` باشد، در غیر این صورت False. این تابع برای استفاده در مجوزهای DRF طراحی شده تا دسترسی را فقط به کاربران با نقش دکتر اجازه دهد.
        """
        role_obj = getattr(request.user, 'role', None)
        return getattr(role_obj, 'role', None) == Role.DOCTOR


class IsOwnerDoctorOrReadOnly(BasePermission):
    """
    Write access only if the requesting user is the patient's primary_doctor.

    - Read-only methods (GET, HEAD, OPTIONS): allowed for authenticated users; actual
      queryset scoping should be handled in the view's get_queryset.
    - Write methods (POST, PUT, PATCH, DELETE): allowed only when the object has a
      `patient` attribute whose `primary_doctor` equals `request.user`.
    """

    def has_permission(self, request: HttpRequest, view: Any) -> bool:  # type: ignore[override]
        # Base gate is handled by default IsAuthenticated in settings; allow here.
        # For POST without object, object-level check happens in has_object_permission.
        return True

    def has_object_permission(self, request: HttpRequest, view: Any, obj: Any) -> bool:  # type: ignore[override]
        if request.method in SAFE_METHODS:
            return True
        patient = getattr(obj, "patient", None)
        if patient is None:
            return False
        primary_doctor = getattr(patient, "primary_doctor", None)
        return primary_doctor == getattr(request, "user", None)