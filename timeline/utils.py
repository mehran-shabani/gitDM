from django.utils import timezone
from datetime import timedelta
from typing import Dict, List, Any
from .models import MedicalTimeline, TestReminder


class TimelineAnalyzer:
    """
    کلاس تحلیل تایم‌لاین برای استخراج الگوها و بینش‌های پزشکی
    """
    
    @staticmethod
    def analyze_lab_trends(patient, test_type: str, months_back: int = 6) -> Dict[str, Any]:
        """
        تحلیل روند آزمایشات در طول زمان
        """
        start_date = timezone.now() - timedelta(days=30 * months_back)
        
        lab_events = MedicalTimeline.objects.filter(
            patient=patient,
            event_type=MedicalTimeline.EventType.LAB_RESULT,
            occurred_at__gte=start_date
        ).order_by('occurred_at')
        
        # فیلتر بر اساس نوع آزمایش
        test_mapping = {
            'HBA1C': ['4548-4', '17856-6'],
            'FBS': ['2345-7', '2339-0'],
            'BUN': ['3094-0'],
            'CR': ['2160-0']
        }
        
        target_loincs = test_mapping.get(test_type, [])
        if target_loincs:
            lab_events = lab_events.filter(
                metadata__loinc__in=target_loincs
            )
        
        # استخراج داده‌ها
        data_points = []
        for event in lab_events:
            try:
                value = float(event.metadata.get('value', 0))
                data_points.append({
                    'date': event.occurred_at,
                    'value': value,
                    'unit': event.metadata.get('unit', ''),
                    'severity': event.severity
                })
            except (ValueError, TypeError):
                continue
        
        if not data_points:
            return {'trend': 'insufficient_data', 'data_points': []}
        
        # تحلیل روند
        values = [point['value'] for point in data_points]
        if len(values) >= 2:
            trend = 'improving' if values[-1] < values[0] else 'worsening' if values[-1] > values[0] else 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'trend': trend,
            'data_points': data_points,
            'latest_value': values[-1] if values else None,
            'average_value': sum(values) / len(values) if values else None,
            'improvement_percentage': ((values[0] - values[-1]) / values[0] * 100) if len(values) >= 2 and values[0] != 0 else 0
        }
    
    @staticmethod
    def get_compliance_score(patient) -> Dict[str, Any]:
        """
        محاسبه امتیاز پایبندی بیمار به برنامه درمانی
        """
        # یادآورهای فعال
        active_reminders = TestReminder.objects.filter(
            patient=patient,
            is_active=True
        )
        
        if not active_reminders.exists():
            return {'score': 0, 'message': 'یادآوری فعال وجود ندارد'}
        
        # محاسبه امتیاز
        total_reminders = active_reminders.count()
        overdue_count = sum(1 for r in active_reminders if r.is_overdue())
        on_time_count = total_reminders - overdue_count
        
        compliance_score = (on_time_count / total_reminders) * 100 if total_reminders > 0 else 0
        
        # تعیین سطح پایبندی
        if compliance_score >= 90:
            level = 'عالی'
            color = 'success'
        elif compliance_score >= 70:
            level = 'خوب'
            color = 'warning'
        elif compliance_score >= 50:
            level = 'متوسط'
            color = 'info'
        else:
            level = 'ضعیف'
            color = 'danger'
        
        return {
            'score': round(compliance_score, 1),
            'level': level,
            'color': color,
            'total_reminders': total_reminders,
            'overdue_count': overdue_count,
            'on_time_count': on_time_count
        }
    
    @staticmethod
    def get_critical_alerts(patient, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        دریافت هشدارهای بحرانی اخیر
        """
        start_date = timezone.now() - timedelta(days=days_back)
        
        critical_events = MedicalTimeline.objects.filter(
            patient=patient,
            severity=MedicalTimeline.Severity.CRITICAL,
            occurred_at__gte=start_date,
            is_visible=True
        ).order_by('-occurred_at')
        
        alerts = []
        for event in critical_events:
            alerts.append({
                'title': event.title,
                'description': event.description,
                'occurred_at': event.occurred_at,
                'event_type': event.get_event_type_display(),
                'metadata': event.metadata
            })
        
        return alerts


class ReminderOptimizer:
    """
    کلاس بهینه‌سازی یادآورها بر اساس الگوهای رفتاری بیمار
    """
    
    @staticmethod
    def optimize_reminder_schedule(patient):
        """
        بهینه‌سازی زمان‌بندی یادآورها بر اساس تاریخچه انجام آزمایشات
        """
        reminders = TestReminder.objects.filter(
            patient=patient,
            is_active=True
        )
        
        optimizations = []
        
        for reminder in reminders:
            # تحلیل الگوی انجام آزمایشات
            lab_events = MedicalTimeline.objects.filter(
                patient=patient,
                event_type=MedicalTimeline.EventType.LAB_RESULT,
                metadata__loinc__isnull=False
            ).order_by('-occurred_at')[:10]  # ۱۰ آزمایش اخیر
            
            # محاسبه میانگین تأخیر
            delays = []
            for event in lab_events:
                # پیدا کردن یادآوری مربوطه در زمان آزمایش
                # این محاسبه ساده‌سازی شده است
                if reminder.test_type == 'HBA1C' and event.metadata.get('loinc') in ['4548-4', '17856-6']:
                    # محاسبه تأخیر نسبت به سررسید
                    pass
            
            # پیشنهاد بهینه‌سازی
            if reminder.is_overdue():
                optimizations.append({
                    'reminder_id': reminder.id,
                    'test_type': reminder.get_test_type_display(),
                    'current_frequency': reminder.get_frequency_display(),
                    'suggested_action': 'افزایش فرکانس یادآوری',
                    'reason': 'عقب‌افتادگی مکرر'
                })
        
        return optimizations
    
    @staticmethod
    def suggest_new_reminders(patient):
        """
        پیشنهاد یادآورهای جدید بر اساس تاریخچه پزشکی
        """
        suggestions = []
        
        # بررسی آخرین نتایج آزمایش
        recent_labs = MedicalTimeline.objects.filter(
            patient=patient,
            event_type=MedicalTimeline.EventType.LAB_RESULT,
            occurred_at__gte=timezone.now() - timedelta(days=90)
        )
        
        # اگر HbA1c بالا باشد، پیشنهاد معاینه چشم
        hba1c_events = recent_labs.filter(metadata__loinc__in=['4548-4', '17856-6'])
        for event in hba1c_events:
            try:
                value = float(event.metadata.get('value', 0))
                if value > 8:  # HbA1c بالای ۸٪
                    # بررسی وجود یادآوری معاینه چشم
                    eye_reminder_exists = TestReminder.objects.filter(
                        patient=patient,
                        test_type='EYE_EXAM',
                        is_active=True
                    ).exists()
                    
                    if not eye_reminder_exists:
                        suggestions.append({
                            'test_type': 'EYE_EXAM',
                            'reason': f'HbA1c بالا ({value}%) - ریسک عوارض چشمی',
                            'priority': 'HIGH',
                            'suggested_frequency': 'BIANNUALLY'
                        })
            except (ValueError, TypeError):
                continue
        
        return suggestions


def export_timeline_to_pdf(patient, start_date=None, end_date=None):
    """
    تولید فایل PDF از تایم‌لاین بیمار
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from io import BytesIO
    
    # آماده‌سازی داده‌ها
    timeline_events = TimelineService.get_patient_timeline(
        patient, start_date, end_date
    )
    
    # ایجاد PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # عنوان
    title = Paragraph(
        f"تایم‌لاین پزشکی - {patient.full_name}",
        styles['Title']
    )
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # اطلاعات بیمار
    patient_info = f"""
    نام: {patient.full_name}<br/>
    سن: {patient.age} سال<br/>
    تاریخ تولید گزارش: {timezone.now().strftime('%Y/%m/%d %H:%M')}
    """
    story.append(Paragraph(patient_info, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # جدول رویدادها
    data = [['تاریخ', 'نوع رویداد', 'عنوان', 'توضیحات', 'شدت']]
    
    for event in timeline_events:
        data.append([
            event.occurred_at.strftime('%Y/%m/%d'),
            event.get_event_type_display(),
            event.title,
            event.description[:50] + '...' if len(event.description) > 50 else event.description,
            event.get_severity_display()
        ])
    
    table = Table(data)
    story.append(table)
    
    # ساخت PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer


class TimelineDataExporter:
    """
    کلاس صادرات داده‌های تایم‌لاین به فرمت‌های مختلف
    """
    
    @staticmethod
    def export_to_csv(patient, start_date=None, end_date=None):
        """صادرات تایم‌لاین به فرمت CSV"""
        import csv
        from io import StringIO
        
        timeline_events = TimelineService.get_patient_timeline(
            patient, start_date, end_date
        )
        
        output = StringIO()
        writer = csv.writer(output)
        
        # هدر
        writer.writerow([
            'تاریخ', 'نوع رویداد', 'عنوان', 'توضیحات', 
            'شدت', 'ایجادکننده', 'متادیتا'
        ])
        
        # داده‌ها
        for event in timeline_events:
            writer.writerow([
                event.occurred_at.strftime('%Y-%m-%d %H:%M'),
                event.get_event_type_display(),
                event.title,
                event.description,
                event.get_severity_display(),
                event.created_by.full_name if event.created_by else '',
                str(event.metadata)
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_to_json(patient, start_date=None, end_date=None):
        """صادرات تایم‌لاین به فرمت JSON"""
        import json
        from timeline.serializers import MedicalTimelineSerializer
        
        timeline_events = TimelineService.get_patient_timeline(
            patient, start_date, end_date
        )
        
        serializer = MedicalTimelineSerializer(timeline_events, many=True)
        
        export_data = {
            'patient': {
                'id': patient.id,
                'name': patient.full_name,
                'age': patient.age
            },
            'export_date': timezone.now().isoformat(),
            'date_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'timeline_events': serializer.data
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)


def calculate_health_score(patient) -> Dict[str, Any]:
    """
    محاسبه امتیاز کلی سلامت بر اساس تایم‌لاین
    """
    # آخرین نتایج آزمایش
    recent_labs = MedicalTimeline.objects.filter(
        patient=patient,
        event_type=MedicalTimeline.EventType.LAB_RESULT,
        occurred_at__gte=timezone.now() - timedelta(days=90)
    )
    
    score_components = {}
    total_weight = 0
    weighted_score = 0
    
    # امتیاز HbA1c
    hba1c_events = recent_labs.filter(metadata__loinc__in=['4548-4', '17856-6']).first()
    if hba1c_events:
        try:
            hba1c_value = float(hba1c_events.metadata.get('value', 0))
            if hba1c_value <= 7:
                hba1c_score = 100
            elif hba1c_value <= 8:
                hba1c_score = 80
            elif hba1c_value <= 9:
                hba1c_score = 60
            else:
                hba1c_score = 40
            
            score_components['hba1c'] = {
                'score': hba1c_score,
                'value': hba1c_value,
                'weight': 0.4
            }
            weighted_score += hba1c_score * 0.4
            total_weight += 0.4
        except (ValueError, TypeError):
            pass
    
    # امتیاز پایبندی به یادآورها
    compliance = TimelineAnalyzer.analyze_compliance(patient)
    if compliance:
        score_components['compliance'] = {
            'score': compliance['score'],
            'weight': 0.3
        }
        weighted_score += compliance['score'] * 0.3
        total_weight += 0.3
    
    # امتیاز کلی
    overall_score = weighted_score / total_weight if total_weight > 0 else 0
    
    return {
        'overall_score': round(overall_score, 1),
        'components': score_components,
        'last_updated': timezone.now().isoformat()
    }


def get_next_appointment_suggestions(patient) -> List[Dict[str, Any]]:
    """
    پیشنهادات برای قرار ملاقات بعدی بر اساس تایم‌لاین
    """
    suggestions = []
    
    # بررسی یادآورهای عقب‌افتاده
    overdue_reminders = TestReminder.objects.filter(
        patient=patient,
        next_due__lt=timezone.now(),
        is_active=True
    )
    
    if overdue_reminders.exists():
        suggestions.append({
            'type': 'urgent_tests',
            'message': f'{overdue_reminders.count()} آزمایش عقب‌افتاده نیاز به انجام فوری دارد',
            'priority': 'HIGH',
            'tests': [r.get_test_type_display() for r in overdue_reminders]
        })
    
    # بررسی آخرین مواجهه
    last_encounter = MedicalTimeline.objects.filter(
        patient=patient,
        event_type=MedicalTimeline.EventType.ENCOUNTER
    ).order_by('-occurred_at').first()
    
    if last_encounter:
        days_since_last = (timezone.now() - last_encounter.occurred_at).days
        if days_since_last > 90:  # بیش از ۳ ماه
            suggestions.append({
                'type': 'routine_checkup',
                'message': f'آخرین ویزیت {days_since_last} روز پیش بوده، ویزیت دوره‌ای توصیه می‌شود',
                'priority': 'MEDIUM'
            })
    
    return suggestions