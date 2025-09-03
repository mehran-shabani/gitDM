from rest_framework import serializers
from .models import Notification, ClinicalAlert


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer برای اطلاع‌رسانی‌ها
    """
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'priority',
            'patient_id', 'resource_type', 'resource_id',
            'is_read', 'read_at', 'created_at', 'expires_at',
            'recipient_name'
        ]
        read_only_fields = ['id', 'created_at', 'read_at', 'recipient_name']


class ClinicalAlertSerializer(serializers.ModelSerializer):
    """
    Serializer برای هشدارهای بالینی
    """
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.get_full_name', read_only=True)
    
    class Meta:
        model = ClinicalAlert
        fields = [
            'id', 'alert_type', 'severity', 'trigger_value', 'threshold_value',
            'message', 'is_active', 'acknowledged_at', 'created_at',
            'patient_name', 'acknowledged_by_name'
        ]
        read_only_fields = [
            'id', 'created_at', 'acknowledged_at', 'patient_name', 'acknowledged_by_name'
        ]