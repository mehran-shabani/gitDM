from celery import shared_task
from .services import create_ai_summary, link_references
from .models import AISummary
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task
def create_summary_with_references(
    patient_id,
    content,
    content_type_model=None,
    object_id=None,
    context=None,
    summary_type="medical_record",
    topic_hint="diabetes"
):
    """Create an AI summary using GapGPT/OpenAI and link relevant clinical references.

    Args:
        patient_id: ID of the patient
        content: Raw content to be summarized by AI
        content_type_model: Model name for generic foreign key (e.g., 'encounter', 'lab_result')
        object_id: ID of the specific object for generic foreign key
        context: Optional patient context for better summarization
        summary_type: Type of summary for specialized prompts ('encounter', 'lab_results', 'medications', 'medical_record')
        topic_hint: Optional topic hint for linking references (e.g., 'diabetes', 'hypertension')

    Returns:
        The ID of the created AISummary object
    """
    try:
        # Get ContentType if model name provided
        content_type_id = None
        if content_type_model:
            try:
                content_type = ContentType.objects.get(model=content_type_model.lower())
                content_type_id = content_type.id
            except ContentType.DoesNotExist:
                logger.warning(f"ContentType not found for model: {content_type_model}")

        # Create AI summary using the service
        summary = create_ai_summary(
            content=content,
            patient_id=patient_id,
            content_type_id=content_type_id,
            object_id=object_id,
            context=context,
            summary_type=summary_type,
            topic_hint=topic_hint
        )

        logger.info(f"Successfully created AI summary {summary.id} for patient {patient_id}")
        return summary.id

    except Exception as e:
        logger.error(f"Error creating AI summary for patient {patient_id}: {str(e)}")
        raise

@shared_task
def generate_summary_for_existing_record(summary_id, new_content, context=None, summary_type="medical_record"):
    """Regenerate AI summary for an existing AISummary record.

    Args:
        summary_id: ID of existing AISummary
        new_content: New content to summarize
        context: Optional patient context
        summary_type: Type of summary for specialized prompts

    Returns:
        Updated AISummary ID
    """
    try:
        from .services import OpenAIService

        summary = AISummary.objects.get(id=summary_id)
        ai_service = OpenAIService()

        # Generate new summary
        new_summary_text = ai_service.generate_summary(new_content, context, summary_type)

        # Update the summary
        summary.summary = new_summary_text
        summary.save()

        logger.info(f"Successfully regenerated AI summary {summary_id}")
        return summary.id

    except AISummary.DoesNotExist:
        logger.error(f"AISummary {summary_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error regenerating AI summary {summary_id}: {str(e)}")
        raise


@shared_task
def run_pattern_analysis_for_patient(patient_id, pattern_types=None, months_back=6):
    """
    اجرای تحلیل الگو برای یک بیمار در پس‌زمینه
    """
    try:
        from .services import PatternAnalysisService, BaselineCalculationService, PatternAlertService
        from .models import PatternAnalysis
        
        # محاسبه baseline metrics
        BaselineCalculationService.calculate_baseline_metrics(patient_id, months_back)
        
        if not pattern_types:
            pattern_types = [
                PatternAnalysis.PatternType.GLUCOSE_TREND,
                PatternAnalysis.PatternType.MEDICATION_ADHERENCE
            ]
        
        results = []
        alerts_created = []
        
        for pattern_type in pattern_types:
            try:
                analysis = None
                if pattern_type == PatternAnalysis.PatternType.GLUCOSE_TREND:
                    analysis = PatternAnalysisService.analyze_glucose_trend(patient_id, months_back)
                elif pattern_type == PatternAnalysis.PatternType.MEDICATION_ADHERENCE:
                    analysis = PatternAnalysisService.analyze_medication_adherence(patient_id, months_back)
                
                if analysis:
                    results.append(analysis.id)
                    
                    # ایجاد هشدار در صورت نیاز
                    if analysis.trend_direction == PatternAnalysis.TrendDirection.WORSENING:
                        if pattern_type == PatternAnalysis.PatternType.MEDICATION_ADHERENCE:
                            alert = PatternAlertService.create_adherence_alert(patient_id, analysis)
                        else:
                            alert = PatternAlertService.create_deterioration_alert(patient_id, analysis)
                        
                        if alert:
                            alerts_created.append(alert.id)
                
            except Exception as e:
                logger.error(f"Pattern analysis failed for {pattern_type}: {e}")
        
        logger.info(f"Pattern analysis completed for patient {patient_id}: {len(results)} analyses, {len(alerts_created)} alerts")
        return {
            'patient_id': patient_id,
            'analyses_created': results,
            'alerts_created': alerts_created
        }
        
    except Exception as e:
        logger.error(f"Pattern analysis task failed for patient {patient_id}: {e}")
        raise


@shared_task
def run_anomaly_detection_for_new_lab(lab_result_id):
    """
    اجرای تشخیص ناهنجاری برای نتیجه آزمایش جدید
    """
    try:
        from laboratory.models import LabResult
        from .services import AnomalyDetectionService
        
        lab_result = LabResult.objects.get(id=lab_result_id)
        
        # تعیین نوع metric بر اساس LOINC
        metric_type = None
        if lab_result.loinc in ['4548-4', '17856-6']:
            metric_type = 'hba1c'
        elif lab_result.loinc in ['2345-7', '2339-0', '1558-6']:
            metric_type = 'glucose'
        
        if not metric_type:
            return None
        
        # تشخیص ناهنجاری آماری
        anomaly = AnomalyDetectionService.detect_statistical_anomalies(
            patient_id=lab_result.patient.id,
            new_value=lab_result.value,
            metric_type=metric_type
        )
        
        # تشخیص تغییرات ناگهانی
        sudden_changes = AnomalyDetectionService.detect_sudden_changes(
            patient_id=lab_result.patient.id,
            metric_type=metric_type
        )
        
        anomaly_ids = []
        if anomaly:
            anomaly_ids.append(anomaly.id)
        anomaly_ids.extend([a.id for a in sudden_changes])
        
        logger.info(f"Anomaly detection completed for lab {lab_result_id}: {len(anomaly_ids)} anomalies detected")
        return {
            'lab_result_id': lab_result_id,
            'anomalies_detected': anomaly_ids
        }
        
    except Exception as e:
        logger.error(f"Anomaly detection task failed for lab {lab_result_id}: {e}")
        raise


@shared_task
def run_daily_pattern_analysis():
    """
    تحلیل روزانه الگوهای تمام بیماران فعال
    """
    try:
        from gitdm.models import PatientProfile
        
        # دریافت بیماران فعال (که در 3 ماه گذشته داده داشته‌اند)
        cutoff_date = timezone.now() - timezone.timedelta(days=90)
        
        active_patients = PatientProfile.objects.filter(
            Q(labresult__taken_at__gte=cutoff_date) |
            Q(encounter__occurred_at__gte=cutoff_date)
        ).distinct()
        
        total_processed = 0
        total_alerts = 0
        
        for patient in active_patients:
            try:
                result = run_pattern_analysis_for_patient.delay(patient.id)
                # در محیط واقعی، نتیجه را منتظر نمی‌مانیم
                total_processed += 1
            except Exception as e:
                logger.error(f"Failed to schedule pattern analysis for patient {patient.id}: {e}")
        
        logger.info(f"Daily pattern analysis scheduled for {total_processed} patients")
        return {
            'patients_processed': total_processed,
            'status': 'scheduled'
        }
        
    except Exception as e:
        logger.error(f"Daily pattern analysis task failed: {e}")
        raise