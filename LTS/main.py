import nltk
from config import parse_args
from labeling import Labeling
from preprocessing import TextPreprocessor
from lts_processing import LTS
import os

from utils import load_data_with_lda, print_summary, prepare_validation, initialize_trainer, initialize_sampler

nltk.download('punkt')

def main():
    args = parse_args()

    sampling = args.sampling
    sample_size = args.sample_size
    filter_label = args.filter_label
    balance = args.balance
    model_finetune = args.model_finetune
    labeling = args.labeling
    filename = args.filename
    model = args.model
    metric = args.metric
    validation_path = args.val_path
    validation_size = int(args.val_size)
    cluster_size = int(args.cluster_size)
    budget = int(args.budget)
    retrain = args.retrain
    baseline = args.baseline
    id = args.id


    # Load data
    preprocessor = TextPreprocessor()
    data = load_data_with_lda(filename, preprocessor, cluster_size, id)

    # Set up labeling and validation
    labeler = Labeling(label_model=labeling)
    labeler.set_model()
    validation = prepare_validation(validation_path, validation_size, data, labeler, preprocessor, id)

    # Initialize fine-tuner and sampler
    trainer = initialize_trainer(model, model_finetune, validation, id=id)
    sampler = initialize_sampler(sampling, cluster_size, id)


    if not os.path.exists(id):
        os.mkdir(id)
    # Main processing loop
    for idx in range(budget):
        LTS(sampler, data, sample_size, filter_label, trainer, labeler, filename, balance, metric, baseline, labeling, retrain, idx, id)
    # print_summary(sampler)


if __name__ == "__main__":
    main()
