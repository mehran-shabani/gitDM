from django.contrib import admin

from .models import AIDigest, HealthCheckResult, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "base_url", "health_path", "method", "timeout_s", "enabled")
    list_filter = ("enabled", "method")
    search_fields = ("name", "base_url")


@admin.register(HealthCheckResult)
class HealthCheckResultAdmin(admin.ModelAdmin):
    list_display = ("id", "service", "status_code", "ok", "latency_ms", "checked_at")
    list_filter = ("ok", "service")
    search_fields = ("service__name",)
    date_hierarchy = "checked_at"


@admin.register(AIDigest)
class AIDigestAdmin(admin.ModelAdmin):
    list_display = ("id", "service", "period_start", "period_end", "created_at")
    list_filter = ("service",)
    search_fields = ("service__name", "summary_text")
    date_hierarchy = "created_at"

