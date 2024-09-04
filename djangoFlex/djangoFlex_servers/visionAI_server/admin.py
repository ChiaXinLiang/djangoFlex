from django.contrib import admin
from .models import KeyFrame, EntityType, DetectedObject, Role, PersonRole, SceneType, Scene, Rule, Violation, VisionAIConfig

@admin.register(KeyFrame)
class KeyFrameAdmin(admin.ModelAdmin):
    list_display = ('frame_id', 'frame_time', 'frame_index', 'rtmp_url')
    search_fields = ('frame_id', 'frame_time', 'rtmp_url')
    list_filter = ('rtmp_url',)
    actions = ['delete_selected']

@admin.register(EntityType)
class EntityTypeAdmin(admin.ModelAdmin):
    list_display = ('entity_type_id', 'type_name')
    search_fields = ('type_name',)
    actions = ['delete_selected']

@admin.register(DetectedObject)
class DetectedObjectAdmin(admin.ModelAdmin):
    list_display = ('detected_object_id', 'frame', 'parent_object', 'entity_type', 'specific_type', 'confidence_score', 're_id', 'frame_time', 'rtmp_url')
    list_filter = ('entity_type', 'specific_type', 'parent_object', 'frame__rtmp_url')
    search_fields = ('specific_type', 're_id', 'parent_object__detected_object_id', 'frame__rtmp_url')
    actions = ['delete_selected']

    def frame_time(self, obj):
        return obj.frame.frame_time if obj.frame else "N/A"
    frame_time.short_description = 'Frame Time'

    def rtmp_url(self, obj):
        return obj.frame.rtmp_url if obj.frame else "N/A"
    rtmp_url.short_description = 'RTMP URL'

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name')
    search_fields = ('role_name',)
    actions = ['delete_selected']

@admin.register(PersonRole)
class PersonRoleAdmin(admin.ModelAdmin):
    list_display = ('person_role_id', 'detected_object', 'role', 'frame_time', 'rtmp_url')
    list_filter = ('role', 'detected_object__frame__rtmp_url')
    search_fields = ('detected_object__frame__rtmp_url',)
    actions = ['delete_selected']

    def frame_time(self, obj):
        return obj.detected_object.frame.frame_time if obj.detected_object and obj.detected_object.frame else "N/A"
    frame_time.short_description = 'Frame Time'

    def rtmp_url(self, obj):
        return obj.detected_object.frame.rtmp_url if obj.detected_object and obj.detected_object.frame else "N/A"
    rtmp_url.short_description = 'RTMP URL'

@admin.register(SceneType)
class SceneTypeAdmin(admin.ModelAdmin):
    list_display = ('scene_type_id', 'type_name')
    search_fields = ('type_name',)
    actions = ['delete_selected']

@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ('scene_id', 'frame', 'scene_type', 'frame_time', 'rtmp_url')
    list_filter = ('scene_type', 'frame__rtmp_url')
    search_fields = ('frame__rtmp_url',)
    actions = ['delete_selected']

    def frame_time(self, obj):
        return obj.frame.frame_time if obj.frame else "N/A"
    frame_time.short_description = 'Frame Time'

    def rtmp_url(self, obj):
        return obj.frame.rtmp_url if obj.frame else "N/A"
    rtmp_url.short_description = 'RTMP URL'

@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('rule_id', 'rule_code', 'severity_level')
    list_filter = ('severity_level',)
    search_fields = ('rule_code', 'description')
    actions = ['delete_selected']

@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ('violation_id', 'rule', 'frame', 'detected_object', 'scene', 'occurrence_time', 'frame_time', 'rtmp_url')
    list_filter = ('rule', 'occurrence_time', 'frame__rtmp_url')
    search_fields = ('rule__rule_code', 'detected_object__specific_type', 'frame__rtmp_url')
    actions = ['delete_selected']

    def frame_time(self, obj):
        return obj.frame.frame_time if obj.frame else "N/A"
    frame_time.short_description = 'Frame Time'

    def rtmp_url(self, obj):
        return obj.frame.rtmp_url if obj.frame else "N/A"
    rtmp_url.short_description = 'RTMP URL'

@admin.register(VisionAIConfig)
class VisionAIConfigAdmin(admin.ModelAdmin):
    list_display = ('config_id', 'violation_detect_frequency', 'aggregation_interval', 'last_updated')
    actions = ['delete_selected']
