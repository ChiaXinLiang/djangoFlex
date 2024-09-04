from rest_framework import serializers
from ..models import Rule, Role, EntityType, SceneType

class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ['rule_id', 'rule_code', 'description', 'severity_level', 'condition_logic']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['role_id', 'role_name', 'description']

class EntityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityType
        fields = ['entity_type_id', 'type_name', 'description']

class SceneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SceneType
        fields = ['scene_type_id', 'type_name', 'description']
