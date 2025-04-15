import pandas as pd
import torch
from openai import OpenAI
import pandas as pd
# import random
import json
import time

class Labeling:
    def __init__(self, label_model= "llama", model_name="meta-llama/Llama-3.3-70B-Instruct", prompt= "", batch=False):
        self.label_model = label_model
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.prompt = prompt
        self.batch = batch
        self.model_name = model_name

    def generate_prompt(self, title):
        if self.label_model == "llama":
            return self.generate_prompt_llama(title)
        elif self.label_model=="llama70":
            return self.generate_prompt_llama(title)
        elif self.label_model=="gpt":
            return self.generate_prompt_gpt(title)
        elif self.label_model=="mistral":
            return self.generate_prompt_llama(title)
        else:
            return None


    def generate_prompt_llama(self, title: str) -> str:
        return f'''{self.prompt}.
             {title}.
            Label: '''


    def generate_prompt_gpt(self, title):
        return f'''{self.prompt}.
                Input Advertisement: {title}
                Label: '''

    def set_model(self):
        # if self.label_model == "llama":
        #     from ollama import Client
        #     self.model = Client(host='https://ollama-asr498.users.hsrn.nyu.edu/')
        #     print("Using OLLAMA client")
        if self.label_model=="llama":
            self.model = OpenAI(api_key="x")
        elif self.label_model == "gpt":
            self.model = OpenAI(api_key="X")
        elif self.label_model =="mistral":
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1", device_map="auto")
            self.tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1", use_fast=False)
        elif self.label_model =="file":
            self.model = None


    def predict_animal_product(self, data: pd.DataFrame) -> pd.DataFrame:

        print(f"Predicting Animal Product with {self.label_model} model")

        # Check if the model is 'gpt' and process in batches
        if self.label_model == "gpt" and self.batch:
            self.create_batch_jsonl(data)
            predictions = self.get_gpt_batch_labels()

        else:
            # Process row by row for other models
            predictions = data.apply(self.predict_row, axis=1)
            print(len(predictions))
            print(data)

        return predictions

    def predict_row(self, row):
        """
        Predict the label for a single row based on the selected model.
        """
        label = Labeling.check_already_label(row)
        if label:
            return label
        if self.label_model == "llama":
            return self.get_llama70_label(row)
        if self.label_model == "gpt":
            return self.get_gpt_label(row)
        elif self.label_model == "mistral":
            return self.get_mistral_label(row)
        elif self.label_model == "file":
            return self.get_file_label(row)
        else:
            raise ValueError("No model selected")

    def get_gpt_batch_labels(self) -> list:
        batch_input_file = self.model.files.create(
            file=open("batch_hilts.jsonl", "rb"),
            purpose="batch"
        )
        batch_input_file_id = batch_input_file.id
        batch = self.model.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
                "description": "hilts"
            }
        )
        output_file_id = None
        print(batch)
        while output_file_id == None:
            output_file_id = self.model.batches.retrieve(batch.id).output_file_id
            if output_file_id is None:
                time.sleep(2) # limit is 100 request/min

        file_response = self.model.files.content(output_file_id)
        json_lines = file_response.text.strip().split('\n')
        json_objects = [json.loads(line) for line in json_lines]
        results = []
        for json_obj in json_objects:
            results.append(json_obj["response"]["body"]["choices"][0]["message"]["content"])
        return results

    def create_batch_jsonl(self, data: pd.DataFrame):
        prompt = data["text"].to_list()
        json_list = []

        for idx, prompt in enumerate(prompt, start=1):
            custom_id = f"request-{idx}"

            # Create the body for the request
            body = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800
            }

            json_object = {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": body
            }

            json_list.append(json_object)

        with open("batch_hilts.jsonl", "w") as file:
            for json_object in json_list:
                file.write(json.dumps(json_object) + "\n")


    def generate_inference_data(self, data, column):
        def truncate_string(s, max_length=2000):  # Adjust max_length as needed
            return s[:max_length] + '...' if len(s) > max_length else s
        if self.label_model != "file":
            examples = []
            for _, data_point in data.iterrows():
                examples.append(
                {
                    "metadeta":  data_point["metadata"],
                    "id": data_point["id"],
                    "url": data_point["url"],
                    "image_path": data_point["image_path"],
                    "label_cluster": data_point["label_cluster"],
                    "title": data_point["title"],
                    "text": self.generate_prompt(truncate_string(data_point[column])),
                }
                )
            data = pd.DataFrame(examples)
        return data

    def get_gpt_label(self, row):
        prompt = row["text"]
        response = self.model.chat.completions.create(
                model=self.model_name,
                messages=[
                    # {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.2,
            )
        return response.choices[0].message.content
        # products = ["not a relevant product", "relevant product"]
        # return random.choice(products)

    def get_llama70_label(self, row):
        prompt = row["text"]
        response = self.model.chat.completions.create(
                model=self.model_name,
                messages=[
                    # {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.2,
            )
        res = response.choices[0].message.content
        print(f"res: {res}")
        return res
        # products = ["not a relevant product", "relevant product"]
        # return random.choice(products)

    def get_mistral_label(self, row):
        prompt = row["text"]
        model_inputs = self.tokenizer([prompt], return_tensors="pt").to(self.device)
        # self.model.to(self.device)
        generated_ids = self.model.generate(**model_inputs, max_new_tokens=100, do_sample=True)
        return self.tokenizer.batch_decode(generated_ids)[0]


    def get_llama_label(self, row):
        prompt = row["text"]
        response = self.model.chat(model='llama3.1:8b-text-q8_0', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
            ])
        return response['message']['content'].lower()
        # products = ["not a relevant product", "relevant product"]
        # return random.choice(products)

    def get_file_label(self, row):
        raise NotImplementedError()

    @staticmethod
    def check_already_label(row):
        return None
        # labeled_data = pd.read_csv("all_labeled_data_gpt.csv")
        # if row["id"] in labeled_data["id"].values:
        #     # Retrieve the label for the corresponding id
        #     print("data already labeled")
        #     label = labeled_data.loc[labeled_data["id"] == row["id"], "label"].values[0]
        #     return label
        # else:
        #     return None


