from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_summarizer', '0002_add_generic_relation_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='aisummary',
            old_name='content',
            new_name='summary',
        ),
    ]

