# Generated by Django 5.0.2 on 2024-09-04 14:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("videoCap_server", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="videocapconfig",
            name="redis_client",
            field=models.CharField(default="default", max_length=255),
        ),
        migrations.AddField(
            model_name="videocapconfig",
            name="redis_host",
            field=models.CharField(default="localhost", max_length=255),
        ),
        migrations.AlterField(
            model_name="videocapconfig",
            name="frame_interval",
            field=models.FloatField(default=0.1),
        ),
    ]
