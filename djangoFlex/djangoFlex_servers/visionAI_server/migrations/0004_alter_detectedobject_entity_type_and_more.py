# Generated by Django 5.0.2 on 2024-09-04 19:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("visionAI_server", "0003_remove_visionaiconfig_violation_threshold"),
    ]

    operations = [
        migrations.AlterField(
            model_name="detectedobject",
            name="entity_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="visionAI_server.entitytype",
            ),
        ),
        migrations.AlterField(
            model_name="detectedobject",
            name="parent_object",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="visionAI_server.detectedobject",
            ),
        ),
        migrations.AlterField(
            model_name="personrole",
            name="role",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="visionAI_server.role"
            ),
        ),
        migrations.AlterField(
            model_name="scene",
            name="scene_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="visionAI_server.scenetype",
            ),
        ),
        migrations.AlterField(
            model_name="violation",
            name="detected_object",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="visionAI_server.detectedobject",
            ),
        ),
        migrations.AlterField(
            model_name="violation",
            name="rule",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="visionAI_server.rule"
            ),
        ),
        migrations.AlterField(
            model_name="violation",
            name="scene",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="visionAI_server.scene",
            ),
        ),
    ]
