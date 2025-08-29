from rest_framework import serializers
from .models import AISummary


class AISummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = AISummary
        fields = ['id', 'patient', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']