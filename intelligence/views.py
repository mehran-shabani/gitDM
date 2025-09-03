from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
import logging

from .models import AISummary, BaselineMetrics, PatternAnalysis, AnomalyDetection, PatternAlert
from .serializers import (
    AISummarySerializer,
    CreateAISummarySerializer,
    RegenerateAISummarySerializer,
    AISummaryListSerializer,
    BaselineMetricsSerializer,
    PatternAnalysisSerializer,
    AnomalyDetectionSerializer,
    PatternAlertSerializer,
    AnomalyAcknowledgeSerializer,
    PatternAlertResolveSerializer,
    PatternAnalysisRequestSerializer
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


@extend_schema_view(
    list=extend_schema(
        summary="List pattern analyses",
        description="List all pattern analyses with optional filtering by patient and pattern type"
    ),
    retrieve=extend_schema(
        summary="Get pattern analysis",
        description="Retrieve a specific pattern analysis by ID"
    )
)
class PatternAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for pattern analysis results"""
    queryset = PatternAnalysis.objects.all().select_related('patient')
    serializer_class = PatternAnalysisSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Filter by patient if specified
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        # Filter by pattern type if specified
        pattern_type = self.request.query_params.get('pattern_type')
        if pattern_type:
            queryset = queryset.filter(pattern_type=pattern_type)
        
        return queryset
    
    @extend_schema(
        summary="Request new pattern analysis",
        description="Trigger new pattern analysis for specified patient and pattern types"
    )
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Trigger new pattern analysis"""
        serializer = PatternAnalysisRequestSerializer(data=request.data)
        if serializer.is_valid():
            from .services import PatternAnalysisService, BaselineCalculationService
            
            patient_id = serializer.validated_data['patient_id']
            pattern_types = serializer.validated_data['pattern_types']
            months_back = serializer.validated_data['months_back']
            
            results = []
            
            # محاسبه baseline metrics اگر وجود نداشته باشد
            try:
                BaselineCalculationService.calculate_baseline_metrics(patient_id, months_back)
            except Exception as e:
                logger.error(f"Failed to calculate baseline metrics: {e}")
            
            # تحلیل انواع مختلف الگو
            for pattern_type in pattern_types:
                try:
                    if pattern_type == PatternAnalysis.PatternType.GLUCOSE_TREND:
                        analysis = PatternAnalysisService.analyze_glucose_trend(patient_id, months_back)
                    elif pattern_type == PatternAnalysis.PatternType.MEDICATION_ADHERENCE:
                        analysis = PatternAnalysisService.analyze_medication_adherence(patient_id, months_back)
                    else:
                        continue
                    
                    if analysis:
                        results.append(PatternAnalysisSerializer(analysis).data)
                        
                except Exception as e:
                    logger.error(f"Pattern analysis failed for {pattern_type}: {e}")
            
            return Response({
                'status': 'success',
                'analyses_created': len(results),
                'results': results
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="List anomaly detections",
        description="List all detected anomalies with optional filtering"
    ),
    retrieve=extend_schema(
        summary="Get anomaly detection",
        description="Retrieve a specific anomaly detection by ID"
    )
)
class AnomalyDetectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for anomaly detection results"""
    queryset = AnomalyDetection.objects.all().select_related('patient', 'acknowledged_by')
    serializer_class = AnomalyDetectionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on parameters"""
        queryset = super().get_queryset()
        
        # Filter by patient
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity_level=severity)
        
        # Filter by acknowledgment status
        acknowledged = self.request.query_params.get('acknowledged')
        if acknowledged is not None:
            is_acknowledged = acknowledged.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_acknowledged=is_acknowledged)
        
        return queryset
    
    @extend_schema(
        summary="Acknowledge anomaly",
        description="Mark an anomaly as acknowledged by the current user"
    )
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an anomaly"""
        anomaly = self.get_object()
        serializer = AnomalyAcknowledgeSerializer(data=request.data)
        
        if serializer.is_valid():
            from django.utils import timezone
            
            anomaly.is_acknowledged = True
            anomaly.acknowledged_by = request.user
            anomaly.acknowledged_at = timezone.now()
            anomaly.save()
            
            return Response({
                'status': 'success',
                'message': 'Anomaly acknowledged successfully'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="List pattern alerts",
        description="List all pattern-based alerts with filtering options"
    ),
    retrieve=extend_schema(
        summary="Get pattern alert",
        description="Retrieve a specific pattern alert by ID"
    )
)
class PatternAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for pattern-based alerts"""
    queryset = PatternAlert.objects.all().select_related('patient', 'resolved_by')
    serializer_class = PatternAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on parameters"""
        queryset = super().get_queryset()
        
        # Filter by patient
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by active status
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() in ['true', '1', 'yes']:
            queryset = queryset.filter(is_active=True, is_resolved=False)
        
        return queryset
    
    @extend_schema(
        summary="Resolve pattern alert",
        description="Mark a pattern alert as resolved"
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a pattern alert"""
        alert = self.get_object()
        serializer = PatternAlertResolveSerializer(data=request.data)
        
        if serializer.is_valid():
            from django.utils import timezone
            
            alert.is_resolved = True
            alert.resolved_by = request.user
            alert.resolved_at = timezone.now()
            alert.resolution_notes = serializer.validated_data['resolution_notes']
            alert.is_active = False
            alert.save()
            
            return Response({
                'status': 'success',
                'message': 'Alert resolved successfully'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="List baseline metrics",
        description="List baseline metrics for patients"
    ),
    retrieve=extend_schema(
        summary="Get baseline metrics",
        description="Retrieve baseline metrics for a specific patient"
    )
)
class BaselineMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for baseline metrics"""
    queryset = BaselineMetrics.objects.all().select_related('patient')
    serializer_class = BaselineMetricsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by patient if specified"""
        queryset = super().get_queryset()
        
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        return queryset
    
    @extend_schema(
        summary="Calculate baseline metrics",
        description="Calculate or recalculate baseline metrics for a patient"
    )
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate baseline metrics for a patient"""
        patient_id = request.data.get('patient_id')
        months_back = request.data.get('months_back', 12)
        
        if not patient_id:
            return Response({
                'error': 'patient_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .services import BaselineCalculationService
            
            baseline = BaselineCalculationService.calculate_baseline_metrics(
                patient_id=patient_id,
                months_back=months_back
            )
            
            return Response({
                'status': 'success',
                'baseline_metrics': BaselineMetricsSerializer(baseline).data
            })
            
        except Exception as e:
            logger.error(f"Baseline calculation failed: {e}")
            return Response({
                'error': f'Baseline calculation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)