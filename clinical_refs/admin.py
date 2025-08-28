from django.contrib import admin
from .models import ClinicalReference


@admin.register(ClinicalReference)
class ClinicalReferenceAdmin(admin.ModelAdmin):
    list_display = ('topic', 'source', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('topic', 'content', 'source')
    readonly_fields = ('id', 'created_at', 'updated_at')