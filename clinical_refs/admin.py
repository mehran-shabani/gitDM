from django.contrib import admin
from .models import ClinicalReference

@admin.register(ClinicalReference)
class ClinicalReferenceAdmin(admin.ModelAdmin):
    list_display = ("title","source","year","topic","section","lang")
    list_filter = ("source","year","topic","lang")
    search_fields = ("title","topic","section")