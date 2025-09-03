from rest_framework import serializers
from .models import Reminder


class ReminderSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    is_due = serializers.BooleanField(read_only=True)

    class Meta:
        model = Reminder
        fields = [
            'id', 'patient', 'patient_name', 'reminder_type', 'title', 'description',
            'due_at', 'snooze_until', 'status', 'priority', 'completed_at', 'created_at',
            'is_due'
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'patient_name', 'is_due']

