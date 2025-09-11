# Generated migration file for analytics app
# This is a placeholder - actual migration should be generated using:
# python manage.py makemigrations analytics

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    
    dependencies = [
        ('gitdm', '0001_initial'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='PatientAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('avg_glucose', models.FloatField(blank=True, null=True)),
                ('avg_hba1c', models.FloatField(blank=True, null=True)),
                ('encounters_count', models.IntegerField(default=0)),
                ('lab_tests_count', models.IntegerField(default=0)),
                ('medications_count', models.IntegerField(default=0)),
                ('alerts_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='gitdm.patientprofile')),
            ],
        ),
        migrations.CreateModel(
            name='DoctorAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('total_patients', models.IntegerField(default=0)),
                ('active_patients', models.IntegerField(default=0)),
                ('total_encounters', models.IntegerField(default=0)),
                ('avg_patient_hba1c', models.FloatField(blank=True, null=True)),
                ('patients_at_goal', models.IntegerField(default=0)),
                ('patients_above_goal', models.IntegerField(default=0)),
                ('performance_score', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='gitdm.doctorprofile')),
            ],
        ),
        migrations.CreateModel(
            name='SystemAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('total_users', models.IntegerField(default=0)),
                ('active_users', models.IntegerField(default=0)),
                ('total_doctors', models.IntegerField(default=0)),
                ('total_patients', models.IntegerField(default=0)),
                ('total_encounters', models.IntegerField(default=0)),
                ('total_lab_tests', models.IntegerField(default=0)),
                ('total_medications', models.IntegerField(default=0)),
                ('total_alerts', models.IntegerField(default=0)),
                ('avg_system_hba1c', models.FloatField(blank=True, null=True)),
                ('system_goal_achievement', models.FloatField(blank=True, null=True)),
                ('daily_active_users', models.IntegerField(default=0)),
                ('api_calls', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]