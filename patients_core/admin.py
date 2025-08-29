from django.contrib import admin
from .models import User, Patient

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "is_active", "is_staff", "date_joined")
    list_filter  = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "full_name")
    ordering = ("-date_joined",)
    # اجازه نده از ادمین یوزر جدید ساخته بشه (پسورد مشکل می‌شود)
    def has_add_permission(self, request):
        return False
    # پسورد را قابل ویرایش نکن
    readonly_fields = ("date_joined",)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "primary_doctor", "sex", "created_at")
    list_filter = ("sex", "created_at")
    search_fields = ("full_name", "national_id")
    autocomplete_fields = ("primary_doctor",)
