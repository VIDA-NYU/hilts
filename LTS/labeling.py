import pandas as pd
import torch
from openai import OpenAI
import pandas as pd


class Labeling:
    def __init__(self, label_model= "llama", prompt= ""):
        self.label_model = label_model
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.prompt = prompt

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
        if self.task == "animal":
            return f'''{self.prompt}
                    Input: {title}
                    Label: '''

    def set_model(self):
        # if self.label_model == "llama":
        #     from ollama import Client
        #     self.model = Client(host='https://ollama-asr498.users.hsrn.nyu.edu/')
        #     print("Using OLLAMA client")
        if self.label_model=="llama":
            self.model = OpenAI(api_key="x", base_url="https://api.deepinfra.com/v1/openai")
        elif self.label_model == "gpt":
            self.model = OpenAI(api_key="")
        elif self.label_model =="mistral":
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1", device_map="auto")
            self.tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1", use_fast=False)
        elif self.label_model =="file":
            self.model = None


    def predict_animal_product(self, row):
        print(f"Prediction Animal with {self.model}")
        label = Labeling.check_already_label(row)
        if label:
            return label
        # if self.label_model == "llama":
        #     return self.get_llama_label(row)
        elif self.label_model == "llama":
            return self.get_llama70_label(row)
        elif self.label_model == "gpt":
            return self.get_gpt_label(row)
        elif self.label_model =="mistral":
            return self.get_mistral_label(row)
        elif self.label_model == "file":
            return self.get_file_label(row)
        else:
            raise ValueError("No model selected")


    def generate_inference_data(self, data, column):
        def truncate_string(s, max_length=2000):  # Adjust max_length as needed
            return s[:max_length] + '...' if len(s) > max_length else s

        # Define a function to create metadata JSON
        # def get_metadata(row):
        #     return {"url": row["url"], "price": 10, "currency": "USD", "seller": "Juliana Store"}



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
                model="gpt-4",
                messages=[
                    # {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.2,
            )
        return response.choices[0].message.content

    def get_llama70_label(self, row):
        prompt = row["text"]
        print(row)
        response = self.model.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct",
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


