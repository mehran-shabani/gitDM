from django.contrib import admin
from .models import ClinicalReference


@admin.register(ClinicalReference)
class ClinicalReferenceAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'year', 'topic')
    list_filter = ('year', 'topic', 'source')
    search_fields = ('title', 'source', 'topic', 'url')
    readonly_fields = ('id',)

