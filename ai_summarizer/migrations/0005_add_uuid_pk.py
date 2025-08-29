from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('ai_summarizer', '0004_change_object_id_to_char'),
    ]

    operations = [
        migrations.AddField(
            model_name='aisummary',
            name='id',
            field=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False),
        ),
    ]

