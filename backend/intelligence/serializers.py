from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import AISummary, BaselineMetrics, PatternAnalysis, AnomalyDetection, PatternAlert
from .tasks import create_summary_with_references


class AISummarySerializer(serializers.ModelSerializer):
    """Serializer for AISummary model with enhanced fields"""
    resource_type = serializers.CharField(source='content_type.model', read_only=True)
    references = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = AISummary
        fields = [
            'id', 'patient', 'content_type', 'object_id', 'resource_type',
            'summary', 'references', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'resource_type', 'references']


class CreateAISummarySerializer(serializers.Serializer):
    """Serializer for creating AI summaries with content to be processed"""
    patient_id = serializers.IntegerField()
    content = serializers.CharField(
        help_text="Raw medical content to be summarized by AI"
    )
    content_type_model = serializers.CharField(
        required=False,
        help_text="Model name for generic relation (e.g., 'encounter', 'lab_result')"
    )
    object_id = serializers.CharField(
        required=False,
        help_text="Object ID for generic relation"
    )
    context = serializers.CharField(
        required=False,
        help_text="Optional patient context for better summarization"
    )
    summary_type = serializers.ChoiceField(
        choices=[
            ('medical_record', 'Medical Record'),
            ('encounter', 'Patient Encounter'),
            ('lab_results', 'Laboratory Results'),
            ('medications', 'Medications'),
        ],
        default='medical_record',
        help_text="Type of summary for specialized AI prompts"
    )
    topic_hint = serializers.CharField(
        default='diabetes',
        help_text="Topic hint for linking clinical references"
    )
    async_processing = serializers.BooleanField(
        default=True,
        help_text="Process summary asynchronously using background task"
    )

    def create(self, validated_data):
        """Create AI summary using background task or synchronously"""
        async_processing = validated_data.pop('async_processing', True)

        if async_processing:
            # Process asynchronously using Celery task
            task_result = create_summary_with_references.delay(**validated_data)
            return {
                'task_id': task_result.id,
                'status': 'processing',
                'message': 'AI summary is being generated in the background'
            }
        else:
            # Process synchronously
            from .services import create_ai_summary

            content_type_id = None
            content_type_model = validated_data.get('content_type_model')
            if content_type_model:
                try:
                    content_type = ContentType.objects.get(model=content_type_model.lower())
                    content_type_id = content_type.id
                except ContentType.DoesNotExist:
                    pass

            summary = create_ai_summary(
                content=validated_data['content'],
                patient_id=validated_data['patient_id'],
                content_type_id=content_type_id,
                object_id=validated_data.get('object_id'),
                context=validated_data.get('context'),
                summary_type=validated_data.get('summary_type', 'medical_record'),
                topic_hint=validated_data.get('topic_hint', 'diabetes')
            )

            return summary


class RegenerateAISummarySerializer(serializers.Serializer):
    """Serializer for regenerating existing AI summaries"""
    summary_id = serializers.CharField()
    content = serializers.CharField(
        help_text="New content to summarize"
    )
    context = serializers.CharField(
        required=False,
        help_text="Optional patient context"
    )
    summary_type = serializers.ChoiceField(
        choices=[
            ('medical_record', 'Medical Record'),
            ('encounter', 'Patient Encounter'),
            ('lab_results', 'Laboratory Results'),
            ('medications', 'Medications'),
        ],
        default='medical_record'
    )

    def validate_summary_id(self, value):
        """Validate that the summary exists"""
        try:
            AISummary.objects.get(id=value)
            return value
        except AISummary.DoesNotExist:
            raise serializers.ValidationError("AI Summary not found")


class AISummaryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing AI summaries"""
    resource_type = serializers.CharField(source='content_type.model', read_only=True)
    summary_preview = serializers.SerializerMethodField()
    references_count = serializers.SerializerMethodField()

    class Meta:
        model = AISummary
        fields = [
            'id', 'patient', 'resource_type', 'summary_preview',
            'references_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'resource_type', 'references_count']

    def get_summary_preview(self, obj):
        """Return truncated summary for list views"""
        return obj.summary[:200] + "..." if len(obj.summary) > 200 else obj.summary

    def get_references_count(self, obj):
        """Return count of linked clinical references"""
        return obj.references.count()


# Simple serializer for the API gateway (backward compatibility)
class AISummarySimpleSerializer(serializers.ModelSerializer):
    resource_type = serializers.CharField(read_only=True)
    resource_id = serializers.SerializerMethodField()
    
    class Meta:
        model = AISummary
        fields = ['id', 'resource_type', 'resource_id', 'summary', 'created_at']
        read_only_fields = ['id', 'resource_type', 'resource_id', 'created_at']
    
    def get_resource_id(self, obj):
        """
        یک‌خطی: شناسهٔ منبع مرتبط با AISummary را به صورت رشته برمی‌گرداند.
        
        توضیحات:
        این متد مقدار صفت `object_id` از نمونهٔ ورودی `obj` را گرفته و آن را به رشته تبدیل می‌کند تا برای فیلد سریالایزر `resource_id` قابل استفاده باشد. تبدیل به رشته تضمین می‌کند که مقدار بازگشتی مستقل از نوع اصلی (مثلاً UUID، عدد صحیح یا مقدار None) به شکل یک مقدار متنی عرضه شود.
        
        Parameters:
            obj: نمونهٔ مدل AISummary یا هر آبجکتی که صفت `object_id` را داشته باشد.
        
        Returns:
            str: مقدار `object_id` به صورت رشته.
        """
        return str(obj.object_id)


class BaselineMetricsSerializer(serializers.ModelSerializer):
    """Serializer for BaselineMetrics model"""
    
    class Meta:
        model = BaselineMetrics
        fields = [
            'patient', 'avg_hba1c', 'avg_blood_glucose', 'avg_systolic_bp', 'avg_diastolic_bp',
            'std_hba1c', 'std_blood_glucose', 'std_systolic_bp', 'std_diastolic_bp',
            'avg_encounters_per_month', 'avg_labs_per_month', 'medication_adherence_score',
            'last_calculated', 'data_points_count'
        ]
        read_only_fields = ['last_calculated']


class PatternAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for PatternAnalysis model"""
    pattern_type_display = serializers.CharField(source='get_pattern_type_display', read_only=True)
    trend_direction_display = serializers.CharField(source='get_trend_direction_display', read_only=True)
    
    class Meta:
        model = PatternAnalysis
        fields = [
            'id', 'patient', 'pattern_type', 'pattern_type_display',
            'trend_direction', 'trend_direction_display', 'analysis_result',
            'confidence_score', 'statistical_significance',
            'analysis_start_date', 'analysis_end_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'pattern_type_display', 'trend_direction_display']


class AnomalyDetectionSerializer(serializers.ModelSerializer):
    """Serializer for AnomalyDetection model"""
    anomaly_type_display = serializers.CharField(source='get_anomaly_type_display', read_only=True)
    severity_level_display = serializers.CharField(source='get_severity_level_display', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.full_name', read_only=True)
    
    class Meta:
        model = AnomalyDetection
        fields = [
            'id', 'patient', 'anomaly_type', 'anomaly_type_display',
            'severity_level', 'severity_level_display', 'description',
            'detected_value', 'expected_value', 'deviation_score',
            'is_acknowledged', 'acknowledged_by', 'acknowledged_by_name',
            'acknowledged_at', 'detected_at', 'data_timestamp'
        ]
        read_only_fields = [
            'id', 'detected_at', 'anomaly_type_display', 
            'severity_level_display', 'acknowledged_by_name'
        ]


class PatternAlertSerializer(serializers.ModelSerializer):
    """Serializer for PatternAlert model"""
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.full_name', read_only=True)
    related_patterns_count = serializers.SerializerMethodField()
    related_anomalies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PatternAlert
        fields = [
            'id', 'patient', 'alert_type', 'alert_type_display',
            'priority', 'priority_display', 'title', 'message',
            'related_patterns_count', 'related_anomalies_count',
            'is_active', 'is_resolved', 'resolved_by', 'resolved_by_name',
            'resolved_at', 'resolution_notes', 'created_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'alert_type_display', 'priority_display',
            'resolved_by_name', 'related_patterns_count', 'related_anomalies_count'
        ]
    
    def get_related_patterns_count(self, obj):
        return obj.related_patterns.count()
    
    def get_related_anomalies_count(self, obj):
        return obj.related_anomalies.count()


class AnomalyAcknowledgeSerializer(serializers.Serializer):
    """Serializer for acknowledging anomalies"""
    notes = serializers.CharField(required=False, help_text="Optional notes about the acknowledgment")


class PatternAlertResolveSerializer(serializers.Serializer):
    """Serializer for resolving pattern alerts"""
    resolution_notes = serializers.CharField(help_text="Notes about how the alert was resolved")


class PatternAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for requesting pattern analysis"""
    patient_id = serializers.IntegerField()
    pattern_types = serializers.MultipleChoiceField(
        choices=PatternAnalysis.PatternType.choices,
        help_text="Types of patterns to analyze"
    )
    months_back = serializers.IntegerField(
        default=6,
        min_value=1,
        max_value=24,
        help_text="Number of months of historical data to analyze"
    )