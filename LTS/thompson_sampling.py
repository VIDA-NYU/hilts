from typing import Any
import numpy as np
from scipy.stats import beta
import os
import pandas as pd

class ThompsonSampler:
    def __init__(self, n_bandits, project_id, alpha=0.5, beta=0.5, decay=0.99):
        self.n_bandits = n_bandits
        self.project_id = project_id
        # self.wins = np.zeros(n_bandits)  # Initialize wins array
        # self.losses = np.zeros(n_bandits)  # Initialize losses array
        self.alpha = alpha  # Prior parameter for Beta distribution (successes)
        self.beta = beta   # Prior parameter for Beta distribution (failures)
        self.decay = decay
        try:
            self.selected_ids = set(np.loadtxt(f'data/{self.project_id}/selected_ids.txt', dtype=str))
        except IOError:
            self.selected_ids = set()

        try:
            self.wins = np.loadtxt(f'data/{self.project_id}/wins.txt')
            self.losses = np.loadtxt(f'data/{self.project_id}/losses.txt')
        except IOError:
            self.wins = np.zeros(n_bandits)
            self.losses = np.zeros(n_bandits)

    def choose_bandit(self):
        betas = beta(self.wins + self.alpha, self.losses + self.beta)
        sampled_rewards = betas.rvs(size=self.n_bandits)
        return np.argmax(sampled_rewards)

    def update(self, chosen_bandit, df):

        pos = df["label"].value_counts().get(1, 0)
        neg = df["label"].value_counts().get(0, 0)
        self.wins[chosen_bandit] += pos
        self.losses[chosen_bandit] += neg

        self.wins *= self.decay
        self.losses *= self.decay

        np.savetxt(f'data/{self.project_id}/wins.txt', self.wins)
        np.savetxt(f'data/{self.project_id}/losses.txt', self.losses)

    def get_sample_data(self, df, sample_size, filter_label: bool, trainer: Any, labeling: str, filename: str):

        def select_data(df, chosen_bandit, sample_size):
            filtered_df = df[df['label_cluster'] == chosen_bandit].sample(min(sample_size, len(df[df['label_cluster'] == chosen_bandit])))
            return filtered_df

        if labeling == "file":
            if os.path.exists(f"data/{self.project_id}/{filename}.csv"):
                new_labels_df = pd.read_csv(f"data/{self.project_id}/hilts_data.csv")
                self.update_labels(filename, new_labels_df)
            return new_labels_df, new_labels_df["label_cluster"].unique()[0]

        #remove already used data
        df = df[~df['id'].isin(self.selected_ids)]

        data = pd.DataFrame()
        while data.empty:
            chosen_bandit = self.choose_bandit()
            print(f"Chosen bandit {chosen_bandit}")
            bandit_df = df[df["label_cluster"] == chosen_bandit]
            print(f"length of bendit {len(bandit_df)}")
            if not bandit_df.empty:
                if filter_label:
                    if trainer.get_clf():
                        bandit_df["predicted_label"] = trainer.get_inference(bandit_df)
                        print("inference results")
                        print(bandit_df["predicted_label"].value_counts())
                    if "predicted_label" in bandit_df.columns:
                        print("inference results")
                        print(bandit_df["predicted_label"].value_counts())
                        pos = bandit_df[bandit_df["predicted_label"] == 1]
                        neg = bandit_df[bandit_df["predicted_label"] == 0]
                        if pos.empty:
                            print("no positive data available")
                            data=pos
                        else:
                            n_sample = sample_size/2
                            data = select_data(pos, chosen_bandit, int(n_sample))
                            neg_data = select_data(neg, chosen_bandit, int(sample_size-len(data)))
                            data = pd.concat([data, neg_data]).sample(frac=1)
                    else:
                        data = select_data(bandit_df, chosen_bandit, sample_size)
                else:
                    data = select_data(bandit_df, chosen_bandit, sample_size)


        # Add the IDs of sampled data to the selected_ids set
        self.selected_ids.update(data['id'])
        with open(f'data/{self.project_id}/selected_ids.txt', 'w') as f:
            f.write('\n'.join(self.selected_ids))

        return data, chosen_bandit

    def update_labels(self, filename, new_labels_df):
        # Check if the CSV file exists
        if os.path.exists(f"data/{self.project_id}/{filename}.csv"):
            # Read the original data (df)
            df = pd.read_csv(f"data/{self.project_id}/{filename}.csv")

            # Ensure that the 'id' or common column is present to match the rows for updating
            if "id" not in df.columns or "id" not in new_labels_df.columns:
                raise ValueError("Both dataframes must contain an 'id' column to merge on.")


            updated_df = df.merge(new_labels_df[['id', 'label']], on='id', how='left', suffixes=('', '_corrected'))

            # Now, we update the 'label' column in df with the 'label_corrected' column from new_labels_df.
            updated_df['label'] = updated_df['label_corrected'].combine_first(updated_df['label'])

            # Drop the temporary 'label_corrected' column
            updated_df = updated_df.drop(columns=['label_corrected'])

            # Save the updated DataFrame back to CSV
            updated_df.to_csv(f"data/{self.project_id}/{filename}.csv", index=False)

            print(f"Labels updated and saved to {self.project_id}/{filename}.csv")
        else:
            print(f"File {filename}.csv does not exist in {self.project_id}.")
