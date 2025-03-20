import multiprocessing
import os
import pandas as pd
import numpy as np
from LTS.main import initialize_LTS
from LTS.lts_processing import LTS
import json
import shutil
from .search import VectorDB


class LTSManager:
    def __init__(self, projectID: str, labeldb: VectorDB):
        self.project_id = projectID
        self.status = False
        self.process = None
        self.labeldb = labeldb
        # self.label_hilts = args.get("labeling")

    def train_model(self, label_hilts):
        # label_hilts = self.label_hilts

        project_id = self.project_id
        metrics_path = f"data/{project_id}/metrics.json"
        process_id = self.process.pid
        state_path = f"data/{project_id}/{process_id}/"
        stop_path = f"data/{project_id}/{process_id}/stop.txt"
        epoch_path= f"data/{project_id}/epoch_training.json"

        print(f"processid: {process_id}")

        args, sampler, data, trainer, labeler = initialize_LTS(project_id, state_path, label_hilts)

        budget = args.get("budget")
        budget_value = int(args.get("bugetValue"))
        if os.path.exists(metrics_path):
            with open(metrics_path, "r") as json_file:
                result_json = json.load(json_file)
        if budget == "trainingSize":
            loops = int(budget_value/args.get("sample_size"))
            for idx in range(loops):
                with open(state_path + "loop.txt", "w") as f:
                    f.write(str(idx+1))
                    log_path = f"{state_path}log/"
                self.remove_dirc(log_path)
                if os.path.exists(stop_path):
                    print(f"Removing Stop file {stop_path}")
                    os.remove(stop_path)
                    os.remove(epoch_path)
                    print("Training stopped!")
                    return # End of LTS process
                if idx == 0 and label_hilts =="file":
                    label = label_hilts
                else:
                    label = args.get("labeling")
                res =  LTS(sampler, data, args.get("sample_size"), True, trainer, labeler, "filename", True, args.get("metric"), args.get("baseline"), label, idx, project_id, state_path)

                csvpath =f"data/{project_id}/current_sample_training.csv"
                if os.path.exists(csvpath):
                    df = pd.read_csv(csvpath)
                    image_paths = df["image_path"].to_list()
                    label_llm = ["animal origin" if label == 1 else "not animal origin" for label in df["label"].to_list()]
                    for path, labelllm in zip(image_paths, label_llm):
                        self.labeldb.add_label(image_path=path,label= labelllm, table="relevant")

                if res:
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
                else:
                    if os.path.exists(stop_path):
                        print(f"Removing Stop file {stop_path}")
                        os.remove(stop_path)
                    print("LTS Finished!")
                    return # End of LTS process

        # TODO
        # elif budget=="metric":
        #     generate = True
        #     idx = 0
        #     while generate:
        #         process_path = f"data/{project_id}/{os.getpid()}/stop.txt"
        #         if os.path.exists(process_path):
        #             print("Training stopped!")
        #             os.remove(process_path)
        #             print("Training stopped!")
        #             break
        #         result = LTS(sampler, data, args.get("sample_size"), True, trainer, labeler, "filename", True, args.get("metric"), args.get("baseline"), args.get("labeling"), idx, project_id)
        #         if result[f'eval_{args.get("metric")}'] >= budget_value:
        #             generate = False
        #         idx+=1
        #         result = {
        #             "step": idx,
        #             "precision": result["eval_precision"],
        #             "recall": result["eval_recall"],
        #             "f1_score": result["eval_f1"],
        #             "accuracy": result["eval_accuracy"]
        #         }
                # training_results.append(result)

                # Emit the training result after each step
                # socketio.emit('my response', result)
                # time.sleep(120)

        # if not os.path.exists(f"data/{project_id}/stop.txt"):
        #     return()
        #     # socketio.emit('my response', {'message': 'Training complete!'})
        # else:
        #     return()


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

        # Save the process ID to a file # DO I NEED THIS?
        process_path = f"data/{self.project_id}/{self.process.pid}"
        project_path = f"data/{self.project_id}/"
        os.makedirs(process_path, exist_ok=True)
        with open(f"{process_path}/training_process_id.txt", "w") as f:
            f.write(f"{self.project_id}: {self.process.pid}\n")

        # Return the training process
        return self.process

    def get_status(self):
        project_path = f"data/{self.project_id}/"
        process_path = f"data/{self.project_id}/{self.process_id}/"
        status = {
            "loop": 1,
            "lts_status": "",
            "lts_state": "",
            "stats": {
                "llm_labels": [],
                "epochs": {},
                "training_metrics": {}
            }
        }
        loop = self.get_loop_idx(process_path)

        labels = self.get_llm_labels(project_path)
        metrics = self.get_metrics(project_path)

        epochs = self.get_epoch_logs(project_path, process_path, loop)

        status["loop"] = loop
        status["lts_status"] = self.process.is_alive()
        status["lts_state"] = self.get_LTS_state(process_path)

        if labels:
            status["stats"]["llm_labels"].append(labels)
        if epochs:
            status["stats"]["epochs"] = epochs
        if metrics:
            status["stats"]["training_metrics"]= metrics

        if not status["lts_status"]:
            self.remove_dirc(process_path) ## remove process folder after process is done

        return status


    def stop_LTS(self):
        p_process = f"data/{self.project_id}/{self.process_id}/stop.txt"
        with open(p_process, "w") as f:
            f.write("stop")


    @staticmethod
    def get_LTS_state(state_path):
        if os.path.exists(state_path + "state.txt"):
            with open(state_path + "state.txt", "r") as file:
                state = file.read()
                return state
        else:
            print("No state available")

    @staticmethod
    def get_loop_idx(state_path):
        if os.path.exists(state_path + "loop.txt"):
            with open(state_path + "loop.txt", "r") as file:
                idx = file.read()
                return idx
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
    def get_epoch_logs(project_path, process_path, loop):
        # List all files in the directory
        log_path = process_path+"log"
        if os.path.exists(log_path):
            files = [f for f in os.listdir(log_path) if f.endswith('.json') and 'epoch_' in f]
            if len(files) >0:
                files.sort(key=lambda f: float(f.split('_')[1].split('.')[0]))  # Sort by the epoch number (e.g., 1.0, 2.0, etc.)

                if len(files) > 1:
                    previous_file = files[-1]  # The second-to-last file
                else:
                    return None  # If there are not enough files to get the previous one

                previous_file_path = os.path.join(log_path, previous_file)

                with open(previous_file_path, 'r') as file:
                    epoch_logs = json.load(file)

                if os.path.exists(f"{project_path}epoch_training.json"):
                    with open(f"{project_path}epoch_training.json", 'r') as file:
                        epochs = json.load(file)
                        epochs[f"{loop}"] = epoch_logs
                else:
                    epochs = {}
                    epochs[f"{loop}"] = epoch_logs

                with open(f"{project_path}epoch_training.json", 'w') as file:
                    json.dump(epochs, file)

                return epochs
        else:
            print(f"Epoch logs file does not exists {log_path}")
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






