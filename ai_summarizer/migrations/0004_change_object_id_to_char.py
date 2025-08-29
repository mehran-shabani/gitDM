from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_summarizer', '0003_rename_content_to_summary'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aisummary',
            name='object_id',
            field=models.CharField(max_length=64, null=True),
        ),
    ]

