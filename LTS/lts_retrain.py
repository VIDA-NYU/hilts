import pandas as pd
import numpy as np
import os
import json

def LTS(sampler, data, sample_size, filter_label, trainer, labeler, filename, balance, metric, baseline, labeling, retrain, indx):
    training_data, chosen_bandit = sampler.get_sample_data(data, sample_size, filter_label, trainer)
    ## Generate labels
    if labeling != "file":
        training_data = labeler.generate_inference_data(training_data, 'clean_title')
        training_data["answer"] = training_data.apply(lambda x: labeler.predict_animal_product(x), axis=1)
        training_data["answer"] = training_data["answer"].str.strip()
        training_data["label"] = np.where(training_data["answer"] == 'relevant animal', 1, 0)
        file_name = f"data_labeled_{filename}.csv"
        load_and_save_csv(file_name, training_data)

    if sampler.__class__.__name__ == "ThompsonSampler":
        sampler.update(chosen_bandit, training_data)

    # ADD POSITIVE DATA IF AVAILABLE
    training_data = add_previous_data(training_data, filename)
    # Balance Data (undersampling) # postpone use of undesire labels negative
    training_data, still_unbalenced = maybe_balance_data(balance, training_data)

    ## FINE TUNE MODEL
    #get base model
    model_name, baseline = get_model_and_baseline(trainer, metric, baseline, retrain)

    results, _ = trainer.train_data(training_data, still_unbalenced)

    improved = (results[f"eval_{metric}"] - baseline) > 0

    # not retrain but fine-tune best model
    if improved > 0 and not retrain:
        print(f"Model improved with {improved}")
        model_name = f"models/fine_tunned_{indx}_bandit_{chosen_bandit}"
        trainer.update_model(model_name, results[f"eval_{metric}"], save_model=True)
        # remove used positive data
        if os.path.exists('positive_data.csv'):
            os.remove('positive_data.csv')
        # save separated training data file
        name = f'{filename}_training_data'
        load_and_save_csv(name, training_data)
        # use model to label next sample
        if filter_label:
            trainer.set_clf(True)
    elif improved > 0 and retrain:
        trainer.update_model(model_name, baseline, save_model=True)
        name = f'{filename}_previous_data.csv'
        training_data.to_csv(name,index=False)
        if filter_label:
            trainer.set_clf(True)
    else:
        #back to initial model
        trainer.update_model(model_name, baseline, save_model=False)
        # save positive sample
        # load_and_save_csv("positive_data", training_data[training_data["label"]==1])

    save_bendit_results(filename, chosen_bandit, results)


def load_and_save_csv(filename, data):
    if os.path.exists(f"{filename}.csv"):
        train_data = pd.read_csv(f"{filename}.csv")
        train_data = pd.concat([train_data, data])
        train_data.to_csv(f"{filename}.csv", index=False)
    else:
        data.to_csv(f"{filename}.csv", index=False)


def add_previous_data(df, filename):
    if os.path.exists('positive_data.csv'):
        pos = pd.read_csv('positive_data.csv')
        df = pd.concat([df, pos]).sample(frac=1)
        print(f"adding positive data: {df['label'].value_counts()}")
    if os.path.exists(f'{filename}_previous_data.csv'):
        old = pd.read_csv(f'{filename}_previous_data.csv')
        df = pd.concat([df, old]).sample(frac=1)
        print(f"adding previous data: {df['label'].value_counts()}")
    return df

def maybe_balance_data(balance, df):
    if balance:
        if len(df[df["label"]==1]) > 0:
            unbalanced = len(df[df["label"]==0]) / len(df[df["label"]==1]) >= 2
            if unbalanced:
                label_counts = df["label"].value_counts()
                # Determine the number of samples to keep for each label
                min_count = min(label_counts)
                balanced_df = pd.concat([
                    df[df["label"] == 0].sample(min_count*2),
                    df[df["label"] == 1].sample(min_count)
                ])

                # Shuffle the rows
                df = balanced_df.sample(frac=1).reset_index(drop=True)
                print(f"Balanced data: {df.label.value_counts()}")
    else:
        unbalanced = len(df[df["label"]==0]) / len(df[df["label"]==1]) >= 2
    return df, unbalanced

def get_model_and_baseline(trainer, metric, baseline, retrain):
    # init_model = trainer.get_init_model()
    model_name = trainer.get_base_model()

    model_results = trainer.get_last_model_acc()
    if model_results:
        baseline = model_results[model_name]
        print(f"previous model {metric} metric baseline of: {baseline}")
    else:
        print(f"Starting with metric {metric} baseline {baseline}")
    print(f"Starting training")
    # if retrain:
    #     print(f"using model {init_model}")
    #     return init_model, baseline
    # else:
    #     print(f"using model {model_name}")
    return model_name, baseline

def save_bendit_results(filename, chosen_bandit, results):
    if os.path.exists(f'{filename}_model_results.json'):
        with open(f'{filename}_model_results.json', 'r') as file:
            existing_results = json.load(file)
    else:
        existing_results = {}

    if existing_results.get(str(chosen_bandit)):
        existing_results[str(chosen_bandit)].append(results)
    else:
        existing_results[str(chosen_bandit)] = [results]
    # Write the updated list to the file
    with open(f'{filename}_model_results.json', 'w') as file:
        json.dump(existing_results, file, indent=4)
