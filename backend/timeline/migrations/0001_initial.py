# Generated migration for timeline app

from django.conf import settings
import django.contrib.contenttypes.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gitdm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimelineEventCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('color', models.CharField(default='#007bff', max_length=7)),
                ('icon', models.CharField(blank=True, max_length=50)),
            ],
            options={
                'verbose_name': 'Timeline Event Category',
                'verbose_name_plural': 'Timeline Event Categories',
            },
        ),
        migrations.CreateModel(
            name='ReminderTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_type', models.CharField(choices=[('HBA1C', 'HbA1c (هموگلوبین گلیکوزیله)'), ('FBS', 'قند ناشتا (Fasting Blood Sugar)'), ('2HPP', 'قند ۲ ساعت بعد از غذا (2-Hour Post-Prandial)'), ('BUN', 'اوره خون (Blood Urea Nitrogen)'), ('CR', 'کراتینین (Creatinine)'), ('ALT', 'آلانین آمینوترانسفراز'), ('AST', 'آسپارتات آمینوترانسفراز'), ('ALP', 'آلکالین فسفاتاز'), ('TSH', 'هورمون محرک تیروئید'), ('PR_URINE_24', 'پروتئین ادرار ۲۴ ساعته'), ('EYE_EXAM', 'معاینه چشم'), ('EMG', 'الکترومایوگرافی'), ('NCV', 'سرعت رسانش عصبی'), ('BMI', 'شاخص توده بدنی'), ('BP', 'فشار خون'), ('DIET', 'مشاوره تغذیه'), ('EXERCISE', 'برنامه ورزشی')], max_length=20, unique=True)),
                ('default_frequency', models.CharField(choices=[('WEEKLY', 'هفتگی'), ('MONTHLY', 'ماهانه'), ('QUARTERLY', 'سه‌ماهه'), ('BIANNUALLY', 'شش‌ماهه'), ('ANNUALLY', 'سالانه'), ('CUSTOM', 'سفارشی')], max_length=15)),
                ('default_priority', models.CharField(choices=[('LOW', 'پایین'), ('MEDIUM', 'متوسط'), ('HIGH', 'بالا'), ('URGENT', 'فوری')], default='MEDIUM', max_length=10)),
                ('default_reminder_days', models.PositiveIntegerField(default=7)),
                ('instructions', models.TextField(blank=True)),
                ('preparation_notes', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Reminder Template',
                'verbose_name_plural': 'Reminder Templates',
            },
        ),
        migrations.CreateModel(
            name='TestReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_type', models.CharField(choices=[('HBA1C', 'HbA1c (هموگلوبین گلیکوزیله)'), ('FBS', 'قند ناشتا (Fasting Blood Sugar)'), ('2HPP', 'قند ۲ ساعت بعد از غذا (2-Hour Post-Prandial)'), ('BUN', 'اوره خون (Blood Urea Nitrogen)'), ('CR', 'کراتینین (Creatinine)'), ('ALT', 'آلانین آمینوترانسفراز'), ('AST', 'آسپارتات آمینوترانسفراز'), ('ALP', 'آلکالین فسفاتاز'), ('TSH', 'هورمون محرک تیروئید'), ('PR_URINE_24', 'پروتئین ادرار ۲۴ ساعته'), ('EYE_EXAM', 'معاینه چشم'), ('EMG', 'الکترومایوگرافی'), ('NCV', 'سرعت رسانش عصبی'), ('BMI', 'شاخص توده بدنی'), ('BP', 'فشار خون'), ('DIET', 'مشاوره تغذیه'), ('EXERCISE', 'برنامه ورزشی')], max_length=20)),
                ('frequency', models.CharField(choices=[('WEEKLY', 'هفتگی'), ('MONTHLY', 'ماهانه'), ('QUARTERLY', 'سه‌ماهه'), ('BIANNUALLY', 'شش‌ماهه'), ('ANNUALLY', 'سالانه'), ('CUSTOM', 'سفارشی')], max_length=15)),
                ('priority', models.CharField(choices=[('LOW', 'پایین'), ('MEDIUM', 'متوسط'), ('HIGH', 'بالا'), ('URGENT', 'فوری')], default='MEDIUM', max_length=10)),
                ('last_performed', models.DateTimeField(blank=True, null=True)),
                ('next_due', models.DateTimeField()),
                ('reminder_days_before', models.PositiveIntegerField(default=7)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('custom_interval_days', models.PositiveIntegerField(blank=True, help_text='فاصله سفارشی به روز (فقط برای نوع CUSTOM)', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_reminders', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_reminders', to='gitdm.patientprofile')),
            ],
            options={
                'verbose_name': 'Test Reminder',
                'verbose_name_plural': 'Test Reminders',
                'ordering': ['next_due'],
            },
        ),
        migrations.CreateModel(
            name='PatientTimelinePreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('show_lab_results', models.BooleanField(default=True)),
                ('show_medications', models.BooleanField(default=True)),
                ('show_encounters', models.BooleanField(default=True)),
                ('show_alerts', models.BooleanField(default=True)),
                ('show_reminders', models.BooleanField(default=True)),
                ('enable_email_reminders', models.BooleanField(default=True)),
                ('enable_sms_reminders', models.BooleanField(default=False)),
                ('default_timeline_range_days', models.PositiveIntegerField(default=365)),
                ('patient', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='timeline_preferences', to='gitdm.patientprofile')),
            ],
            options={
                'verbose_name': 'Patient Timeline Preference',
                'verbose_name_plural': 'Patient Timeline Preferences',
            },
        ),
        migrations.CreateModel(
            name='MedicalTimeline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('event_type', models.CharField(choices=[('ENCOUNTER', 'مواجهه بالینی'), ('LAB_RESULT', 'نتیجه آزمایش'), ('MEDICATION', 'دارو'), ('PHYSICAL_EXAM', 'معاینه فیزیکی'), ('DIAGNOSTIC_TEST', 'تست تشخیصی'), ('PROCEDURE', 'اقدام درمانی'), ('DIET_PLAN', 'برنامه غذایی'), ('EXERCISE', 'ورزش'), ('ALERT', 'هشدار بالینی'), ('REMINDER', 'یادآوری')], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('occurred_at', models.DateTimeField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('severity', models.CharField(choices=[('LOW', 'پایین'), ('NORMAL', 'عادی'), ('HIGH', 'بالا'), ('CRITICAL', 'بحرانی')], default='NORMAL', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_visible', models.BooleanField(default=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_timeline_events', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timeline_events', to='gitdm.patientprofile')),
            ],
            options={
                'verbose_name': 'Medical Timeline Event',
                'verbose_name_plural': 'Medical Timeline Events',
                'ordering': ['-occurred_at'],
            },
        ),
        migrations.CreateModel(
            name='MedicalTimelineNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField()),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('timeline_event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='timeline.medicaltimeline')),
            ],
            options={
                'ordering': ['-added_at'],
            },
        ),
        migrations.AddIndex(
            model_name='testreminder',
            index=models.Index(fields=['patient', 'test_type'], name='timeline_te_patient_5a9c63_idx'),
        ),
        migrations.AddIndex(
            model_name='testreminder',
            index=models.Index(fields=['next_due', 'is_active'], name='timeline_te_next_du_4f8a21_idx'),
        ),
        migrations.AddIndex(
            model_name='testreminder',
            index=models.Index(fields=['test_type', 'frequency'], name='timeline_te_test_ty_7c4b89_idx'),
        ),
        migrations.AddIndex(
            model_name='testreminder',
            index=models.Index(fields=['priority', 'next_due'], name='timeline_te_priorit_f2d1a8_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='testreminder',
            unique_together={('patient', 'test_type')},
        ),
        migrations.AddIndex(
            model_name='medicaltimeline',
            index=models.Index(fields=['patient', 'occurred_at'], name='timeline_me_patient_b8f2c1_idx'),
        ),
        migrations.AddIndex(
            model_name='medicaltimeline',
            index=models.Index(fields=['event_type', 'occurred_at'], name='timeline_me_event_t_a9d3e4_idx'),
        ),
        migrations.AddIndex(
            model_name='medicaltimeline',
            index=models.Index(fields=['severity', 'occurred_at'], name='timeline_me_severit_c5f7b2_idx'),
        ),
        migrations.AddIndex(
            model_name='medicaltimeline',
            index=models.Index(fields=['patient', 'event_type', 'occurred_at'], name='timeline_me_patient_1a2b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='medicaltimeline',
            index=models.Index(fields=['content_type', 'object_id'], name='timeline_me_content_d4e5f6_idx'),
        ),
    ]