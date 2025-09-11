from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gitdm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_type', models.CharField(choices=[('HBA1C', 'HbA1c'), ('FBS', 'Fasting Blood Sugar'), ('2HPP', '2-Hour Postprandial Glucose'), ('BUN', 'Blood Urea Nitrogen'), ('CR', 'Creatinine'), ('ALT', 'Alanine Transaminase'), ('AST', 'Aspartate Transaminase'), ('ALP', 'Alkaline Phosphatase'), ('PR_URINE_24H', '24h Urine Protein'), ('EYE_EXAM', 'Eye Physical Exam'), ('EMG', 'EMG'), ('NCV', 'NCV'), ('TSH', 'Thyroid Stimulating Hormone'), ('BMI', 'Body Mass Index'), ('DIET', 'Diet/Nutrition Review'), ('OTHER', 'Other')], max_length=32)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('due_at', models.DateTimeField()),
                ('snooze_until', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('SENT', 'Sent'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=16)),
                ('priority', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('URGENT', 'Urgent')], default='MEDIUM', max_length=10)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_reminders', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='gitdm.patientprofile')),
            ],
            options={
                'ordering': ('due_at', 'id'),
            },
        ),
        migrations.AddIndex(
            model_name='reminder',
            index=models.Index(fields=['patient', 'status'], name='reminders_r_patient_65b5f9_idx'),
        ),
        migrations.AddIndex(
            model_name='reminder',
            index=models.Index(fields=['due_at'], name='reminders_r_due_at_c9dbff_idx'),
        ),
        migrations.AddIndex(
            model_name='reminder',
            index=models.Index(fields=['reminder_type'], name='reminders_r_reminde_88f226_idx'),
        ),
        migrations.AddConstraint(
            model_name='reminder',
            constraint=models.CheckConstraint(
                name='completed_requires_timestamp',
                condition=(
                    (models.Q(('status', 'COMPLETED'), ('completed_at__isnull', False)) |
                     models.Q(~models.Q(('status', 'COMPLETED')), ('completed_at__isnull', True)))
                ),
            ),
        ),
    ]

