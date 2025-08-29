from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import AISummary
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
            from django.contrib.contenttypes.models import ContentType

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
    summary_id = serializers.UUIDField()
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
