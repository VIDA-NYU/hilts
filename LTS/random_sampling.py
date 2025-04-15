from typing import Any
import numpy as np
import pandas as pd
import os

class RandomSampler:
    def __init__(self, cluster_size, project_path):
        self.cluster_size = cluster_size
        self.project_path = project_path
        self.selected_ids = set(np.loadtxt(f'{project_path}/selected_ids.txt', dtype=str)) if os.path.exists(f'{project_path}/selected_ids.txt') else set()

    def sample_data(self, data, sample_size):
        # Filter out already selected IDs
        available_data = data[~data.index.isin(self.selected_ids)]
        if available_data.empty:
            return pd.DataFrame(), None

        # Sample data
        sample = available_data.sample(n=min(sample_size, len(available_data)))

        # Update selected IDs
        self.selected_ids.update(sample.index)

        # Save selected IDs
        np.savetxt(f'{self.project_path}/selected_ids.txt', list(self.selected_ids), fmt='%s')

        return sample, None

    def create_validation_data(self, df, val_size):
        print(val_size, self.cluster_size)
        if val_size < self.cluster_size:
            samples_per_cluster = 1
        samples_per_cluster = int(val_size / self.cluster_size)
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
        if sampled_data.empty:
            print("Validation is empty")
        # Add the IDs of sampled data to the selected_ids set to not add this data on the training set
        self.selected_ids.update(sampled_data['id'])
        with open(f'{self.project_path}/selected_ids.txt', 'w') as f:
            f.write('\n'.join(self.selected_ids))

        return sampled_data, "random"

    def get_sample_data(self, df, sample_size, filter_label: bool, trainer: Any):
            selected_ids = self.selected_ids

            samples_per_cluster = int(sample_size / self.cluster_size)

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
            with open(f'{self.project_path}/selected_ids.txt', 'w') as f:
                f.write('\n'.join(self.selected_ids))

            return sampled_data, "random"
