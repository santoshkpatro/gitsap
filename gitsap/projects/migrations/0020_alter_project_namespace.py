# Generated by Django 5.2 on 2025-05-24 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0019_remove_project_unique_project_handle_per_owner"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="namespace",
            field=models.SlugField(blank=True, max_length=128, unique=True),
        ),
    ]
