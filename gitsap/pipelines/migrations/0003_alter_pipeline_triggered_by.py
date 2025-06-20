# Generated by Django 5.2 on 2025-06-15 04:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pipelines", "0002_alter_pipeline_triggered_by"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="pipeline",
            name="triggered_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="triggered_pipelines",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
