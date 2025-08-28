from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user,'role') and request.user.role.role=='admin'

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user,'role') and request.user.role.role=='doctor'