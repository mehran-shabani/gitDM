from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Max, Min, Q
from django.utils import timezone
from datetime import timedelta
from gitdm.models import PatientProfile
from encounters.models import Encounter
from laboratory.models import LabResult
from pharmacy.models import MedicationOrder
from notifications.models import Notification


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_dashboard(request):
    """
    Return comprehensive analytics dashboard data for doctors.
    """
    user = request.user
    
    # Base queryset for patients
    if user.is_superuser:
        patients_qs = PatientProfile.objects.all()
    else:
        patients_qs = PatientProfile.objects.filter(primary_doctor=user)
    
    # Time ranges
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)
    
    # Patient Statistics
    patient_stats = {
        'total_patients': patients_qs.count(),
        'new_patients_this_month': patients_qs.filter(
            created_at__gte=last_30_days
        ).count(),
        'patients_by_sex': dict(
            patients_qs.values('sex').annotate(count=Count('id'))
            .values_list('sex', 'count')
        ),
        'average_age': calculate_average_age(patients_qs),
    }
    
    # Lab Results Analytics
    lab_results_qs = LabResult.objects.filter(
        patient__in=patients_qs
    )
    
    # Calculate average HbA1c for diabetic patients
    hba1c_stats = lab_results_qs.filter(
        hba1c__isnull=False,
        taken_at__gte=last_30_days
    ).aggregate(
        avg_hba1c=Avg('hba1c'),
        min_hba1c=Min('hba1c'),
        max_hba1c=Max('hba1c'),
        count_hba1c=Count('hba1c')
    )
    
    # Calculate glucose statistics
    glucose_stats = lab_results_qs.filter(
        glucose__isnull=False,
        taken_at__gte=last_30_days
    ).aggregate(
        avg_glucose=Avg('glucose'),
        high_glucose_count=Count('id', filter=Q(glucose__gt=250)),
        low_glucose_count=Count('id', filter=Q(glucose__lt=70)),
        normal_glucose_count=Count('id', filter=Q(glucose__gte=70, glucose__lte=250))
    )
    
    lab_stats = {
        'total_lab_results': lab_results_qs.count(),
        'recent_lab_results': lab_results_qs.filter(
            taken_at__gte=last_7_days
        ).count(),
        'hba1c_stats': hba1c_stats,
        'glucose_stats': glucose_stats,
    }
    
    # Encounter Statistics
    encounters_qs = Encounter.objects.filter(
        patient__in=patients_qs
    )
    
    encounter_stats = {
        'total_encounters': encounters_qs.count(),
        'recent_encounters': encounters_qs.filter(
            occurred_at__gte=last_7_days
        ).count(),
        'encounters_by_type': dict(
            encounters_qs.values('encounter_type').annotate(count=Count('id'))
            .values_list('encounter_type', 'count')
        ),
    }
    
    # Medication Statistics
    medications_qs = MedicationOrder.objects.filter(
        patient__in=patients_qs
    )
    
    active_medications = medications_qs.filter(
        start_date__lte=now,
        end_date__gte=now
    ).count()
    
    medication_stats = {
        'total_prescriptions': medications_qs.count(),
        'active_medications': active_medications,
        'new_prescriptions_this_week': medications_qs.filter(
            created_at__gte=last_7_days
        ).count(),
    }
    
    # Critical Alerts
    critical_notifications = Notification.objects.filter(
        user=user,
        priority='CRITICAL',
        is_read=False
    ).count()
    
    # Patients needing follow-up (no encounter in last 3 months)
    three_months_ago = now - timedelta(days=90)
    patients_needing_followup = patients_qs.exclude(
        encounters__occurred_at__gte=three_months_ago
    ).distinct().count()
    
    # Risk Assessment
    high_risk_patients = identify_high_risk_patients(patients_qs, lab_results_qs)
    
    # Summary Dashboard
    dashboard_data = {
        'summary': {
            'total_patients': patient_stats['total_patients'],
            'critical_alerts': critical_notifications,
            'patients_needing_followup': patients_needing_followup,
            'high_risk_patients': high_risk_patients['count'],
        },
        'patient_stats': patient_stats,
        'lab_stats': lab_stats,
        'encounter_stats': encounter_stats,
        'medication_stats': medication_stats,
        'high_risk_details': high_risk_patients,
        'generated_at': now.isoformat(),
    }
    
    return Response(dashboard_data)


def calculate_average_age(patients_qs):
    """Calculate average age of patients."""
    ages = []
    for patient in patients_qs:
        if patient.age is not None:
            ages.append(patient.age)
    
    if ages:
        return round(sum(ages) / len(ages), 1)
    return None


def identify_high_risk_patients(patients_qs, lab_results_qs):
    """
    Identify high-risk patients based on recent lab results.
    """
    high_risk_criteria = []
    patient_ids = set()
    
    # HbA1c > 9.0 in last 3 months
    three_months_ago = timezone.now() - timedelta(days=90)
    high_hba1c = lab_results_qs.filter(
        hba1c__gt=9.0,
        taken_at__gte=three_months_ago
    ).values_list('patient_id', flat=True).distinct()
    
    patient_ids.update(high_hba1c)
    if high_hba1c:
        high_risk_criteria.append(f"{len(high_hba1c)} patients with HbA1c > 9.0%")
    
    # Frequent high glucose readings
    high_glucose_frequent = lab_results_qs.filter(
        glucose__gt=300,
        taken_at__gte=three_months_ago
    ).values('patient_id').annotate(
        high_count=Count('id')
    ).filter(high_count__gte=3).values_list('patient_id', flat=True)
    
    patient_ids.update(high_glucose_frequent)
    if high_glucose_frequent:
        high_risk_criteria.append(
            f"{len(high_glucose_frequent)} patients with frequent high glucose (>300 mg/dL)"
        )
    
    # High blood pressure
    high_bp = lab_results_qs.filter(
        Q(blood_pressure_systolic__gt=180) | Q(blood_pressure_diastolic__gt=120),
        taken_at__gte=three_months_ago
    ).values_list('patient_id', flat=True).distinct()
    
    patient_ids.update(high_bp)
    if high_bp:
        high_risk_criteria.append(
            f"{len(high_bp)} patients with critically high blood pressure"
        )
    
    return {
        'count': len(patient_ids),
        'criteria': high_risk_criteria,
        'patient_ids': list(patient_ids)[:10]  # Return first 10 for privacy
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_analytics(request, patient_id):
    """
    Return detailed analytics for a specific patient.
    """
    user = request.user
    
    # Check access permission
    try:
        if user.is_superuser:
            patient = PatientProfile.objects.get(id=patient_id)
        else:
            patient = PatientProfile.objects.get(
                id=patient_id,
                primary_doctor=user
            )
    except PatientProfile.DoesNotExist:
        return Response(
            {"detail": "Patient not found or access denied."},
            status=403
        )
    
    # Time ranges
    now = timezone.now()
    last_year = now - timedelta(days=365)
    last_6_months = now - timedelta(days=180)
    last_3_months = now - timedelta(days=90)
    
    # Lab trends
    lab_trends = {
        'glucose': get_lab_trend(patient, 'glucose', last_6_months),
        'hba1c': get_lab_trend(patient, 'hba1c', last_year),
        'cholesterol': get_lab_trend(patient, 'cholesterol', last_year),
        'blood_pressure': get_bp_trend(patient, last_6_months),
    }
    
    # Medication adherence (simplified)
    active_meds = MedicationOrder.objects.filter(
        patient=patient,
        start_date__lte=now,
        end_date__gte=now
    )
    
    # Recent encounters
    recent_encounters = Encounter.objects.filter(
        patient=patient
    ).order_by('-occurred_at')[:5].values(
        'id', 'encounter_type', 'occurred_at', 'chief_complaint'
    )
    
    # Risk factors
    risk_factors = calculate_patient_risk_factors(patient, last_3_months)
    
    analytics_data = {
        'patient': {
            'id': str(patient.id),
            'full_name': patient.full_name,
            'age': patient.age,
            'sex': patient.sex,
        },
        'lab_trends': lab_trends,
        'active_medications': active_meds.count(),
        'recent_encounters': list(recent_encounters),
        'risk_factors': risk_factors,
        'last_visit': recent_encounters[0]['occurred_at'] if recent_encounters else None,
    }
    
    return Response(analytics_data)


def get_lab_trend(patient, test_name, since_date):
    """Get trend data for a specific lab test."""
    results = LabResult.objects.filter(
        patient=patient,
        taken_at__gte=since_date
    ).exclude(**{f'{test_name}__isnull': True}).order_by('taken_at').values(
        'taken_at', test_name
    )
    
    return [{
        'date': r['taken_at'].date().isoformat(),
        'value': float(r[test_name])
    } for r in results]


def get_bp_trend(patient, since_date):
    """Get blood pressure trend data."""
    results = LabResult.objects.filter(
        patient=patient,
        taken_at__gte=since_date,
        blood_pressure_systolic__isnull=False,
        blood_pressure_diastolic__isnull=False
    ).order_by('taken_at').values(
        'taken_at', 'blood_pressure_systolic', 'blood_pressure_diastolic'
    )
    
    return [{
        'date': r['taken_at'].date().isoformat(),
        'systolic': r['blood_pressure_systolic'],
        'diastolic': r['blood_pressure_diastolic']
    } for r in results]


def calculate_patient_risk_factors(patient, since_date):
    """Calculate risk factors for a patient."""
    risk_factors = []
    
    # Get recent lab results
    recent_labs = LabResult.objects.filter(
        patient=patient,
        taken_at__gte=since_date
    ).order_by('-taken_at')
    
    if recent_labs.exists():
        latest_lab = recent_labs.first()
        
        # Check HbA1c
        if latest_lab.hba1c:
            if latest_lab.hba1c > 9.0:
                risk_factors.append({
                    'factor': 'Very High HbA1c',
                    'value': f'{latest_lab.hba1c}%',
                    'severity': 'high'
                })
            elif latest_lab.hba1c > 7.0:
                risk_factors.append({
                    'factor': 'Elevated HbA1c',
                    'value': f'{latest_lab.hba1c}%',
                    'severity': 'medium'
                })
        
        # Check blood pressure
        if latest_lab.blood_pressure_systolic and latest_lab.blood_pressure_diastolic:
            if (latest_lab.blood_pressure_systolic > 180 or 
                latest_lab.blood_pressure_diastolic > 120):
                risk_factors.append({
                    'factor': 'Hypertensive Crisis',
                    'value': f'{latest_lab.blood_pressure_systolic}/{latest_lab.blood_pressure_diastolic}',
                    'severity': 'high'
                })
            elif (latest_lab.blood_pressure_systolic > 140 or 
                  latest_lab.blood_pressure_diastolic > 90):
                risk_factors.append({
                    'factor': 'Hypertension',
                    'value': f'{latest_lab.blood_pressure_systolic}/{latest_lab.blood_pressure_diastolic}',
                    'severity': 'medium'
                })
        
        # Check cholesterol
        if latest_lab.cholesterol and latest_lab.cholesterol > 240:
            risk_factors.append({
                'factor': 'High Cholesterol',
                'value': f'{latest_lab.cholesterol} mg/dL',
                'severity': 'medium'
            })
    
    # Check age
    if patient.age and patient.age > 65:
        risk_factors.append({
            'factor': 'Advanced Age',
            'value': f'{patient.age} years',
            'severity': 'low'
        })
    
    return risk_factors