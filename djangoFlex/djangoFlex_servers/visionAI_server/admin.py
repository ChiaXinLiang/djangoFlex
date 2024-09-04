from django.contrib import admin
from .models import KeyFrame, EntityType, DetectedObject, Role, PersonRole, SceneType, Scene, Rule, Violation, VisionAIConfig

@admin.register(KeyFrame)
class KeyFrameAdmin(admin.ModelAdmin):
    list_display = ('frame_id', 'frame_time', 'frame_index')
    search_fields = ('frame_id', 'frame_time')
    actions = ['delete_selected']

@admin.register(EntityType)
class EntityTypeAdmin(admin.ModelAdmin):
    list_display = ('entity_type_id', 'type_name')
    search_fields = ('type_name',)
    actions = ['delete_selected']

@admin.register(DetectedObject)
class DetectedObjectAdmin(admin.ModelAdmin):
    list_display = ('detected_object_id', 'frame', 'parent_object', 'entity_type', 'specific_type', 'confidence_score', 're_id')
    list_filter = ('entity_type', 'specific_type', 'parent_object')
    search_fields = ('specific_type', 're_id', 'parent_object__detected_object_id')
    actions = ['delete_selected']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name')
    search_fields = ('role_name',)
    actions = ['delete_selected']

@admin.register(PersonRole)
class PersonRoleAdmin(admin.ModelAdmin):
    list_display = ('person_role_id', 'detected_object', 'role')
    list_filter = ('role',)
    actions = ['delete_selected']

@admin.register(SceneType)
class SceneTypeAdmin(admin.ModelAdmin):
    list_display = ('scene_type_id', 'type_name')
    search_fields = ('type_name',)
    actions = ['delete_selected']

@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ('scene_id', 'frame', 'scene_type')
    list_filter = ('scene_type',)
    actions = ['delete_selected']

@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('rule_id', 'rule_code', 'severity_level')
    list_filter = ('severity_level',)
    search_fields = ('rule_code', 'description')
    actions = ['delete_selected']

@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ('violation_id', 'rule', 'frame', 'detected_object', 'scene', 'occurrence_time')
    list_filter = ('rule', 'occurrence_time')
    search_fields = ('rule__rule_code', 'detected_object__specific_type')
    actions = ['delete_selected']

@admin.register(VisionAIConfig)
class VisionAIConfigAdmin(admin.ModelAdmin):
    list_display = ('config_id', 'violation_detect_frequency', 'aggregation_interval', 'last_updated')
    actions = ['delete_selected']
