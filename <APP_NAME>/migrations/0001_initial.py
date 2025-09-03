from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Service",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, unique=True)),
                ("base_url", models.URLField(max_length=500)),
                ("health_path", models.CharField(max_length=255)),
                ("method", models.CharField(default="GET", max_length=10)),
                ("headers", models.JSONField(blank=True, default=dict)),
                ("timeout_s", models.PositiveIntegerField(default=5)),
                ("enabled", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="HealthCheckResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status_code", models.IntegerField(blank=True, null=True)),
                ("ok", models.BooleanField(default=False)),
                ("latency_ms", models.FloatField(blank=True, null=True)),
                ("error_text", models.TextField(blank=True, null=True)),
                ("checked_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("meta", models.JSONField(blank=True, default=dict)),
                (
                    "service",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="results", to="<APP_NAME>.service"),
                ),
            ],
            options={"ordering": ["-checked_at"]},
        ),
        migrations.AddIndex(
            model_name="healthcheckresult",
            index=models.Index(fields=["service", "checked_at"], name="service_checked_at_idx"),
        ),
        migrations.CreateModel(
            name="AIDigest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("period_start", models.DateTimeField()),
                ("period_end", models.DateTimeField()),
                ("anomalies", models.JSONField(blank=True, default=list)),
                ("summary_text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "service",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="digests", to="<APP_NAME>.service"),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

