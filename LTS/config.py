import json

def parse_args(project_id):
    # parser = argparse.ArgumentParser(prog="Sampling fine-tuning", description='Perform Sampling and fine tune')
    # parser.add_argument('-sampling', type=str, help="Name of sampling method")
    # parser.add_argument('-sample_size', type=int, help="Sample size")
    # parser.add_argument('-filter_label', type=bool, help="Use model clf results to filter data")
    # parser.add_argument('-balance', type=bool, help="Balance positive and negative samples")
    # parser.add_argument('-model_finetune', type=str, help="Model base for fine tuning")
    # parser.add_argument('-labeling', type=str, help="Model to be used for labeling or file if label already on file")
    # parser.add_argument('-filename', type=str, help="The initial file to be used")
    # parser.add_argument('-model', type=str, help="The type of model to be fine-tuned")
    # parser.add_argument('-metric', type=str, help="The type of metric to be used for baseline")
    # parser.add_argument('-val_path', type=str, help="Path to validation")
    # parser.add_argument('-val_size', type=int, help="Size of validation data if no validation is provided")
    # parser.add_argument('-cluster_size', type=str, help="Path to validation")
    # parser.add_argument('-budget', type=int, help="Number of times to do the loop")
    # parser.add_argument('-retrain', type=bool, help="retrain or keep the best model to fine tune")
    # parser.add_argument('-baseline', type=float, help="The initial baseline metric")
    # parser.add_argument('-id', type=str, help="The id of the process")


    # def parse_args(project_id):
    try:
        config = read_config(f"data/{project_id}/config_file.json")
    except Exception as e:
        raise ValueError(f"Config file is required: {e}")
    return config


def read_config(config_file):
    """
    Reads the configuration from a JSON file.
    """
    with open(config_file, "r") as f:
        return json.load(f)

def save_config(config, config_file):
    """
    Saves the updated configuration to a JSON file.
    """
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)

def update_config(project_id, new_info):
    """
    Updates the configuration file for a given project ID with new information.
    """
    config_file = f"data/{project_id}/config_file.json"

    config = read_config(config_file)

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
    save_config(config, config_file)

    print("Config updated successfully.")




