from rest_framework import serializers
from .models import MedicationOrder


class MedicationOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationOrder
        fields = ['id', 'patient', 'encounter', 'atc', 'name', 'dose', 'frequency', 'start_date', 'end_date']
        read_only_fields = ['id']