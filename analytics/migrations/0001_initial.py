# Generated migration file for analytics app
# This is a placeholder - actual migration should be generated using:
# python manage.py makemigrations analytics

from django.db import migrations

class Migration(migrations.Migration):
    initial = True
    
    dependencies = [
        ('encounters', '0001_initial'),
        ('security', '0001_initial'),
        ('auth', '0001_initial'),
    ]
    
    operations = [
        # Migration operations will be auto-generated when running makemigrations
    ]