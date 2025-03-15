import multiprocessing
import os
import re
import pandas as pd
import numpy as np
from LTS.main import initialize_LTS
from LTS.lts_processing import LTS
import json


class LTSManager:
    def __init__(self, projectID: str):
        self.project_id = projectID
        self.status = False
        self.process = None
        # self.label_hilts = args.get("labeling")

    def train_model(self, label_hilts):
        # label_hilts = self.label_hilts

        project_id = self.project_id
        metrics_path = f"data/{project_id}/metrics.json"
        process_id = self.process.pid
        state_path = f"data/{project_id}/{process_id}/"

        args, sampler, data, trainer, labeler = initialize_LTS(project_id)

        budget = args.get("budget")
        budget_value = int(args.get("bugetValue"))
        if os.path.exists(metrics_path):
            with open(metrics_path, "r") as json_file:
                result_json = json.load(json_file)
        if budget == "trainingSize":
            loops = int(budget_value/args.get("sample_size"))
            for idx in range(loops):
                process_path = f"data/{project_id}/{process_id}/stop.txt"
                if os.path.exists(process_path):
                    print("Training stopped!")
                    os.remove(process_path)
                    self.process.terminate()
                    break
                if idx == 0 and label_hilts =="file":
                    label = label_hilts
                else:
                    label = args.get("labeling")
                res =  LTS(sampler, data, args.get("sample_size"), True, trainer, labeler, "filename", True, args.get("metric"), args.get("baseline"), label, idx, project_id, state_path)
                result = {
                        "step": [idx],
                        "precision": [res["eval_precision"]],
                        "recall": [res["eval_recall"]],
                        "f1_score": [res["eval_f1"]],
                        "accuracy": [res["eval_accuracy"]]
                    }
                if not os.path.exists(metrics_path):
                    with open(metrics_path, "w") as json_file:
                        json.dump(result, json_file, indent=4)
                else:
                    with open(metrics_path, "r") as json_file:
                        result_json = json.load(json_file)
                    result_json["precision"].append(res["eval_precision"])
                    result_json["recall"].append(res["eval_recall"])
                    result_json["f1_score"].append(res["eval_f1"])
                    result_json["accuracy"].append(res["eval_accuracy"])
                    result_json["step"].append(idx)
                    with open(metrics_path, "w") as json_file:
                        json.dump(result_json, json_file, indent=4)

                # data = pd.read_csv(f"data/{project_id}/current_sample_training.csv")
                # data["relevant"] = np.where(data["label"]==1, "animal origin", "not animal origin")
                # global db
                # for _, row in data.iterrows():
                #     db.add_label(image_path=row["image_path"], label=row["relevant"], table="relevant")
                # time.sleep(120)

        elif budget=="metric":
            generate = True
            idx = 0
            while generate:
                process_path = f"data/{project_id}/{os.getpid()}/stop.txt"
                if os.path.exists(process_path):
                    print("Training stopped!")
                    os.remove(process_path)
                    print("Training stopped!")
                    break
                result = LTS(sampler, data, args.get("sample_size"), True, trainer, labeler, "filename", True, args.get("metric"), args.get("baseline"), args.get("labeling"), idx, project_id)
                if result[f'eval_{args.get("metric")}'] >= budget_value:
                    generate = False
                idx+=1
                result = {
                    "step": idx,
                    "precision": result["eval_precision"],
                    "recall": result["eval_recall"],
                    "f1_score": result["eval_f1"],
                    "accuracy": result["eval_accuracy"]
                }
                # training_results.append(result)

                # Emit the training result after each step
                # socketio.emit('my response', result)
                # time.sleep(120)

        # if not os.path.exists(f"data/{project_id}/stop.txt"):
        #     return()
        #     # socketio.emit('my response', {'message': 'Training complete!'})
        # else:
        #     return()


    def start_training(self, label_hits):
        """
        Starts the model training in a separate process.
        :param args: Arguments for model training
        """
        # Start the training in a new process
        self.process = multiprocessing.Process(target=self.train_model, args=(label_hits,))
        self.process.start()
        self.status = self.process.is_alive()

        # Save the process ID to a file # DO I NEED THIS?
        process_path = f"data/{self.project_id}/{self.process.pid}"
        os.mkdir(process_path, exist_ok=True)
        with open(f"{process_path}/training_process_id.txt", "w") as f:
            f.write(f"{self.project_id}: {self.process.pid}\n")

        print(f"Training process started with PID: {self.process.pid}")

        # Return the training process
        return self.process


    def get_status(self, processId):
        project_path = f"data/{self.project_id}/"
        process_path = f"data/{self.project_id}/{processId}/"

        if os.path.exists(process_path + "status.json"):
            with open(process_path + "status.json", "r") as json_file:
                status = json.load(json_file)
        else:
            status = {
                "lts_status": "",
                "lts_state": "",
                "stats": {
                    "llm_labels": [],
                    "epochs": [],
                    "training_metrics": []
                }
            }

        labels = self.get_llm_labels(project_path)
        epochs = self.get_epoch_logs(project_path)
        metrics = self.get_metrics(project_path)

        status["lts_status"] = self.process.is_alive()
        status["lts_state"] = self.get_LTS_state(process_path)

        if labels:
            status["stats"]["llm_labels"].append(labels)
        if epochs:
            status["stats"]["epochs"] = [epochs]
        if metrics:
            status["stats"]["training_metrics"].append(metrics)

        with open(process_path + "status.json", "w") as json_file:
            json.dump(status, json_file, indent=4)

        return status


    def stop_LTS(self, processId):
        p_process = f"data/{self.project_id}/{processId}/stop.txt"
        with open(p_process, "r") as f:
            f.write("stop")


    @staticmethod
    def get_LTS_state(state_path):
        if os.path.exists(state_path + "state.json"):
            with open(state_path, "r") as json_file:
                state = json.load(json_file)
                return state
        else:
            print("No state available")


    @staticmethod
    def get_metrics(project_path):
        if os.path.exists(project_path +  "metrics.json"):
            with open(project_path +  "metrics.json", "r") as json_file:
                metrics = json.load(json_file)
            return metrics
        else:
            return None

    @staticmethod
    def get_llm_labels(project_path):
        count_1 = 0
        count_0 = 0
        if os.path.exists(project_path + "current_sample_training.csv"):
            df = pd.read_csv(project_path + "current_sample_training.csv")
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
    def get_epoch_logs(project_path):
        # List all files in the directory
        log_path = project_path+"log"
        files = [f for f in os.listdir(log_path) if f.endswith('.txt') and 'epoch_' in f]

        files.sort(key=lambda f: float(f.split('_')[1].split('.')[0]))  # Sort by the epoch number (e.g., 1.0, 2.0, etc.)

        if len(files) > 1:
            previous_file = files[-2]  # The second-to-last file
        else:
            return None  # If there are not enough files to get the previous one

        previous_file_path = os.path.join(log_path, previous_file)
        with open(previous_file_path, 'r') as file:
            file_content = file.read()

        try:
            epoch_logs = json.loads(file_content)  # Parse the content as JSON
            return epoch_logs
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {previous_file}: {e}")
            return None


    # @staticmethod
    # def process_status(pid):
    #     try:
    #         process = psutil.Process(pid)
    #         # Check if process is running
    #         process_status = process.status()

    #         # If process status is 'running', then it's actively running
    #         if process_status == psutil.STATUS_RUNNING:
    #             return "running"
    #         else:
    #             return "not running"

    #     except psutil.NoSuchProcess:
    #         return "not running"
    #     except psutil.AccessDenied:
    #         return "Access denied to check process status"
    #     except psutil.ZombieProcess:
    #         return "not running"
    #     except TypeError:
    #         return "not running"





