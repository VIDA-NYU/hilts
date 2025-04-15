import nltk
from .config import parse_args
from .labeling import Labeling
from .preprocessing import TextPreprocessor
from .lts_processing import LTS
import os
from .state_manager import write_state
from .utils import create_clustered_data, prepare_validation, initialize_trainer, initialize_sampler

nltk.download('punkt')

def initialize_LTS(project_path):

    args = parse_args(project_path)

    sampling = args.get("sampling")
    sample_size = args.get("sample_size")
    labeling = args.get("labeling")
    metric = args.get("metric")
    validation_path = args.get("val_path")
    validation_size = int(args.get("validation_size"))
    cluster_size = int(args.get("cluster_size"))
    cluster_algorithm = args.get("cluster")
    budget = args.get("budget")
    baseline = args.get("baseline")
    prompt = args.get("task_prompt")
    budget_value = int(args.get("bugetValue"))
    model_finetune = args.get("model_finetune")
    model_name = args.get("model_name")
    # model_init = args.get("model_init")

    # Load data
    preprocessor = TextPreprocessor()

    data = create_clustered_data(preprocessor, cluster_algorithm, cluster_size, project_path)

    # Set up labeling and validation
    labeler = Labeling(label_model=labeling,model_name=model_name, prompt=prompt)
    labeler.set_model()

    validation = prepare_validation(validation_path, validation_size, data, labeler, preprocessor, project_path)

    # Initialize fine-tuner and sampler
    write_state(project_path, "Loading Base Model")

    trainer = initialize_trainer("text", model_finetune, validation, project_path=project_path)

    sampler = initialize_sampler(sampling, cluster_size, project_path)

    return args, sampler, data, trainer, labeler


    # # if not os.path.exists(id):
    # #     os.mkdir(id)
    # # Main processing loop
    # if budget == "trainingSize":
    #     loops = int(budget_value/sample_size)
    #     for idx in range(loops):
    #         result = LTS(sampler, data, sample_size, True, trainer, labeler, "filename", True, metric, baseline, labeling, idx, project_id)
    # elif budget=="metric":
    #     generate = True
    #     while generate:
    #         result = LTS(sampler, data, sample_size, True, trainer, labeler, "filename", True, metric, baseline, labeling, idx, project_id)
    #         if result[f"eval_{metric}"] < budget_value:
    #             generate = False
    # # print_summary(sampler)

