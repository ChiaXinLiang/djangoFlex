# Generated by Django 5.0.2 on 2024-11-01 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videoCap_server', '0009_remove_cameralist_camera_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cameralist',
            name='camera_status',
            field=models.BooleanField(default=False),
        ),
    ]
