"""
Resources that are shared across all requests.
"""
from deepviz_webui.app import app
from deepviz_webui.imagecorpus import CIFAR10ImageCorpus
from deepviz_webui.model_stats_db import ModelStatsDB
from deepviz_webui.utils.decaf import load_from_convnet
from gpumodel import IGPUModel
from shownet import ShowConvNet
import os

# TODO: These objects should be made thread-safe.

_model_stats_db = None
_models = None
_model = None  # TODO: remove this once the graph is drawn from Decaf
_image_corpus = None


def get_image_corpus():
    global _image_corpus
    if _image_corpus is None:
        _image_corpus = CIFAR10ImageCorpus(app.config["CIFAR_10_PATH"])
    return _image_corpus


def get_models():
    global _models
    if _models is None:
        model_path = app.config["TRAINED_MODEL_PATH"]
        checkpoints = sorted(os.listdir(model_path))
        _models = [load_from_convnet(os.path.join(model_path, c)) for c in checkpoints]
    return _models


# TODO: remove this once the graph is drawn from Decaf:
def get_model():
    global _model
    if _model is None:
        # This code is adapted from gpumodel.py and shownet.py
        load_dic = IGPUModel.load_checkpoint(app.config["TRAINED_MODEL_PATH"])
        op = ShowConvNet.get_options_parser()
        old_op = load_dic["op"]
        old_op.merge_from(op)
        op = old_op
        _model = ShowConvNet(op, load_dic)
    return _model


def get_model_stats_db():
    global _model_stats_db
    if _model_stats_db is None:
        _model_stats_db = ModelStatsDB(app.config["MODEL_STATS_DB"])
    return _model_stats_db