# Generated by Django 5.2 on 2025-05-27 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0021_project_unique_project_handle_per_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='namespace',
            field=models.SlugField(blank=True, max_length=128),
        ),
    ]
