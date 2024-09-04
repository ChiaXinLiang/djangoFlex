from django.db import models
from django.utils import timezone


class KeyFrame(models.Model):
    frame_id = models.AutoField(primary_key=True)
    frame_time = models.DateTimeField()
    frame_index = models.IntegerField()

class EntityType(models.Model):
    entity_type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=100)
    description = models.TextField()

class DetectedObject(models.Model):
    detected_object_id = models.AutoField(primary_key=True)
    frame = models.ForeignKey(KeyFrame, on_delete=models.CASCADE)
    parent_object = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    entity_type = models.ForeignKey(EntityType, on_delete=models.PROTECT)
    specific_type = models.CharField(max_length=100)
    confidence_score = models.FloatField()
    bounding_box = models.JSONField()  # Storing as JSON array
    segmentation = models.JSONField()  # Storing as JSON array
    re_id = models.IntegerField()

class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=100)
    description = models.TextField()

class PersonRole(models.Model):
    person_role_id = models.AutoField(primary_key=True)
    detected_object = models.ForeignKey(DetectedObject, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)

class SceneType(models.Model):
    scene_type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=100)
    description = models.TextField()

class Scene(models.Model):
    scene_id = models.AutoField(primary_key=True)
    frame = models.ForeignKey(KeyFrame, on_delete=models.CASCADE)
    scene_type = models.ForeignKey(SceneType, on_delete=models.PROTECT)
    description = models.TextField()

class Rule(models.Model):
    rule_id = models.AutoField(primary_key=True)
    rule_code = models.CharField(max_length=50)
    description = models.TextField()
    severity_level = models.IntegerField()
    condition_logic = models.TextField()

class Violation(models.Model):
    violation_id = models.AutoField(primary_key=True)
    rule = models.ForeignKey(Rule, on_delete=models.PROTECT)
    frame = models.ForeignKey(KeyFrame, on_delete=models.CASCADE)
    detected_object = models.ForeignKey(DetectedObject, null=True, blank=True, on_delete=models.SET_NULL)
    scene = models.ForeignKey(Scene, null=True, blank=True, on_delete=models.SET_NULL)
    occurrence_time = models.DateTimeField(default=timezone.now)

class VisionAIConfig(models.Model):
    config_id = models.AutoField(primary_key=True)
    violation_detect_frequency = models.IntegerField(default=1)  # Set violation detect frequency to 1sec 1 frame
    aggregation_interval = models.IntegerField(default=5)  # Default aggregation interval
    last_updated = models.DateTimeField(auto_now=True)