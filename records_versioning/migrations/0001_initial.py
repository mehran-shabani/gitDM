# Generated migration for records_versioning

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RecordVersion',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('resource_type', models.CharField(max_length=48)),
                ('resource_id', models.UUIDField()),
                ('version', models.PositiveIntegerField()),
                ('prev_version', models.PositiveIntegerField(blank=True, null=True)),
                ('snapshot', models.JSONField()),
                ('diff', models.JSONField(blank=True, null=True)),
                ('meta', models.JSONField(blank=True, default=dict)),
                ('changed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
             options={
-                'indexes': [
-                    models.Index(fields=['resource_type', 'resource_id', 'version'], name='records_ver_resourc_8e8f5f_idx'),
-                    models.Index(fields=['changed_at'], name='records_ver_changed_f3e8f5_idx'),
-                ],
                'indexes': [
                    models.Index(fields=['changed_at'], name='records_ver_changed_f3e8f5_idx'),
                ],
                'unique_together': {('resource_type', 'resource_id', 'version')},
             },
        ),
    ]