from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
import logging

from .models import AISummary
from .serializers import (
    AISummarySerializer,
    CreateAISummarySerializer,
    RegenerateAISummarySerializer,
    AISummaryListSerializer
)
from .tasks import generate_summary_for_existing_record

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List AI summaries",
        description="List all AI summaries with optional filtering by patient"
    ),
    retrieve=extend_schema(
        summary="Get AI summary",
        description="Retrieve a specific AI summary by ID"
    ),
    create=extend_schema(
        summary="Create AI summary",
        description="Create a new AI summary using GapGPT/OpenAI"
    ),
    destroy=extend_schema(
        summary="Delete AI summary",
        description="Delete an AI summary"
    )
)
class AISummaryViewSet(viewsets.ModelViewSet):
    """ViewSet for AI summaries with GapGPT/OpenAI integration"""
    queryset = AISummary.objects.all().select_related('patient', 'content_type')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return AISummaryListSerializer
        elif self.action == 'create':
            return CreateAISummarySerializer
        return AISummarySerializer

    def get_queryset(self):
        """Filter queryset by patient if specified"""
        queryset = super().get_queryset()
        patient_id = self.request.query_params.get('patient_id')

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Create AI summary with enhanced response"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        # Handle different response types based on processing method
        if isinstance(result, dict) and 'task_id' in result:
            # Async processing
            return Response(result, status=status.HTTP_202_ACCEPTED)
        else:
            # Synchronous processing - return serialized summary
            summary_serializer = AISummarySerializer(result)
            return Response(summary_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Regenerate AI summary",
        description="Regenerate AI summary for existing record with new content",
        request=RegenerateAISummarySerializer
    )
    @action(detail=True, methods=['post'], url_path='regenerate')
    def regenerate_summary(self, request, pk=None):
        """Regenerate AI summary for existing record"""
        summary = self.get_object()
        serializer = RegenerateAISummarySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Start background task for regeneration
        task_result = generate_summary_for_existing_record.delay(
            summary_id=summary.id,
            new_content=serializer.validated_data['content'],
            context=serializer.validated_data.get('context'),
            summary_type=serializer.validated_data.get('summary_type', 'medical_record')
        )

        return Response({
            'task_id': task_result.id,
            'status': 'processing',
            'message': f'AI summary {summary.id} is being regenerated in the background'
        }, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Test AI service",
        description="Test the AI service connection and generate a simple summary"
    )
    @action(detail=False, methods=['post'], url_path='test')
    def test_ai_service(self, request):
        """Test AI service connectivity"""
        from .services import OpenAIService

        test_content = request.data.get('content', 'Test patient has diabetes and takes metformin daily.')

        try:
            ai_service = OpenAIService()
            if not ai_service.client:
                return Response({
                    'status': 'error',
                    'message': 'AI service not configured properly'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            summary = ai_service.generate_summary(test_content, summary_type='medical_record')

            return Response({
                'status': 'success',
                'api_provider': ai_service.api_provider,
                'original_content': test_content,
                'generated_summary': summary,
                'message': f'AI service is working properly using {ai_service.api_provider}'
            })

        except Exception as e:
            logger.error(f"AI service test failed: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'AI service test failed: {str(e)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @extend_schema(
        summary="Get summary statistics",
        description="Get statistics about AI summaries"
    )
    @action(detail=False, methods=['get'], url_path='stats')
    def get_statistics(self, request):
        """Get AI summary statistics"""
        from django.db.models import Count, Avg
        from django.db.models.functions import Length

        stats = {
            'total_summaries': self.get_queryset().count(),
            'summaries_by_type': list(
                self.get_queryset()
                .values('content_type__model')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
            'average_summary_length': self.get_queryset()
            .aggregate(avg_length=Avg(Length('summary')))['avg_length'],
            'total_references_linked': sum(s.references.count() for s in self.get_queryset()),
        }

        # Add patient-specific stats if patient_id provided
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            patient_summaries = self.get_queryset().filter(patient_id=patient_id)
            stats['patient_summaries'] = patient_summaries.count()
            stats['patient_summary_types'] = list(
                patient_summaries
                .values('content_type__model')
                .annotate(count=Count('id'))
            )
            stats['patient_references_linked'] = sum(s.references.count() for s in patient_summaries)

        return Response(stats)

    @extend_schema(
        summary="Test clinical references linking",
        description="Test the clinical references linking function with sample text"
    )
    @action(detail=False, methods=['post'], url_path='test-references')
    def test_references_linking(self, request):
        """Test clinical references linking"""
        from .services import link_references

        test_content = request.data.get('content', 'Patient has diabetes with elevated HbA1c. Starting metformin and insulin therapy.')
        topic_hint = request.data.get('topic_hint', 'diabetes')

        try:
            # Test reference linking
            references = link_references(test_content, topic_hint)

            return Response({
                'status': 'success',
                'test_content': test_content,
                'topic_hint': topic_hint,
                'references_found': len(references),
                'references': [
                    {
                        'title': ref.title,
                        'topic': ref.topic,
                        'id': ref.id
                    } for ref in references
                ],
                'message': f'Found {len(references)} clinical references for the given content'
            })

        except Exception as e:
            logger.error(f"Reference linking test failed: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Reference linking test failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
