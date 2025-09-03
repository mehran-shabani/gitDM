from rest_framework import serializers
from .models import PatientAnalytics, DoctorAnalytics, SystemAnalytics, Report
from encounters.models import Patient
from security.models import DoctorProfile


class PatientAnalyticsSerializer(serializers.ModelSerializer):
    """سریالایزر برای آمارهای بیمار"""
    
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    glucose_in_range_percentage = serializers.SerializerMethodField()
    hba1c_status = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientAnalytics
        fields = [
            'id', 'patient', 'patient_name', 'date',
            'avg_glucose', 'min_glucose', 'max_glucose', 'glucose_std_dev',
            'glucose_trend', 'glucose_in_range_percentage',
            'avg_hba1c', 'hba1c_trend', 'hba1c_status',
            'avg_systolic', 'avg_diastolic',
            'encounters_count', 'medications_count', 'lab_tests_count',
            'alerts_count', 'compliance_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_glucose_in_range_percentage(self, obj):
        """محاسبه درصد قندهای در محدوده نرمال"""
        if not obj.avg_glucose:
            return None
        
        # محدوده نرمال: 70-180 mg/dL
        if 70 <= obj.avg_glucose <= 180:
            return 100
        elif obj.avg_glucose < 70:
            return max(0, (obj.avg_glucose / 70) * 100)
        else:
            return max(0, (180 / obj.avg_glucose) * 100)
    
    def get_hba1c_status(self, obj):
        """تعیین وضعیت HbA1c"""
        if not obj.avg_hba1c:
            return 'unknown'
        
        if obj.avg_hba1c < 7:
            return 'excellent'
        elif obj.avg_hba1c < 8:
            return 'good'
        elif obj.avg_hba1c < 9:
            return 'fair'
        else:
            return 'poor'


class DoctorAnalyticsSerializer(serializers.ModelSerializer):
    """سریالایزر برای آمارهای پزشک"""
    
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    goal_achievement_rate = serializers.SerializerMethodField()
    alert_response_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorAnalytics
        fields = [
            'id', 'doctor', 'doctor_name', 'date',
            'total_patients', 'active_patients', 'new_patients',
            'total_encounters', 'avg_encounters_per_patient',
            'avg_patient_hba1c', 'patients_at_goal', 'patients_above_goal',
            'goal_achievement_rate',
            'total_alerts', 'critical_alerts', 'alert_response_rate',
            'performance_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_goal_achievement_rate(self, obj):
        """محاسبه نرخ دستیابی به اهداف درمانی"""
        if obj.total_patients == 0:
            return 0
        return round((obj.patients_at_goal / obj.total_patients) * 100, 2)
    
    def get_alert_response_rate(self, obj):
        """محاسبه نرخ پاسخ به هشدارها"""
        # این باید از داده‌های واقعی محاسبه شود
        # فعلاً یک مقدار نمونه برمی‌گردانیم
        return 85.5


class SystemAnalyticsSerializer(serializers.ModelSerializer):
    """سریالایزر برای آمارهای سیستم"""
    
    user_engagement_rate = serializers.SerializerMethodField()
    data_completeness_score = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemAnalytics
        fields = [
            'id', 'date',
            'total_users', 'active_users', 'total_doctors', 'total_patients',
            'user_engagement_rate',
            'total_encounters', 'total_lab_tests', 'total_medications', 'total_alerts',
            'avg_system_hba1c', 'system_goal_achievement',
            'data_completeness_score',
            'daily_active_users', 'api_calls',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_user_engagement_rate(self, obj):
        """محاسبه نرخ درگیری کاربران"""
        if obj.total_users == 0:
            return 0
        return round((obj.active_users / obj.total_users) * 100, 2)
    
    def get_data_completeness_score(self, obj):
        """محاسبه امتیاز کامل بودن داده‌ها"""
        # این باید بر اساس معیارهای مختلف محاسبه شود
        # فعلاً یک مقدار نمونه برمی‌گردانیم
        return 78.3


class ChartDataSerializer(serializers.Serializer):
    """سریالایزر برای داده‌های نمودار"""
    
    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField(child=serializers.DictField())
    chart_type = serializers.ChoiceField(choices=['line', 'bar', 'pie', 'doughnut', 'radar'])
    options = serializers.DictField(required=False)


class TrendAnalysisSerializer(serializers.Serializer):
    """سریالایزر برای تحلیل روند"""
    
    metric = serializers.CharField()
    current_value = serializers.FloatField()
    previous_value = serializers.FloatField(allow_null=True)
    change_percentage = serializers.FloatField()
    trend = serializers.ChoiceField(choices=['up', 'down', 'stable'])
    forecast = serializers.DictField(required=False)


class ReportSerializer(serializers.ModelSerializer):
    """سریالایزر برای گزارش‌ها"""
    
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_type', 'format', 'status',
            'requested_by', 'requested_by_name',
            'start_date', 'end_date',
            'patient', 'patient_name',
            'doctor', 'doctor_name',
            'file_path', 'error_message', 'metadata',
            'created_at', 'completed_at', 'duration'
        ]
        read_only_fields = ['file_path', 'error_message', 'created_at', 'completed_at']
    
    def get_duration(self, obj):
        """محاسبه مدت زمان تولید گزارش"""
        if obj.completed_at and obj.created_at:
            duration = obj.completed_at - obj.created_at
            return duration.total_seconds()
        return None


class ReportRequestSerializer(serializers.Serializer):
    """سریالایزر برای درخواست گزارش"""
    
    report_type = serializers.ChoiceField(choices=[
        ('patient_summary', 'خلاصه بیمار'),
        ('doctor_performance', 'عملکرد پزشک'),
        ('system_overview', 'نمای کلی سیستم'),
        ('custom', 'سفارشی'),
    ])
    format = serializers.ChoiceField(choices=['pdf', 'excel', 'csv'], default='pdf')
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    patient_id = serializers.IntegerField(required=False)
    doctor_id = serializers.IntegerField(required=False)
    include_charts = serializers.BooleanField(default=True)
    include_detailed_data = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """اعتبارسنجی داده‌های گزارش"""
        if attrs.get('start_date') and attrs.get('end_date'):
            if attrs['start_date'] > attrs['end_date']:
                raise serializers.ValidationError(
                    "تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد"
                )
        
        # برای گزارش خلاصه بیمار، patient_id الزامی است
        if attrs.get('report_type') == 'patient_summary' and not attrs.get('patient_id'):
            raise serializers.ValidationError(
                "برای گزارش خلاصه بیمار، انتخاب بیمار الزامی است"
            )
        
        # برای گزارش عملکرد پزشک، doctor_id الزامی است
        if attrs.get('report_type') == 'doctor_performance' and not attrs.get('doctor_id'):
            raise serializers.ValidationError(
                "برای گزارش عملکرد پزشک، انتخاب پزشک الزامی است"
            )
        
        return attrs


class DashboardSummarySerializer(serializers.Serializer):
    """سریالایزر برای خلاصه داشبورد"""
    
    # آمار کلی
    total_patients = serializers.IntegerField()
    active_patients = serializers.IntegerField()
    total_encounters_today = serializers.IntegerField()
    pending_alerts = serializers.IntegerField()
    
    # میانگین‌ها
    avg_hba1c = serializers.FloatField()
    avg_glucose = serializers.FloatField()
    
    # روندها
    patient_trend = TrendAnalysisSerializer()
    hba1c_trend = TrendAnalysisSerializer()
    glucose_trend = TrendAnalysisSerializer()
    
    # توزیع‌ها
    hba1c_distribution = serializers.DictField()
    alert_distribution = serializers.DictField()
    
    # عملکرد
    goal_achievement_rate = serializers.FloatField()
    compliance_rate = serializers.FloatField()