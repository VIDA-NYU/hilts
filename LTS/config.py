import json
import os
from typing import Dict, Any


def parse_args(project_path: str) -> Dict[str, Any]:
    """
    Parse configuration from the project's config file.

    Args:
        project_path: Path to the project directory containing config_file.json

    Returns:
        Dict containing the configuration

    Raises:
        ValueError: If config file is missing or invalid
    """
    config_file = os.path.join(project_path, "config_file.json")
    if not os.path.exists(config_file):
        raise ValueError(f"Config file not found at {config_file}")

    try:
        config = read_config(config_file)
        if not config:
            raise ValueError("Config file is empty")
        return config
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error reading config file: {str(e)}")


def read_config(config_file: str) -> Dict[str, Any]:
    """
    Reads the configuration from a JSON file.

    Args:
        config_file: Path to the config file

    Returns:
        Dict containing the configuration

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON
    """
    with open(config_file, "r") as f:
        return json.load(f)


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validates the configuration dictionary.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If required fields are missing or invalid
    """
    required_fields = {
        "sampling": str,
        "sample_size": int,
        "filter_label": bool,
        "balance": bool,
        "model_finetune": str,
        "labeling": str,
        "filename": str,
        "model": str,
        "metric": str,
        "val_size": int,
        "cluster_size": str,
        "budget": int,
        "retrain": bool,
        "baseline": (int, float),
    }

    for field, field_type in required_fields.items():
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
        if not isinstance(config[field], field_type):
            raise ValueError(f"Invalid type for {field}: expected {field_type}, got {type(config[field])}")

def save_config(config, config_path):
    """
    Saves the updated configuration to a JSON file.
    """
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

def update_config(project_path, new_info):
    """
    Updates the configuration file for a given project ID with new information.
    """
    config_path = f"{project_path}/config_file.json"
    config = read_config(config_path)

    ## continue from where it stops
    budget_value = config.get("bugetValue")
    sample_size = config.get("sample_size")
    loops = int(budget_value/sample_size)

    budget_used = new_info.get("bugetValue")
    if budget_used:
        loop_left = loops - (budget_used)
    else:
        loop_left = loops
    budget = loop_left * sample_size

    config["model_finetune"] = new_info.get("model_finetune", config.get("model_finetune"))
    config["bugetValue"] = budget
    config["baseline"] = new_info.get("baseline", config.get("baseline"))

    # Save the updated config back to the file
    save_config(config, config_path)

    print("Config updated successfully.")




