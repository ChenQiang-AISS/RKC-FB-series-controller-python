import os
from typing import Dict, Any
import yaml

CONFIG_FILE_NAME = "rkc_api_config.yaml"

def load_config() -> Dict[str, Any]:
    """
    Loads the configuration from rkc_api_config.yaml.
    Searches in the current working directory and then in the script's directory.
    """
    script_dir = os.path.dirname(__file__)
    # Path within the rkc_controller_api/config directory
    default_config_path = os.path.join(script_dir, CONFIG_FILE_NAME)

    # For robust path finding, consider where the app is run from
    # This assumes config is alongside this __init__.py
    cfg_paths_to_check = [
        os.path.join(os.getcwd(), CONFIG_FILE_NAME), # Check CWD first
        default_config_path # Fallback to package internal
    ]

    loaded_path = None
    for cfg_path in cfg_paths_to_check:
        if os.path.exists(cfg_path):
            loaded_path = cfg_path
            break
    
    if not loaded_path:
        raise FileNotFoundError(
            f"Configuration file '{CONFIG_FILE_NAME}' not found in "
            f"{[os.path.dirname(p) for p in cfg_paths_to_check]}"
        )

    with open(loaded_path, 'r', encoding='utf-8') as stream:
        try:
            config = yaml.safe_load(stream)
            # Construct full log file path
            # Assuming log_directory is relative to the rkc_controller_api package root
            api_package_root = os.path.dirname(script_dir) # Moves up from config to rkc_controller_api
            log_dir_abs = os.path.join(api_package_root, config.get('log_directory', 'logs'))
            
            # Ensure log directory exists
            os.makedirs(log_dir_abs, exist_ok=True)
            
            config['log_file_path'] = os.path.join(log_dir_abs, config.get('log_file', 'rkc_data.csv'))
            return config
        except yaml.YAMLError as exc:
            raise ValueError(f"Error parsing YAML configuration: {exc}") from exc

# Load configuration once when the module is imported
settings = load_config()

# Example of accessing settings:
# from rkc_controller_api.config import settings
# host = settings['host']
