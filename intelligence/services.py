import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Avg, Count, StdDev
from .models import AISummary, BaselineMetrics, PatternAnalysis, AnomalyDetection, PatternAlert
from references.models import ClinicalReference
from laboratory.models import LabResult
from encounters.models import Encounter
from pharmacy.models import Medication
import openai
import numpy as np

logger = logging.getLogger(__name__)

TOPIC_KEYWORDS = {
    'diabetes': ['diabetes','hba1c','metformin','insulin','sglt2','glp-1'],
}

class OpenAIService:
    """Service class for AI GPT integration (supports both GapGPT and OpenAI APIs)"""

    def __init__(self):
        self.client = None
        self.api_provider = None

        # Prefer GapGPT if configured and enabled
        if settings.AI_SUMMARIZER_SETTINGS['USE_GAPGPT'] and settings.GAPGPT_API_KEY:
            try:
                self.client = openai.OpenAI(
                    base_url=settings.GAPGPT_BASE_URL,
                    api_key=settings.GAPGPT_API_KEY
                )
                self.api_provider = 'GapGPT'
                logger.info("Initialized GapGPT client")
            except Exception as e:
                logger.error(f"Failed to initialize GapGPT client: {e}")

        # Fallback to OpenAI if GapGPT not available
        if not self.client and settings.OPENAI_API_KEY:
            try:
                openai.api_key = settings.OPENAI_API_KEY
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                self.api_provider = 'OpenAI'
                logger.info("Initialized OpenAI client")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

        if not self.client:
            logger.warning("No AI client configured. Summaries will use fallback truncation.")

    def generate_summary(
        self,
        content: str,
        context: Optional[str] = None,
        summary_type: str = "medical_record"
    ) -> str:
        """
        Generate AI summary using GapGPT or OpenAI GPT

        Args:
            content: The text content to summarize
            context: Optional context about the patient or medical scenario
            summary_type: Type of summary to generate (medical_record, encounter, lab_results, etc.)

        Returns:
            Generated summary text
        """
        if not self.client:
            logger.warning("AI client not configured. Falling back to truncated content.")
            return content[:500] + "..." if len(content) > 500 else content

        try:
            # Build system prompt based on summary type
            system_prompt = self._get_system_prompt(summary_type)

            # Build user message
            user_message = f"Please summarize the following medical information:\n\n{content}"
            if context:
                user_message = f"Patient Context: {context}\n\n{user_message}"

            logger.info(f"Generating summary using {self.api_provider} with model {settings.AI_SUMMARIZER_SETTINGS['MODEL']}")

            response = self.client.chat.completions.create(
                model=settings.AI_SUMMARIZER_SETTINGS['MODEL'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=settings.AI_SUMMARIZER_SETTINGS['MAX_TOKENS'],
                temperature=settings.AI_SUMMARIZER_SETTINGS['TEMPERATURE']
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary of {len(summary)} characters for content of {len(content)} characters using {self.api_provider}")
            return summary

        except Exception as e:
            logger.error(f"Error generating {self.api_provider} summary: {str(e)}")
            # Fallback to truncated content
            return content[:500] + "..." if len(content) > 500 else content

    def _get_system_prompt(self, summary_type: str) -> str:
        """Get specialized system prompt based on summary type"""
        base_prompt = settings.AI_SUMMARIZER_SETTINGS['SYSTEM_PROMPT']

        prompts = {
            "encounter": base_prompt + " Focus on the patient encounter details, symptoms, diagnoses, and treatment plans.",
            "lab_results": base_prompt + " Focus on laboratory values, reference ranges, and clinical significance of abnormal results.",
            "medications": base_prompt + " Focus on medication changes, dosages, indications, and any noted side effects or adherence issues.",
            "medical_record": base_prompt + " Provide a comprehensive summary of all medical information provided."
        }

        return prompts.get(summary_type, base_prompt)

def link_references(summary_text: str, topic_hint: str = 'diabetes') -> List[ClinicalReference]:
    """Link clinical references based on summary content and topic"""
    qs = ClinicalReference.objects.filter(topic__icontains=topic_hint)
    selected = []
    text_lower = summary_text.lower()
    for ref in qs[:20]:
        score = 0
        for kw in TOPIC_KEYWORDS.get(topic_hint, []):
            if kw in text_lower:
                score += 1
        if score:
            selected.append(ref)
    return selected[:3]

def create_ai_summary(
    content: str,
    patient_id: int,
    content_type_id: Optional[int] = None,
    object_id: Optional[str] = None,
    context: Optional[str] = None,
    summary_type: str = "medical_record",
    topic_hint: str = "diabetes"
) -> 'AISummary':
    """
    Create an AI summary using GapGPT or OpenAI GPT

    Args:
        content: Raw content to summarize
        patient_id: Patient ID
        content_type_id: Optional ContentType ID for generic foreign key
        object_id: Optional object ID for generic foreign key
        context: Optional patient context
        summary_type: Type of summary (encounter, lab_results, etc.)
        topic_hint: Topic hint for reference linking

    Returns:
        Created AISummary instance
    """
    # Generate summary using AI service
    ai_service = OpenAIService()
    summary_text = ai_service.generate_summary(content, context, summary_type)

    # Create AISummary instance
    summary = AISummary.objects.create(
        patient_id=patient_id,
        content_type_id=content_type_id,
        object_id=object_id,
        summary=summary_text
    )

    # Link relevant clinical references
    references = link_references(summary_text, topic_hint)
    if references:
        summary.references.add(*references)
        logger.info(f"Linked {len(references)} clinical references to summary {summary.id}")
    else:
        logger.info(f"No clinical references found for summary {summary.id}")

    return summary


class BaselineCalculationService:
    """
    سرویس محاسبه معیارهای پایه برای هر بیمار
    """
    
    @staticmethod
    def calculate_baseline_metrics(patient_id: int, months_back: int = 12) -> BaselineMetrics:
        """
        محاسبه معیارهای پایه بر اساس داده‌های تاریخی
        """
        from gitdm.models import PatientProfile
        
        patient = PatientProfile.objects.get(id=patient_id)
        cutoff_date = timezone.now() - timedelta(days=months_back * 30)
        
        # محاسبه معیارهای آزمایشگاهی
        lab_data = LabResult.objects.filter(
            patient=patient,
            taken_at__gte=cutoff_date
        )
        
        # HbA1c
        hba1c_values = lab_data.filter(loinc__in=['4548-4', '17856-6']).values_list('value', flat=True)
        hba1c_stats = BaselineCalculationService._calculate_stats(list(hba1c_values))
        
        # Blood Glucose
        glucose_values = lab_data.filter(loinc__in=['2345-7', '2339-0', '1558-6']).values_list('value', flat=True)
        glucose_stats = BaselineCalculationService._calculate_stats(list(glucose_values))
        
        # محاسبه الگوهای رفتاری
        encounters_count = Encounter.objects.filter(
            patient=patient,
            occurred_at__gte=cutoff_date
        ).count()
        
        labs_count = lab_data.count()
        months_count = min(months_back, (timezone.now() - cutoff_date).days // 30)
        
        encounters_per_month = encounters_count / months_count if months_count > 0 else 0
        labs_per_month = labs_count / months_count if months_count > 0 else 0
        
        # ایجاد یا به‌روزرسانی BaselineMetrics
        baseline, created = BaselineMetrics.objects.get_or_create(
            patient=patient,
            defaults={
                'avg_hba1c': hba1c_stats['mean'],
                'std_hba1c': hba1c_stats['std'],
                'avg_blood_glucose': glucose_stats['mean'],
                'std_blood_glucose': glucose_stats['std'],
                'avg_encounters_per_month': Decimal(str(encounters_per_month)),
                'avg_labs_per_month': Decimal(str(labs_per_month)),
                'data_points_count': len(hba1c_values) + len(glucose_values)
            }
        )
        
        if not created:
            baseline.avg_hba1c = hba1c_stats['mean']
            baseline.std_hba1c = hba1c_stats['std']
            baseline.avg_blood_glucose = glucose_stats['mean']
            baseline.std_blood_glucose = glucose_stats['std']
            baseline.avg_encounters_per_month = Decimal(str(encounters_per_month))
            baseline.avg_labs_per_month = Decimal(str(labs_per_month))
            baseline.data_points_count = len(hba1c_values) + len(glucose_values)
            baseline.save()
        
        return baseline
    
    @staticmethod
    def _calculate_stats(values: List[Decimal]) -> Dict[str, Optional[Decimal]]:
        """
        محاسبه آمار پایه (میانگین و انحراف معیار)
        """
        if not values:
            return {'mean': None, 'std': None}
        
        values_float = [float(v) for v in values]
        mean = statistics.mean(values_float)
        std = statistics.stdev(values_float) if len(values_float) > 1 else 0
        
        return {
            'mean': Decimal(str(round(mean, 2))),
            'std': Decimal(str(round(std, 2)))
        }


class AnomalyDetectionService:
    """
    سرویس تشخیص ناهنجاری‌های آماری و الگویی
    """
    
    # آستانه‌های تشخیص ناهنجاری
    Z_SCORE_THRESHOLDS = {
        'LOW': 2.0,
        'MEDIUM': 2.5,
        'HIGH': 3.0,
        'CRITICAL': 3.5
    }
    
    @staticmethod
    def detect_statistical_anomalies(patient_id: int, new_value: Decimal, metric_type: str) -> Optional[AnomalyDetection]:
        """
        تشخیص ناهنجاری‌های آماری با استفاده از Z-Score
        """
        from gitdm.models import PatientProfile
        
        try:
            patient = PatientProfile.objects.get(id=patient_id)
            baseline = BaselineMetrics.objects.get(patient=patient)
        except (PatientProfile.DoesNotExist, BaselineMetrics.DoesNotExist):
            return None
        
        # انتخاب معیار مناسب
        if metric_type == 'hba1c':
            mean = baseline.avg_hba1c
            std = baseline.std_hba1c
        elif metric_type == 'glucose':
            mean = baseline.avg_blood_glucose
            std = baseline.std_blood_glucose
        else:
            return None
        
        if not mean or not std or std == 0:
            return None
        
        # محاسبه Z-Score
        z_score = abs(float(new_value - mean) / float(std))
        
        # تعیین سطح شدت
        severity = AnomalyDetectionService._determine_severity(z_score)
        
        if severity:
            return AnomalyDetection.objects.create(
                patient=patient,
                anomaly_type=AnomalyDetection.AnomalyType.STATISTICAL_OUTLIER,
                severity_level=severity,
                description=f"مقدار {metric_type} ({new_value}) به طور قابل توجهی از میانگین ({mean}) منحرف است",
                detected_value=new_value,
                expected_value=mean,
                deviation_score=Decimal(str(round(z_score, 3))),
                data_timestamp=timezone.now()
            )
        
        return None
    
    @staticmethod
    def detect_sudden_changes(patient_id: int, metric_type: str, lookback_days: int = 30) -> List[AnomalyDetection]:
        """
        تشخیص تغییرات ناگهانی در مقادیر
        """
        from gitdm.models import PatientProfile
        
        try:
            patient = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return []
        
        cutoff_date = timezone.now() - timedelta(days=lookback_days)
        
        # دریافت داده‌های اخیر
        if metric_type == 'hba1c':
            recent_data = LabResult.objects.filter(
                patient=patient,
                loinc__in=['4548-4', '17856-6'],
                taken_at__gte=cutoff_date
            ).order_by('taken_at')
        elif metric_type == 'glucose':
            recent_data = LabResult.objects.filter(
                patient=patient,
                loinc__in=['2345-7', '2339-0', '1558-6'],
                taken_at__gte=cutoff_date
            ).order_by('taken_at')
        else:
            return []
        
        if recent_data.count() < 3:
            return []
        
        values = [float(result.value) for result in recent_data]
        anomalies = []
        
        # بررسی تغییرات ناگهانی بین نقاط متوالی
        for i in range(1, len(values)):
            change_percent = abs(values[i] - values[i-1]) / values[i-1] * 100
            
            # آستانه تغییر ناگهانی (بر حسب درصد)
            if change_percent > 25:  # تغییر بیش از 25%
                severity = AnomalyDetectionService._determine_sudden_change_severity(change_percent)
                
                anomaly = AnomalyDetection.objects.create(
                    patient=patient,
                    anomaly_type=AnomalyDetection.AnomalyType.SUDDEN_CHANGE,
                    severity_level=severity,
                    description=f"تغییر ناگهانی {change_percent:.1f}% در {metric_type}",
                    detected_value=Decimal(str(values[i])),
                    expected_value=Decimal(str(values[i-1])),
                    deviation_score=Decimal(str(round(change_percent, 3))),
                    data_timestamp=list(recent_data)[i].taken_at
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    @staticmethod
    def _determine_severity(z_score: float) -> Optional[str]:
        """
        تعیین سطح شدت بر اساس Z-Score
        """
        thresholds = AnomalyDetectionService.Z_SCORE_THRESHOLDS
        
        if z_score >= thresholds['CRITICAL']:
            return AnomalyDetection.SeverityLevel.CRITICAL
        elif z_score >= thresholds['HIGH']:
            return AnomalyDetection.SeverityLevel.HIGH
        elif z_score >= thresholds['MEDIUM']:
            return AnomalyDetection.SeverityLevel.MEDIUM
        elif z_score >= thresholds['LOW']:
            return AnomalyDetection.SeverityLevel.LOW
        
        return None
    
    @staticmethod
    def _determine_sudden_change_severity(change_percent: float) -> str:
        """
        تعیین شدت تغییر ناگهانی
        """
        if change_percent >= 50:
            return AnomalyDetection.SeverityLevel.CRITICAL
        elif change_percent >= 40:
            return AnomalyDetection.SeverityLevel.HIGH
        elif change_percent >= 30:
            return AnomalyDetection.SeverityLevel.MEDIUM
        else:
            return AnomalyDetection.SeverityLevel.LOW


class PatternAnalysisService:
    """
    سرویس تحلیل الگوهای رفتاری بیمار
    """
    
    @staticmethod
    def analyze_glucose_trend(patient_id: int, months_back: int = 6) -> Optional[PatternAnalysis]:
        """
        تحلیل روند قند خون
        """
        from gitdm.models import PatientProfile
        
        try:
            patient = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return None
        
        cutoff_date = timezone.now() - timedelta(days=months_back * 30)
        
        glucose_data = LabResult.objects.filter(
            patient=patient,
            loinc__in=['2345-7', '2339-0', '1558-6'],
            taken_at__gte=cutoff_date
        ).order_by('taken_at')
        
        if glucose_data.count() < 3:
            return None
        
        values = [float(result.value) for result in glucose_data]
        timestamps = [result.taken_at for result in glucose_data]
        
        # تحلیل روند خطی
        trend_analysis = PatternAnalysisService._calculate_linear_trend(values, timestamps)
        
        # تعیین جهت روند
        if trend_analysis['slope'] > 5:  # افزایش بیش از 5 mg/dL در ماه
            trend_direction = PatternAnalysis.TrendDirection.WORSENING
        elif trend_analysis['slope'] < -5:  # کاهش بیش از 5 mg/dL در ماه
            trend_direction = PatternAnalysis.TrendDirection.IMPROVING
        elif abs(trend_analysis['slope']) < 2:  # تغییر کمتر از 2 mg/dL در ماه
            trend_direction = PatternAnalysis.TrendDirection.STABLE
        else:
            trend_direction = PatternAnalysis.TrendDirection.FLUCTUATING
        
        return PatternAnalysis.objects.create(
            patient=patient,
            pattern_type=PatternAnalysis.PatternType.GLUCOSE_TREND,
            trend_direction=trend_direction,
            analysis_result={
                'slope': trend_analysis['slope'],
                'r_squared': trend_analysis['r_squared'],
                'mean_value': trend_analysis['mean'],
                'data_points': len(values),
                'trend_description': PatternAnalysisService._get_trend_description(trend_direction, trend_analysis['slope'])
            },
            confidence_score=Decimal(str(round(trend_analysis['r_squared'], 2))),
            statistical_significance=Decimal(str(round(trend_analysis.get('p_value', 0.5), 3))),
            analysis_start_date=timestamps[0],
            analysis_end_date=timestamps[-1]
        )
    
    @staticmethod
    def analyze_medication_adherence(patient_id: int, months_back: int = 3) -> Optional[PatternAnalysis]:
        """
        تحلیل پایبندی دارویی
        """
        from gitdm.models import PatientProfile
        
        try:
            patient = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return None
        
        cutoff_date = timezone.now() - timedelta(days=months_back * 30)
        
        # بررسی نسخه‌های دارویی
        medications = Medication.objects.filter(
            patient=patient,
            created_at__gte=cutoff_date
        )
        
        if not medications.exists():
            return None
        
        # تحلیل الگوی تجویز و مصرف
        total_medications = medications.count()
        expected_encounters = total_medications * 2  # انتظار حداقل 2 ویزیت فالوآپ
        
        actual_encounters = Encounter.objects.filter(
            patient=patient,
            occurred_at__gte=cutoff_date
        ).count()
        
        adherence_score = min(actual_encounters / expected_encounters, 1.0) if expected_encounters > 0 else 0
        
        # تعیین وضعیت پایبندی
        if adherence_score >= 0.8:
            trend_direction = PatternAnalysis.TrendDirection.STABLE
        elif adherence_score >= 0.6:
            trend_direction = PatternAnalysis.TrendDirection.FLUCTUATING
        else:
            trend_direction = PatternAnalysis.TrendDirection.WORSENING
        
        return PatternAnalysis.objects.create(
            patient=patient,
            pattern_type=PatternAnalysis.PatternType.MEDICATION_ADHERENCE,
            trend_direction=trend_direction,
            analysis_result={
                'adherence_score': adherence_score,
                'total_medications': total_medications,
                'actual_encounters': actual_encounters,
                'expected_encounters': expected_encounters
            },
            confidence_score=Decimal(str(round(adherence_score, 2))),
            analysis_start_date=cutoff_date,
            analysis_end_date=timezone.now()
        )
    
    @staticmethod
    def _calculate_linear_trend(values: List[float], timestamps: List[datetime]) -> Dict[str, float]:
        """
        محاسبه روند خطی داده‌ها
        """
        if len(values) < 2:
            return {'slope': 0, 'r_squared': 0, 'mean': 0}
        
        # تبدیل timestamps به روزهای عددی
        base_date = timestamps[0]
        x_values = [(ts - base_date).days for ts in timestamps]
        
        # محاسبه رگرسیون خطی
        n = len(values)
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        # محاسبه slope و intercept
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return {'slope': 0, 'r_squared': 0, 'mean': statistics.mean(values)}
            
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        # محاسبه R-squared
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, values))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # تبدیل slope به واحد ماهانه
        monthly_slope = slope * 30
        
        return {
            'slope': monthly_slope,
            'intercept': intercept,
            'r_squared': max(0, r_squared),
            'mean': statistics.mean(values)
        }
    
    @staticmethod
    def _get_trend_description(trend_direction: str, slope: float) -> str:
        """
        تولید توضیح روند
        """
        descriptions = {
            PatternAnalysis.TrendDirection.IMPROVING: f"بهبود با نرخ {abs(slope):.1f} واحد در ماه",
            PatternAnalysis.TrendDirection.WORSENING: f"بدتر شدن با نرخ {abs(slope):.1f} واحد در ماه",
            PatternAnalysis.TrendDirection.STABLE: "وضعیت پایدار",
            PatternAnalysis.TrendDirection.FLUCTUATING: "نوسان قابل توجه"
        }
        return descriptions.get(trend_direction, "روند نامشخص")


class PatternAlertService:
    """
    سرویس ایجاد هشدارهای مبتنی بر الگو
    """
    
    @staticmethod
    def create_deterioration_alert(patient_id: int, pattern_analysis: PatternAnalysis) -> Optional[PatternAlert]:
        """
        ایجاد هشدار بدتر شدن کنترل
        """
        from gitdm.models import PatientProfile
        
        if pattern_analysis.trend_direction != PatternAnalysis.TrendDirection.WORSENING:
            return None
        
        try:
            patient = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return None
        
        # تعیین اولویت بر اساس نوع الگو و شدت
        if pattern_analysis.pattern_type == PatternAnalysis.PatternType.HBA1C_TREND:
            priority = PatternAlert.Priority.HIGH
            title = f"روند نامطلوب HbA1c در بیمار {patient.full_name}"
        elif pattern_analysis.pattern_type == PatternAnalysis.PatternType.GLUCOSE_TREND:
            priority = PatternAlert.Priority.MEDIUM
            title = f"روند نامطلوب قند خون در بیمار {patient.full_name}"
        else:
            priority = PatternAlert.Priority.LOW
            title = f"تغییر الگوی رفتاری در بیمار {patient.full_name}"
        
        message = f"""
تحلیل الگوهای رفتاری نشان می‌دهد که وضعیت بیمار در حال بدتر شدن است.

جزئیات:
- نوع الگو: {pattern_analysis.get_pattern_type_display()}
- اطمینان تحلیل: {pattern_analysis.confidence_score * 100:.1f}%
- بازه زمانی: {pattern_analysis.analysis_start_date.date()} تا {pattern_analysis.analysis_end_date.date()}

توصیه: بررسی فوری وضعیت بیمار و در نظر گیری تغییر برنامه درمانی.
        """
        
        alert = PatternAlert.objects.create(
            patient=patient,
            alert_type=PatternAlert.AlertType.DETERIORATING_CONTROL,
            priority=priority,
            title=title,
            message=message.strip(),
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        alert.related_patterns.add(pattern_analysis)
        return alert
    
    @staticmethod
    def create_adherence_alert(patient_id: int, adherence_analysis: PatternAnalysis) -> Optional[PatternAlert]:
        """
        ایجاد هشدار عدم پایبندی دارویی
        """
        from gitdm.models import PatientProfile
        
        if adherence_analysis.pattern_type != PatternAnalysis.PatternType.MEDICATION_ADHERENCE:
            return None
        
        if adherence_analysis.trend_direction == PatternAnalysis.TrendDirection.STABLE:
            return None
        
        try:
            patient = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return None
        
        adherence_score = adherence_analysis.analysis_result.get('adherence_score', 0)
        
        if adherence_score < 0.6:
            priority = PatternAlert.Priority.HIGH
            urgency = "فوری"
        elif adherence_score < 0.8:
            priority = PatternAlert.Priority.MEDIUM
            urgency = "متوسط"
        else:
            return None
        
        alert = PatternAlert.objects.create(
            patient=patient,
            alert_type=PatternAlert.AlertType.MEDICATION_NON_ADHERENCE,
            priority=priority,
            title=f"عدم پایبندی دارویی - {patient.full_name}",
            message=f"""
بیمار احتمالاً به برنامه درمانی پایبند نیست.

جزئیات:
- امتیاز پایبندی: {adherence_score * 100:.1f}%
- سطح اولویت: {urgency}
- تعداد ویزیت‌های انجام شده: {adherence_analysis.analysis_result.get('actual_encounters', 0)}
- تعداد ویزیت‌های مورد انتظار: {adherence_analysis.analysis_result.get('expected_encounters', 0)}

توصیه: تماس با بیمار و بررسی دلایل عدم پایبندی.
            """.strip(),
            expires_at=timezone.now() + timedelta(days=14)
        )
        
        alert.related_patterns.add(adherence_analysis)
        return alert