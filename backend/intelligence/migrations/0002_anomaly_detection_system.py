# Generated manually for anomaly detection system

from django.db import migrations, models
import django.db.models.deletion
import django.contrib.contenttypes.fields


class Migration(migrations.Migration):

    dependencies = [
        ('intelligence', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('gitdm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaselineMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avg_hba1c', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('avg_blood_glucose', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('avg_systolic_bp', models.IntegerField(blank=True, null=True)),
                ('avg_diastolic_bp', models.IntegerField(blank=True, null=True)),
                ('std_hba1c', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('std_blood_glucose', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('std_systolic_bp', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('std_diastolic_bp', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('avg_encounters_per_month', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('avg_labs_per_month', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('medication_adherence_score', models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True)),
                ('last_calculated', models.DateTimeField(auto_now=True)),
                ('data_points_count', models.IntegerField(default=0)),
                ('patient', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='gitdm.patientprofile')),
            ],
            options={
                'verbose_name': 'Baseline Metrics',
                'verbose_name_plural': 'Baseline Metrics',
            },
        ),
        migrations.CreateModel(
            name='PatternAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pattern_type', models.CharField(choices=[('GLUCOSE_TREND', 'روند قند خون'), ('HBA1C_TREND', 'روند HbA1c'), ('BP_TREND', 'روند فشار خون'), ('MED_ADHERENCE', 'پایبندی دارویی'), ('VISIT_FREQ', 'فراوانی ویزیت'), ('LAB_FREQ', 'فراوانی آزمایش')], max_length=20)),
                ('trend_direction', models.CharField(choices=[('IMPROVING', 'بهبود'), ('STABLE', 'پایدار'), ('WORSENING', 'بدتر شدن'), ('FLUCTUATING', 'نوسان')], max_length=15)),
                ('analysis_result', models.JSONField(default=dict)),
                ('confidence_score', models.DecimalField(decimal_places=2, max_digits=3)),
                ('statistical_significance', models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True)),
                ('analysis_start_date', models.DateTimeField()),
                ('analysis_end_date', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gitdm.patientprofile')),
            ],
            options={
                'verbose_name': 'Pattern Analysis',
                'verbose_name_plural': 'Pattern Analyses',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AnomalyDetection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('anomaly_type', models.CharField(choices=[('OUTLIER', 'نقطه پرت آماری'), ('SUDDEN_CHANGE', 'تغییر ناگهانی'), ('TREND_REVERSAL', 'معکوس شدن روند'), ('MISSING_DATA', 'داده گمشده'), ('MED_SKIP', 'عدم مصرف دارو'), ('UNUSUAL_PATTERN', 'الگوی غیرعادی')], max_length=20)),
                ('severity_level', models.CharField(choices=[('LOW', 'کم'), ('MEDIUM', 'متوسط'), ('HIGH', 'بالا'), ('CRITICAL', 'بحرانی')], max_length=10)),
                ('description', models.TextField()),
                ('detected_value', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('expected_value', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('deviation_score', models.DecimalField(decimal_places=3, max_digits=5)),
                ('object_id', models.CharField(blank=True, max_length=64, null=True)),
                ('is_acknowledged', models.BooleanField(default=False)),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True)),
                ('detected_at', models.DateTimeField(auto_now_add=True)),
                ('data_timestamp', models.DateTimeField()),
                ('acknowledged_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acknowledged_anomalies', to='gitdm.user')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gitdm.patientprofile')),
            ],
            options={
                'verbose_name': 'Anomaly Detection',
                'verbose_name_plural': 'Anomaly Detections',
                'ordering': ['-detected_at'],
            },
        ),
        migrations.CreateModel(
            name='PatternAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_type', models.CharField(choices=[('DETERIORATING', 'بدتر شدن کنترل'), ('NON_ADHERENCE', 'عدم پایبندی دارویی'), ('MISSED_APPT', 'عدم حضور در ویزیت'), ('UNUSUAL_LAB', 'الگوی غیرعادی آزمایش'), ('EMERGENCY', 'الگوی اورژانسی')], max_length=20)),
                ('priority', models.CharField(choices=[('LOW', 'کم'), ('MEDIUM', 'متوسط'), ('HIGH', 'بالا'), ('URGENT', 'فوری')], max_length=10)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('is_resolved', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('resolution_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gitdm.patientprofile')),
                ('related_anomalies', models.ManyToManyField(blank=True, to='intelligence.anomalydetection')),
                ('related_patterns', models.ManyToManyField(blank=True, to='intelligence.patternanalysis')),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_alerts', to='gitdm.user')),
            ],
            options={
                'verbose_name': 'Pattern Alert',
                'verbose_name_plural': 'Pattern Alerts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='baselinemetrics',
            index=models.Index(fields=['patient'], name='intelligenc_patient_8c5e4e_idx'),
        ),
        migrations.AddIndex(
            model_name='baselinemetrics',
            index=models.Index(fields=['last_calculated'], name='intelligenc_last_ca_8c5e4e_idx'),
        ),
        migrations.AddIndex(
            model_name='patternanalysis',
            index=models.Index(fields=['patient', 'pattern_type'], name='intelligenc_patient_8c5e4f_idx'),
        ),
        migrations.AddIndex(
            model_name='patternanalysis',
            index=models.Index(fields=['created_at'], name='intelligenc_created_8c5e4f_idx'),
        ),
        migrations.AddIndex(
            model_name='patternanalysis',
            index=models.Index(fields=['trend_direction'], name='intelligenc_trend_d_8c5e4f_idx'),
        ),
        migrations.AddIndex(
            model_name='anomalydetection',
            index=models.Index(fields=['patient', 'severity_level'], name='intelligenc_patient_8c5e50_idx'),
        ),
        migrations.AddIndex(
            model_name='anomalydetection',
            index=models.Index(fields=['anomaly_type', 'detected_at'], name='intelligenc_anomaly_8c5e50_idx'),
        ),
        migrations.AddIndex(
            model_name='anomalydetection',
            index=models.Index(fields=['is_acknowledged'], name='intelligenc_is_ackn_8c5e50_idx'),
        ),
        migrations.AddIndex(
            model_name='anomalydetection',
            index=models.Index(fields=['data_timestamp'], name='intelligenc_data_ti_8c5e50_idx'),
        ),
        migrations.AddIndex(
            model_name='patternalert',
            index=models.Index(fields=['patient', 'priority'], name='intelligenc_patient_8c5e51_idx'),
        ),
        migrations.AddIndex(
            model_name='patternalert',
            index=models.Index(fields=['alert_type', 'is_active'], name='intelligenc_alert_t_8c5e51_idx'),
        ),
        migrations.AddIndex(
            model_name='patternalert',
            index=models.Index(fields=['created_at'], name='intelligenc_created_8c5e51_idx'),
        ),
        migrations.AddIndex(
            model_name='patternalert',
            index=models.Index(fields=['is_resolved'], name='intelligenc_is_reso_8c5e51_idx'),
        ),
    ]