import yaml
import os
from django.conf import settings

def load_config_from_yaml(file_path):
    """
    Load configuration from a YAML file.

    Args:
        file_path (str): Path to the YAML configuration file.

    Returns:
        dict: Configuration dictionary.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(file_path, 'r') as config_file:
        try:
            config = yaml.safe_load(config_file)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration file: {e}")

    return config

def update_django_settings(config):
    """
    Update Django settings with values from the configuration.

    Args:
        config (dict): Configuration dictionary.
    """
    for key, value in config.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
        else:
            # Optionally, you can log a warning for keys not present in Django settings
            print(f"Warning: {key} is not a recognized Django setting.")

def load_and_update_config(file_path):
    """
    Load configuration from YAML and update Django settings.

    Args:
        file_path (str): Path to the YAML configuration file.
    """
    config = load_config_from_yaml(file_path)
    update_django_settings(config)

# Example usage:
# load_and_update_config('path/to/your/config.yaml')
