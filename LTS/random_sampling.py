from typing import Any
import numpy as np
import pandas as pd

class RandomSampler:
    def __init__(self, n_bandits, id):
        self.n_bandits = n_bandits
        self.id = id
        try:
            self.selected_ids = set(np.loadtxt(f'data/{id}/selected_ids.txt', dtype=str))
        except IOError:
            self.selected_ids = set()

    def get_selected_id(self):
        try:
            self.selected_ids = set(np.loadtxt(f'data/{self.id}/selected_ids.txt', dtype=str))
        except IOError:
            self.selected_ids = set()
        return self.selected_ids

    def create_validation_data(self, df, val_size):
        if val_size < self.n_bandits:
            samples_per_cluster = 1
        samples_per_cluster = int(val_size / self.n_bandits)
        # Sample data from each cluster
        # sampled_data = []
        sampled_data = df.groupby('label_cluster').apply(lambda x: x.sample(n=min(samples_per_cluster, len(x)), random_state=1)).reset_index(drop=True)
        # print(df.groupby('label_cluster').groups)
        # for name, group in df.groupby('label_cluster'):
        #     sample = group.sample(n=min(samples_per_cluster, len(group)), random_state=1)
        #     print(sample)
        #     sampled_data.append()
        # sampled_data = pd.concat(sampled_data)
        sampled_data = sampled_data.sample(frac=1, random_state=42).reset_index(drop=True)
        # Add the IDs of sampled data to the selected_ids set to not add this data on the training set
        self.selected_ids.update(sampled_data['id'])
        with open(f'data/{self.id}/selected_ids.txt', 'w') as f:
            f.write('\n'.join(self.selected_ids))

        return sampled_data, "random"

    def get_sample_data(self, df, sample_size, filter_label: bool, trainer: Any):
            selected_ids = self.get_selected_id()

            samples_per_cluster = int(sample_size / self.n_bandits)

            df = df[~df['id'].isin(selected_ids)]
            if filter_label and trainer.get_clf():
                sample_class = int(samples_per_cluster/2)
                df["predicted_label"] = trainer.get_inference(df)
                pos_df = df[df["predicted_label"] == 1]
                neg_df = df[df["predicted_label"] == 0]
                sampled_data_pos = pos_df.groupby('label_cluster').apply(lambda x: x.sample(n=min(sample_class, len(x)), random_state=1)).reset_index(drop=True)
                sampled_data_neg = neg_df.groupby('label_cluster').apply(lambda x: x.sample(n=min(sample_class, len(x)), random_state=1)).reset_index(drop=True)
                sampled_data = pd.concat([sampled_data_pos, sampled_data_neg])
                sampled_data = sampled_data.sample(frac=1, random_state=42).reset_index(drop=True)
            else:
                sampled_data = df.groupby('label_cluster').apply(lambda x: x.sample(n=min(samples_per_cluster, len(x)), random_state=1)).reset_index(drop=True)
                sampled_data = sampled_data.sample(frac=1, random_state=42).reset_index(drop=True)

            # Add the IDs of sampled data to the selected_ids set
            self.selected_ids.update(sampled_data['id'])
            with open(f'data/{self.id}/selected_ids.txt', 'w') as f:
                f.write('\n'.join(self.selected_ids))

            return sampled_data, "random"
