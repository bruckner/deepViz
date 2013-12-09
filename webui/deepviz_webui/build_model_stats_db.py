"""
Training script usage:

    PYTHONPATH=. python deepviz_webui/build_model_stats_db.py --model ../models/ConvNet__2013-11-20_15.03.37 --cifar ../cifar-10-py-colmajor --num-classes 10 --output-dir stats_db
"""
import argparse
import os
import sys
import logging

if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger("ModelStatsDB").setLevel(logging.INFO)
    # Add the ConvNet scripts to the import path
    sys.path.append(os.path.join(os.path.dirname(__file__), "../../scripts"))

from deepviz_webui.imagecorpus import CIFAR10ImageCorpus
from deepviz_webui.model_stats_db import ModelStatsDB


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--cifar", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--num-classes", type=int, required=True)
    args = parser.parse_args()
    if not os.path.isdir(args.output_dir):
        raise ValueError("Output path '%s' does not exist!" % args.output_dir)

    checkpoints = sorted(os.listdir(args.model))
    model_filenames = (os.path.join(args.model, str(c)) for c in checkpoints)
    corpus = CIFAR10ImageCorpus(args.cifar)
    ModelStatsDB.create(args.output_dir, model_filenames, corpus.get_all_images_data(),
                        corpus._image_labels, args.num_classes)