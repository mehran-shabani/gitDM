# Generated manually for fixing user_id field type and adding indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0007_auditlog_action_auditlog_new_values_auditlog_notes_and_more'),
    ]

    operations = [
        # Change user_id from UUIDField to BigIntegerField
        migrations.AlterField(
            model_name='auditlog',
            name='user_id',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        # Add database indexes for better performance
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['created_at', 'action'], name='security_auditlog_created_action_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['resource_type', 'resource_id'], name='security_auditlog_resource_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['patient_id', 'created_at'], name='security_auditlog_patient_created_idx'),
        ),
    ]