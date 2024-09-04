import yaml
import logging
from django.conf import settings
from django.db import transaction
from django.core.exceptions import MultipleObjectsReturned
from djangoFlex_servers.visionAI_server.models import Rule, Role, EntityType, SceneType

logger = logging.getLogger(__name__)

class VisionAIDBService:
    @staticmethod
    def load_from_yaml(model_class, yaml_file):
        try:
            file_path = f"djangoFlex_servers/visionAI_server/type_initial_config/{yaml_file}"
            with open(file_path, 'r') as file:
                yaml_data = yaml.safe_load(file)
                
            if not yaml_data or not isinstance(yaml_data, list):
                raise ValueError(f"Invalid or empty data in {yaml_file}")
            
            with transaction.atomic():
                for item in yaml_data:
                    if 'fields' not in item:
                        raise ValueError(f"Missing 'fields' key in item from {yaml_file}")
                    
                    fields = item['fields']
                    
                    try:
                        obj, created = model_class.objects.get_or_create(**fields)
                        if created:
                            logger.info(f"Created new {model_class.__name__}: {obj}")
                        else:
                            logger.info(f"Found existing {model_class.__name__}: {obj}")
                    except MultipleObjectsReturned:
                        logger.warning(f"Multiple {model_class.__name__}s found for {fields}. Skipping.")
                    except Exception as e:
                        logger.error(f"Error processing {model_class.__name__} with fields {fields}: {str(e)}")
            
            logger.info(f"{model_class.__name__}s loaded and saved to database successfully from {yaml_file}")
        except Exception as e:
            logger.error(f"Error loading and saving {model_class.__name__}s from {yaml_file}: {str(e)}")
            raise

    @classmethod
    def load_all_from_yaml(cls):
        for model_class, yaml_file in [
            (Rule, 'rule.yaml'),
            (Role, 'role.yaml'),
            (EntityType, 'entity_type.yaml'),
            (SceneType, 'scene_type.yaml')
        ]:
            cls.load_from_yaml(model_class, yaml_file)

    @staticmethod
    def get_all_rules():
        return {rule.rule_code: rule for rule in Rule.objects.all()}

    @staticmethod
    def get_all_roles():
        return {role.role_name: role for role in Role.objects.all()}

    @staticmethod
    def get_all_entity_types():
        return {et.type_name: et for et in EntityType.objects.all()}

    @staticmethod
    def get_all_scene_types():
        return {st.type_name: st for st in SceneType.objects.all()}

    @staticmethod
    def delete_all():
        with transaction.atomic():
            Rule.objects.all().delete()
            Role.objects.all().delete()
            EntityType.objects.all().delete()
            SceneType.objects.all().delete()
        logger.info("All rules, roles, entity types, and scene types have been deleted.")
