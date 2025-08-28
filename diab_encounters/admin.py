from django.contrib import admin
from .models import Encounter

@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ('patient', 'occurred_at', 'created_at')
    list_filter = ('occurred_at', 'created_at')
    search_fields = ('patient__full_name', 'subjective')
    readonly_fields = ('id', 'created_at')