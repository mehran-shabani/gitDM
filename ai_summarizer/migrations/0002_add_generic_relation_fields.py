from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('ai_summarizer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='aisummary',
            name='content_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='aisummary',
            name='object_id',
            field=models.PositiveBigIntegerField(null=True),
        ),
    ]
