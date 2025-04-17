import multiprocessing
import os
import pandas as pd
import numpy as np
from LTS.main import initialize_LTS
from LTS.state_manager import write_state
from LTS.lts_processing import LTS
import json
import shutil
from .search import VectorDB
import time

multiprocessing.set_start_method('spawn', force=True)


class LTSManager:
    def __init__(self, projectID: str, labeldb: VectorDB, demo: bool):
        self.project_id = projectID
        self.status = False
        self.process = None
        self.labeldb = labeldb
        self.project_path = f"data/{self.project_id}"
        self.metrics_path = f"{self.project_path}/metrics.json"
        self.stop_path = f"{self.project_path}/stop.txt"
        self.demo = demo

    def train_model(self, label_hilts):
        process_id = self.process.pid
        process_path = f"{self.project_path}/{process_id}"

        print(f"processid: {process_id}")

        args, sampler, data, trainer, labeler = initialize_LTS(self.project_path)

        budget = args.get("budget")
        budget_value = int(args.get("bugetValue"))
        # stop_on = args.get("stop")
        result_json = []
        if budget == "trainingSize":
            loops = int(budget_value/args.get("sample_size"))
            for idx in range(loops):
                loop = idx+1
                if os.path.exists(self.metrics_path):
                    result_json = self.get_metrics(self.project_path)
                    loop = max(result_json["step"]) + 1
                with open(process_path + "/loop.txt", "w") as f:
                    f.write(str(loop))
                log_path = f"{process_path}/log/"
                self.remove_dirc(log_path)
                if idx == 0 and label_hilts =="file":
                    label = label_hilts
                    # stop_on += 1
                else:
                    label = args.get("labeling")
                # if idx+1 == stop_on:
                # # if os.path.exists(self.stop_path):
                #     # print(f"Removing Stop file {self.stop_path}")
                #     # os.remove(self.stop_path)
                #     print("Training stopped!")
                #     return # End of LTS process
                if not self.demo:
                    res =  LTS(sampler, data, args.get("sample_size"), True, trainer, labeler, "filename", True, args.get("metric"), args.get("baseline"), label, loop, self.project_path, process_path, loop)
                else:
                    res = self.get_demo_res(loop, args)
                if len(res) == 0:
                    csvpath =f"data/{self.project_id}/current_sample_training.csv"

                    if os.path.exists(csvpath):
                        df = pd.read_csv(csvpath)
                        image_paths = df["image_path"].to_list()
                        label_llm = ["animal origin" if label == 1 else "not animal origin" for label in df["label"].to_list()]
                        for path, labelllm in zip(image_paths, label_llm):
                            self.labeldb.add_label(image_path=path,label= labelllm, table="relevant")
                        with open(os.path.join(self.project_path, "state.txt"), "w") as f:
                            f.write("User Labeling")
                    return

                if len(res) > 0:
                    # Check if the keys in `res` contain "eval_"
                    is_eval_format = any(key.startswith("eval_") for key in res.keys())

                    # Extract metrics based on the format
                    precision_key = "eval_precision" if is_eval_format else "precision"
                    recall_key = "eval_recall" if is_eval_format else "recall"
                    f1_key = "eval_f1" if is_eval_format else "f1"
                    accuracy_key = "eval_accuracy" if is_eval_format else "accuracy"

                    result = {
                        "step": [loop],
                        "precision": [res[precision_key]],
                        "recall": [res[recall_key]],
                        "f1_score": [res[f1_key]],
                        "accuracy": [res[accuracy_key]],
                    }

                    if not result_json:
                        # If no previous metrics exist, create a new metrics file
                        with open(self.metrics_path, "w") as json_file:
                            json.dump(result, json_file, indent=4)
                    else:
                        # Append metrics to the existing result_json
                        result_json["precision"].append(res[precision_key])
                        result_json["recall"].append(res[recall_key])
                        result_json["f1_score"].append(res[f1_key])
                        result_json["accuracy"].append(res[accuracy_key])
                        result_json["step"].append(loop)

                        # Save the updated metrics to the file
                        with open(self.metrics_path, "w") as json_file:
                            json.dump(result_json, json_file, indent=4)
                else:
                    if os.path.exists(self.stop_path):
                        print(f"Removing Stop file {self.stop_path}")
                        os.remove(self.stop_path)
                    print("LTS Finished!")
                    return # End of LTS process
    # TODO
        # elif budget=="metric":

    def get_demo_res(self, loop, args):
        if loop%2==1:
            with open(os.path.join(self.project_path, "state.txt"), "w") as f:
                f.write("LLM Labeling")
        # if len(res) == 0:
            csvpath =f"data/{self.project_id}/filename_data_labeled.csv"
            size = loop*args.get("sample_size")
            start = size - args.get("sample_size")
            df = pd.read_csv(csvpath)
            df = df[start:size]
            df.to_csv(f"{self.project_path}/current_sample_training.csv", index=False)
            return {}

        if loop%2==0:
            # wait for 2 seconds
            time.sleep(5)
            # Check if the keys in `res` contain "eval_"
            # read from epoch_training.json
            epoch_file = os.path.join(self.project_path, "epoch_training_demo.json")
            write_state(self.project_path, "Training")
            with open(epoch_file, 'r') as file:
                if os.path.getsize(epoch_file) > 0:
                    try:
                        epochs = json.load(file)
                    except json.JSONDecodeError:
                        print(f"Malformed JSON in {epoch_file}. Attempting to clean.")
                        epochs = LTSManager.clean_json(epoch_file) or {}
                else:
                    print(f"Warning: {epoch_file} is empty.")
                    epochs = {}
            # based on the loop number get the last epoch result and save in the epoch path so the get_epoch will work
            total_loops = epochs.get(str(loop), [])
            print(f"Processing loop {loop}...")
            for train in total_loops:
                # Simulate saving epoch data for the current loop
                self.save_epoch_for_loop(train)
                # read from metrics.json
            metrics_file = os.path.join(self.project_path, "metrics_demo.json")
            if os.path.exists(metrics_file):
                with open(metrics_file, "r") as json_file:
                    result_json_demo = json.load(json_file)

            # get the result from the loop number
            res = result_json_demo[loop]

            result = {
                "step": [loop],
                "precision": [res["precision"][loop-1]],
                "recall": [res["recall"][loop-1]],
                "f1_score": [res["f1_score"][loop-1]],
                "accuracy": [res["accuracy"][loop-1]],
            }
            return result
        else:
            return None



    def start_training(self, label_hits, db):
        """
        Starts the model training in a separate process.
        :param args: Arguments for model training
        """
        # Start the training in a new process
        self.process = multiprocessing.Process(target=self.train_model, args=(label_hits,))
        self.process.start()
        self.status = self.process.is_alive()
        self.process_id = self.process.pid
        print(f"Training process started with PID: {self.process_id}")

        # # Save the process ID to a file # DO I NEED THIS?
        self.process_path = f"{self.project_path}/{self.process.pid}"
        os.makedirs(self.process_path, exist_ok=True)
        # Return the training process
        return self.process

    def get_status(self):
        status = {
            "loop": -1,
            "lts_status": "",
            "lts_state": "",
            "stats": {
                "llm_labels": [],
                "epochs": {},
                "training_metrics": {},
                "inference_progress": None
            }
        }
        loop = self.get_loop_idx(self.process_path)
        status["lts_status"] = self.process.is_alive()
        status["loop"] = loop

        metrics = self.get_metrics(self.project_path)
        epochs = self.get_epoch_logs(self.project_path, self.process_path, loop)
        labels = self.get_llm_labels(self.project_path)

        status["lts_state"] = self.get_LTS_state(self.project_path)

        # Get inference progress if available
        inference_progress_path = f"{self.project_path}/inference_progress.json"
        if os.path.exists(inference_progress_path):
            with open(inference_progress_path, "r") as f:
                status["stats"]["inference_progress"] = json.load(f)

        if labels:
            status["stats"]["llm_labels"].append(labels)
        if epochs:
            status["stats"]["epochs"] = epochs
        if metrics:
            status["stats"]["training_metrics"]= metrics

        if not status["lts_status"]:
            self.remove_dirc(self.process_path) ## remove process folder after process is done

        return status

    def stop_LTS(self):
        p_process = f"data/{self.project_id}/{self.process_id}/stop.txt"
        with open(p_process, "w") as f:
            f.write("stop")


    @staticmethod
    def get_LTS_state(project_path):
        state_file = os.path.join(project_path, "state.txt")
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as file:
                    return file.read().strip()
            except Exception as e:
                print(f"Error reading state file: {e}")
                return None
        return None

    @staticmethod
    def get_loop_idx(process_path):
        loop_file = os.path.join(process_path, "loop.txt")
        if os.path.exists(loop_file):
            with open(loop_file, "r") as file:
                return file.read()
        return -1

    @staticmethod
    def get_metrics(project_path):
        metrics_file = os.path.join(project_path, "metrics.json")
        if os.path.exists(metrics_file):
            with open(metrics_file, "r") as json_file:
                return json.load(json_file)
        return None

    @staticmethod
    def get_llm_labels(project_path):
        try:
            labels_file = os.path.join(project_path, "current_sample_training.csv")
            if os.path.exists(labels_file):
                df = pd.read_csv(labels_file)
                count_1 = len(df[df["label"] == 1]) if not df.empty else 0
                count_0 = len(df[df["label"] == 0]) if not df.empty else 0
                return {"1": count_1, "0": count_0}
        except Exception as e:
            print(f"Error reading labels: {e}")
        return None


    @staticmethod
    def get_epoch_logs(project_path, process_path, loop):
        """
        Retrieve and update epoch logs for the current loop.

        Args:
            project_path (str): Path to the project directory.
            process_path (str): Path to the process directory.
            loop (int): Current loop number.

        Returns:
            dict: Updated epoch logs or None if an error occurs.
        """
        log_path = os.path.join(process_path, "log")
        epoch_file = os.path.join(log_path, "epoch.json")
        training_file = os.path.join(project_path, "epoch_training.json")

        try:
            # Check if the epoch file exists
            if os.path.exists(epoch_file):
                # Ensure the file is not empty
                if os.path.getsize(epoch_file) > 0:
                    with open(epoch_file, 'r') as file:
                        epoch_logs = json.load(file)
                else:
                    print(f"Warning: {epoch_file} is empty.")
                    return None

                # Handle the training file for multiple loops
                # if loop == 1 and os.path.exists(training_file):
                #     os.remove(training_file)

                if os.path.exists(training_file):
                    with open(training_file, 'r') as file:
                        if os.path.getsize(training_file) > 0:
                            try:
                                epochs = json.load(file)
                            except json.JSONDecodeError:
                                print(f"Malformed JSON in {training_file}. Attempting to clean.")
                                epochs = LTSManager.clean_json(training_file) or {}
                        else:
                            print(f"Warning: {training_file} is empty.")
                            epochs = {}
                    epochs[f"{loop}"] = epoch_logs
                else:
                    epochs = {f"{loop}": epoch_logs}

                # Validate JSON before saving
                if LTSManager.validate_json(epochs):
                    with open(training_file, 'w') as file:
                        json.dump(epochs, file, indent=4)
                else:
                    print(f"Invalid JSON data. Skipping save for {training_file}.")
                    return None

                return epochs

            # Handle the case where the training file exists but the epoch file does not
            elif os.path.exists(training_file):
                with open(training_file, 'r') as file:
                    if os.path.getsize(training_file) > 0:
                        try:
                            return json.load(file)
                        except json.JSONDecodeError:
                            print(f"Malformed JSON in {training_file}. Attempting to clean.")
                            return LTSManager.clean_json(training_file)
                    else:
                        print(f"Warning: {training_file} is empty.")
                        return None

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in {epoch_file} or {training_file}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in get_epoch_logs: {e}")
            return None

        return None

    @staticmethod
    def remove_dirc(path):
        # Check if directory exists
        if os.path.exists(path):
            # Iterate through the directory and remove files/subdirectories
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Remove subdirectory
                else:
                    os.remove(file_path)  # Remove file

            # Now remove the empty directory
            os.rmdir(path)

    @staticmethod
    def validate_json(data):
        """
        Validate if the given data can be serialized to JSON.

        Args:
            data (dict): The data to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            json.dumps(data)
            return True
        except (TypeError, ValueError) as e:
            print(f"Invalid JSON data: {e}")
            return False

    @staticmethod
    def clean_json(file_path):
        """
        Attempt to clean a malformed JSON file by removing duplicate keys or extra data.

        Args:
            file_path (str): Path to the JSON file.

        Returns:
            dict: The cleaned JSON data, or None if the file cannot be cleaned.
        """
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            # Attempt to parse each line as JSON
            cleaned_data = []
            for line in lines:
                try:
                    cleaned_data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

            # Combine all valid JSON objects into a single dictionary
            combined_data = {}
            for entry in cleaned_data:
                combined_data.update(entry)

            return combined_data
        except Exception as e:
            print(f"Failed to clean JSON file {file_path}: {e}")
            return None

    def save_epoch_for_loop(self, train_res):
        """
        Simulate saving the epoch data for a specific loop in the process path.

        Args:
            loop (int): The current loop number.
            process_path (str): The path where the epoch data should be saved.
        """
        # Path to the epoch_training.json file
        log_epoch_file = os.path.join(self.process_path, "log", "epoch.json")

        # Ensure the log directory exists
        os.makedirs(os.path.dirname(log_epoch_file), exist_ok=True)

            # Retrieve the epoch data for the current loop
        if train_res:
            # Save the epoch data to the log/epoch.json file
            with open(log_epoch_file, "w") as log_file:
                json.dump(train_res, log_file, indent=4)
            print(f"Saved epoch data to {log_epoch_file}")
        else:
            print(f"No epoch data found")







