from rest_framework import serializers
from .models import Reminder


class ReminderSerializer(serializers.ModelSerializer):
    # Replace the direct CharField with a SerializerMethodField to handle empty names
    patient_name = serializers.SerializerMethodField(read_only=True)

    def get_patient_name(self, obj):
        # Use full_name if available, otherwise fall back to the model’s __str__
        return obj.patient.full_name or str(obj.patient)
    is_due = serializers.BooleanField(read_only=True)

    class Meta:
        model = Reminder
        fields = [
            'id', 'patient', 'patient_name', 'reminder_type', 'title', 'description',
            'due_at', 'snooze_until', 'status', 'priority', 'completed_at', 'created_at',
            'is_due'
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'patient_name', 'is_due']

