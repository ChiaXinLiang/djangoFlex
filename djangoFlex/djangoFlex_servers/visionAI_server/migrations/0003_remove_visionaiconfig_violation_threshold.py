# Generated by Django 5.0.2 on 2024-09-04 15:52

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("visionAI_server", "0002_visionaiconfig_delete_config"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="visionaiconfig",
            name="violation_threshold",
        ),
    ]