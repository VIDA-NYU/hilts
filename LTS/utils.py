import pandas as pd
import numpy as np
import os
import json
import time
from .random_sampling import RandomSampler
from .fine_tune import BertFineTuner
from .thompson_sampling import ThompsonSampler
from .clustering import TextClustering
from .state_manager import write_state

def create_clustered_data(preprocessor, algorithm, cluster_size, project_path, demo):
    """
    Load data from a CSV file and apply LDA if necessary.
    Returns the processed DataFrame.
    """

    try:
        data = pd.read_csv(f"{project_path}/filename_cluster_data.csv")
        print("Using data saved on disk")
    except FileNotFoundError:
        write_state(project_path, "Clustering Data")
        if demo:
            time.sleep(5)
        data = pd.read_csv(f"{project_path}/filename.csv")
        data = preprocessor.preprocess_df(data)

        print("Creating LDA")
        clustering = TextClustering(data, "title", cluster_size, algorithm, project_path)
        clustering.preprocess_text()
        data = clustering.perform_clustering()
    return data


def save_validation_data(validation, filename):
    """
    Save validation data to a CSV file.
    """
    validation.to_csv(filename, index=False)

def load_json(filename):
    """
    Load data from a JSON file.
    Returns the loaded data.
    """
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return {}

def save_json(data, filename):
    """
    Save data to a JSON file.
    """
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def balance_data(df):
    """
    Balance the DataFrame based on the label column.
    Returns the balanced DataFrame.
    """
    label_counts = df["label"].value_counts()
    if len(label_counts) == 2:
        min_count = min(label_counts)
        balanced_df = pd.concat([
            df[df["label"] == 0].sample(min_count * 2),
            df[df["label"] == 1].sample(min_count)
        ])
        return balanced_df.sample(frac=1).reset_index(drop=True)
    return df

def print_summary(sampler):
    """
    Print a summary of the sampler's performance.
    """
    print("Bandit with highest expected improvement:", np.argmax(sampler.wins / (sampler.wins + sampler.losses)))
    print(sampler.wins)
    print(sampler.losses)

def prepare_validation(validation_path, validation_size, data, labeler, preprocessor, project_path, demo):
    if demo:
        write_state(project_path, "Creating Validation")
        time.sleep(5)
    if os.path.exists(f'{project_path}/validation.csv'):
        validation = pd.read_csv(f'{project_path}/validation.csv')
    elif validation_path:
        validation = pd.read_csv(validation_path)
        validation = preprocessor.preprocess_df(validation)
        save_validation_data(validation, f"{project_path}/validation.csv")
    else:
        write_state(project_path, "Creating Validation")
        sampler = RandomSampler(data['label_cluster'].nunique(), project_path)
        sample_validation, _ = sampler.create_validation_data(data, validation_size)
        validation = labeler.generate_inference_data(sample_validation, 'clean_title')
        if "label" not in validation.columns:
            answer = labeler.predict_animal_product(validation)
            validation["answer"] = answer
            validation["answer"] = validation["answer"].str.strip()
            validation["label"] = np.where(validation["answer"].str.contains("not a relevant product"), 0, 1)
        save_validation_data(validation, f"{project_path}/validation.csv")
    return validation

def initialize_trainer(model, model_finetune, validation, project_path):
    return BertFineTuner(model_finetune, None, validation, project_path=project_path)

def initialize_sampler(sampling, cluster_size, project_path):
    if sampling == "thompson":
        return ThompsonSampler(cluster_size, project_path)
    elif sampling == "random":
        return RandomSampler(cluster_size, project_path)
    else:
        raise ValueError("Choose one of thompson or random")

def load_and_save_csv(filename, data):
    if os.path.exists(f"{filename}.csv"):
        train_data = pd.read_csv(f"{filename}.csv")
        train_data = pd.concat([train_data, data])
        train_data.to_csv(f"{filename}.csv", index=False)
    else:
        data.to_csv(f"{filename}.csv", index=False)


