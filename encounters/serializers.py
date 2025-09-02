from rest_framework import serializers

from .models import Encounter


class EncounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encounter
        fields = ['id', 'patient', 'occurred_at', 'subjective', 'objective', 'assessment', 'plan', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_at', 'created_by']
