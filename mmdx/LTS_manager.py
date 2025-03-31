import multiprocessing
import os
import pandas as pd
import numpy as np
from LTS.main import initialize_LTS
from LTS.lts_processing import LTS
import json
import shutil
from .search import VectorDB
multiprocessing.set_start_method('spawn', force=True)


class LTSManager:
    def __init__(self, projectID: str, labeldb: VectorDB):
        self.project_id = projectID
        self.status = False
        self.process = None
        self.labeldb = labeldb
        self.project_path = f"data/{self.project_id}"
        self.metrics_path = f"{self.project_path}/metrics.json"
        self.stop_path = f"{self.project_path}/stop.txt"
        # self.label_hilts = args.get("labeling")

    def train_model(self, label_hilts):

        process_id = self.process.pid
        state_path = f"{self.project_path}/{process_id}"

        print(f"processid: {process_id}")

        args, sampler, data, trainer, labeler = initialize_LTS(self.project_id, self.project_path, label_hilts)

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
                with open(state_path + "/loop.txt", "w") as f:
                    f.write(str(loop))
                log_path = f"{state_path}/log/"
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
                res =  LTS(sampler, data, args.get("sample_size"), True, trainer, labeler, "filename", True, args.get("metric"), args.get("baseline"), label, idx, self.project_id, self.project_path, state_path)
                if len(res) == 0:
                    csvpath =f"data/{self.project_id}/current_sample_training.csv"

                    if os.path.exists(csvpath):
                        df = pd.read_csv(csvpath)
                        image_paths = df["image_path"].to_list()
                        label_llm = ["animal origin" if label == 1 else "not animal origin" for label in df["label"].to_list()]
                        for path, labelllm in zip(image_paths, label_llm):
                            self.labeldb.add_label(image_path=path,label= labelllm, table="relevant")
                        with open(self.project_path + "/state.txt", "w") as f:
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
                "training_metrics": {}
            }
        }
        loop = self.get_loop_idx(self.process_path)
        status["lts_status"] = self.process.is_alive()
        status["loop"] = loop


        metrics = self.get_metrics(self.project_path)
        epochs = self.get_epoch_logs(self.project_path, self.process_path, loop)
        labels = self.get_llm_labels(self.project_path)

        status["lts_state"] = self.get_LTS_state(self.project_path)

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
        # print(project_path + "/state.txt")
        if os.path.exists(project_path + "/state.txt"):
            # print("openning state")
            with open(project_path + "/state.txt", "r") as file:
                state = file.read()
                return state
        else:
            # print("No state available")
            return None

    @staticmethod
    def get_loop_idx(state_path):
        if os.path.exists(state_path + "/loop.txt"):
            with open(state_path + "/loop.txt", "r") as file:
                idx = file.read()
                return idx
        else:
            # print("No loop available")
            return -1

    @staticmethod
    def get_metrics(project_path):
        if os.path.exists(project_path +  "/metrics.json"):
            with open(project_path +  "/metrics.json", "r") as json_file:
                metrics = json.load(json_file)
            return metrics
        else:
            return None

    @staticmethod
    def get_llm_labels(project_path):
        count_1 = 0
        count_0 = 0
        if os.path.exists(project_path + "/current_sample_training.csv"):
            df = pd.read_csv(project_path + "/current_sample_training.csv")
            pos = df[df["label"] == 1]
            neg = df[df["label"] == 0]
            if not pos.empty:
                count_1 = len(pos)
            if not neg.empty:
                count_0 = len(neg)

            labels = {"1": count_1,
                    "0": count_0}
            return labels
        else:
            return None


    @staticmethod
    def get_epoch_logs(project_path, process_path, loop):
        # List all files in the directory
        log_path = process_path+"/log"
        if os.path.exists(log_path):
            if loop == 1 and os.path.exists(f"{project_path}/epoch_training.json"):
                os.remove(f"{project_path}/epoch_training.json")
            if os.path.exists(log_path+"/epoch.json"):
                with open(log_path+"/epoch.json", 'r') as file:
                    epoch_logs = json.load(file)

                if os.path.exists(f"{project_path}/epoch_training.json"):
                    with open(f"{project_path}/epoch_training.json", 'r') as file:
                        epochs = json.load(file)
                        epochs[f"{loop}"] = epoch_logs
                else:
                    epochs = {}
                    epochs[f"{loop}"] = epoch_logs

                with open(f"{project_path}/epoch_training.json", 'w') as file:
                    json.dump(epochs, file)
                return epochs
        elif os.path.exists(f"{project_path}/epoch_training.json"):
            # print(f"no epoch yet for loop {loop}")
            if loop != 1:
                with open(f"{project_path}/epoch_training.json", 'r') as file:
                    epochs = json.load(file)
                    return epochs
            else:
                os.remove(f"{project_path}/epoch_training.json")
                return None

        else:
            # print(f"Epoch logs file does not exists {log_path}")
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






