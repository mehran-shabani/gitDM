from rest_framework import serializers
from .models import ClinicalReference


class ClinicalReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalReference
        fields = ['id', 'title', 'source', 'year', 'url', 'topic']
        read_only_fields = ['id']