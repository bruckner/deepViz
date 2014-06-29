"""
Resources that are shared across all requests.
"""
from deepviz_webui.app import app
from deepviz_webui.imagecorpus import CIFAR10ImageCorpus
from deepviz_webui.model_stats_db import ModelStatsDB
from models import *
import os

# TODO: These objects should be made thread-safe.

_model_stats_db = None
_models = None
_image_corpus = None

class BrokenByCaffeError(Exception):
    pass

def get_image_corpus():
    # TODO Fix this for Imagenet
    raise BrokenByCaffeError('get_image_corpus: Needs to be fixed for ImageNet')
    global _image_corpus
    if _image_corpus is None:
        _image_corpus = CIFAR10ImageCorpus(app.config["CIFAR_10_PATH"])
    return _image_corpus

def get_models():
    global _models
    if _models is None:
        _models = load_models()
    return _models

def load_models():
    caffe_path = app.config["CAFFE_SPEC_PATH"]
    if caffe_path == None:
        return load_decaf_models()
    else:
        return load_caffe_models(caffe_path)

def load_decaf_models():
    model_path = app.config["TRAINED_MODEL_PATH"]
    checkpoints = sorted(os.listdir(model_path))
    paths = [os.path.join(model_path, c) for c in checkpoints]
    return [DecafModel.load(p) for p in paths]

def load_caffe_models(spec_path):
    model_path = app.config["TRAINED_MODEL_PATH"]
    checkpoints = sorted(os.listdir(model_path))
    paths = [os.path.join(model_path, c) for c in checkpoints]
    return [CaffeModel.load(spec_path, p) for p in paths]

def get_model_stats_db():
    # TODO Fix this for Caffe
    raise BrokenByCaffeError('MODEL_STATS_DB needs to be fixed for Caffe/Imagenet')
    global _model_stats_db
    if _model_stats_db is None:
        _model_stats_db = ModelStatsDB(app.config["MODEL_STATS_DB"])
    return _model_stats_db

