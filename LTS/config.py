import argparse

def parse_args():
    parser = argparse.ArgumentParser(prog="Sampling fine-tuning", description='Perform Sampling and fine tune')
    parser.add_argument('-sampling', type=str, help="Name of sampling method")
    parser.add_argument('-sample_size', type=int, help="Sample size")
    parser.add_argument('-filter_label', type=bool, help="Use model clf results to filter data")
    parser.add_argument('-balance', type=bool, help="Balance positive and negative samples")
    parser.add_argument('-model_finetune', type=str, help="Model base for fine tuning")
    parser.add_argument('-labeling', type=str, help="Model to be used for labeling or file if label already on file")
    parser.add_argument('-filename', type=str, help="The initial file to be used")
    parser.add_argument('-model', type=str, help="The type of model to be fine-tuned")
    parser.add_argument('-metric', type=str, help="The type of metric to be used for baseline")
    parser.add_argument('-val_path', type=str, help="Path to validation")
    parser.add_argument('-val_size', type=int, help="Size of validation data if no validation is provided")
    parser.add_argument('-cluster_size', type=str, help="Path to validation")
    parser.add_argument('-budget', type=int, help="Number of times to do the loop")
    parser.add_argument('-retrain', type=bool, help="retrain or keep the best model to fine tune")
    parser.add_argument('-baseline', type=float, help="The initial baseline metric")
    parser.add_argument('-id', type=str, help="The id of the process")



    return parser.parse_args()
