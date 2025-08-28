from django.contrib import admin
from .models import Encounter


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ('patient', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('patient__full_name',)
    readonly_fields = ('id', 'created_at', 'updated_at')