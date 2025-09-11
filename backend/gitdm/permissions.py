from rest_framework import permissions
from .models import DoctorProfile


class IsDoctor(permissions.BasePermission):
    """
    Permission برای اطمینان از اینکه کاربر پزشک است
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            getattr(request.user, 'is_doctor', False)
        )


class IsDoctorAdmin(permissions.BasePermission):
    """
    Permission برای پزشکان با نقش ادمین
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not getattr(request.user, 'is_doctor', False):
            return False
        
        try:
            doctor_profile = request.user.doctor_profile
            return doctor_profile.role == DoctorProfile.DoctorRole.ADMIN
        except DoctorProfile.DoesNotExist:
            return False


class IsEndocrinologist(permissions.BasePermission):
    """
    Permission برای متخصصان غدد
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not getattr(request.user, 'is_doctor', False):
            return False
        
        try:
            doctor_profile = request.user.doctor_profile
            return doctor_profile.role in [
                DoctorProfile.DoctorRole.ENDOCRINOLOGIST,
                DoctorProfile.DoctorRole.ADMIN
            ]
        except DoctorProfile.DoesNotExist:
            return False


class CanViewAllPatients(permissions.BasePermission):
    """
    Permission برای مشاهده تمام بیماران (فقط ادمین‌ها)
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers همیشه دسترسی دارند
        if request.user.is_superuser:
            return True
            
        # بررسی نقش پزشک
        if getattr(request.user, 'is_doctor', False):
            try:
                doctor_profile = request.user.doctor_profile
                return doctor_profile.role == DoctorProfile.DoctorRole.ADMIN
            except DoctorProfile.DoesNotExist:
                return False
        
        return False


class CanModifyTreatmentPlan(permissions.BasePermission):
    """
    Permission برای تغییر برنامه درمانی (متخصصان و ادمین‌ها)
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not getattr(request.user, 'is_doctor', False):
            return False
        
        try:
            doctor_profile = request.user.doctor_profile
            return doctor_profile.role in [
                DoctorProfile.DoctorRole.ENDOCRINOLOGIST,
                DoctorProfile.DoctorRole.ADMIN
            ]
        except DoctorProfile.DoesNotExist:
            return False


class CanAccessEmergencyData(permissions.BasePermission):
    """
    Permission برای دسترسی به داده‌های اضطراری
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # همه پزشکان در شرایط اضطراری دسترسی دارند
        return getattr(request.user, 'is_doctor', False)


class IsPatientOwnerOrDoctor(permissions.BasePermission):
    """
    Permission برای اطمینان از اینکه کاربر صاحب رکورد بیمار یا پزشک مربوطه است
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # اگر کاربر خود بیمار است
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # اگر کاربر پزشک اصلی بیمار است
        if hasattr(obj, 'primary_doctor') and obj.primary_doctor == request.user:
            return True
        
        # اگر کاربر ادمین است
        if getattr(request.user, 'is_doctor', False):
            try:
                doctor_profile = request.user.doctor_profile
                return doctor_profile.role == DoctorProfile.DoctorRole.ADMIN
            except DoctorProfile.DoesNotExist:
                pass
        
        return False