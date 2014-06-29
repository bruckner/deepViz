import math
from deepviz_webui.app import app, cached
from deepviz_webui.globalresources import get_image_corpus, get_models, \
        get_model_stats_db
from deepviz_webui.utils import images
from deepviz_webui.utils.misc import mapterminals
from deepviz_webui.selectmodels import select_region_query
from deepviz_webui.viewdecorators import pylabToJsonBase64PNGs, pylabToPNG, browserCacheIndefinitely

from models import *

from decaf.util.visualize import show_multiple, show_channels, show_single

from flask import render_template, request, Response, jsonify

from cStringIO import StringIO
import networkx as nx
import numpy as np
from PIL import Image


@app.route("/imagecorpus/<int:image_num>.png")
@browserCacheIndefinitely
def get_image_from_corpus(image_num):
    try:
        # TODO Fix this to work with imagenet
        corpus = get_image_corpus()
        image = corpus.get_image(image_num)
    except e:
        image = np.eye(32)
    scale = int(request.args.get('scale', 1))
    if scale != 1:
        (width, height) = image.size
        image = image.resize((width * scale, height * scale), Image.NEAREST)
    png_buffer = StringIO()
    image.save(png_buffer, format="PNG")
    png = png_buffer.getvalue()
    png_buffer.close()
    return Response(png, mimetype="image/png")


@app.route("/imagecorpus/search/<query>")
def image_corpus_query(query):
    # TODO Fix this for imagenet
    try:
        corpus = get_image_corpus()
    except e:
        return jsonify([('foo', 1)])
    # TODO: limit the number of search results, or paginate them.
    results = dict(corpus.find_images(query))
    return jsonify(results)


@app.route("/checkpoints/<int:checkpoint>/confusionmatrix")
def confusion_matrix(checkpoint):
    # TODO Fix this for imagenet (uses both get_image_corpus and get_model_stats_db)
    return 'Broken pending caffe/imagenet support', 500
    stats = get_model_stats_db().get_stats(checkpoint)
    confusion_matrix = stats.confusion_matrix
    json_matrix = list(list(float(y) for y in x) for x in confusion_matrix)
    label_names = get_image_corpus().label_names
    sample_images = stats.images_by_classification
    SAMPLE_IMAGE_LIMIT = 9
    sample_images = [[x[:SAMPLE_IMAGE_LIMIT] for x in y] for y in sample_images]
    return jsonify({'confusionmatrix': json_matrix, 'labelnames': label_names,
                    'sampleimages': sample_images})

@app.route("/checkpoints/<int:checkpoint>/clusters")
def clustered_images(checkpoint):
    # TODO Fix this for caffe/imagenet (model stats db)
    return 'Broken pending caffe/imagenet stats DB support', 500
    top_k = get_model_stats_db().get_stats(checkpoint).top_k_images_by_cluster
    clusters = list({'topkimages': list(int(y) for y in x)} for x in top_k)
    return jsonify({'clusters': clusters})

@app.route("/checkpoints/<int:checkpoint>/layers/<layername>/overview.png")
#@browserCacheIndefinitely
@pylabToPNG
def layer_overview_png(checkpoint, layername):
    # XXX get_models
    model = get_models()[checkpoint]
    layer = model.layers[layername]
    (num_filters, ksize, num_channels) = layer.shape
    ncols = 6 if num_channels in  (1, 3) else num_channels
    reshaped = images.normalize(layer.for_viz(combine=(num_channels==3)))
    return show_multiple(reshaped, ncols=ncols)


def run_model_on_corpus_image(checkpoint, imagenum, output_blobs):
    # TODO Fix for caffe/imagenet
    return 'Broken pending imagenet/caffe support', 500
    # This is based on decaf's "imagenet" script:
    corpus = get_image_corpus()
    image = corpus.get_all_images_data()[imagenum] - corpus.get_mean()
    model = get_models()[checkpoint]
    arr = image.astype(np.float32)
    return model.predict(data=arr, output_blobs=output_blobs)


@app.route("/checkpoints/<int:checkpoint>/layers/<layername>/apply/<int:imagenum>/overview.png")
@browserCacheIndefinitely
@pylabToPNG
def convolved_layer_overview_png(checkpoint, imagenum, layername):
    """
    Visualizes the applications of a layer's filters to an image.
    """
    # This is based on decaf's "imagenet" script:
    classified = run_model_on_corpus_image(checkpoint, imagenum, [layername + "_cudanet_out"])
    layer = classified[layername + "_cudanet_out"]
    if layername.startswith("fc") and layername.endswith("_neuron"):
        # For fcN, the layer's shape is (1, N).
        return show_single(layer[0])
    else:
        layer = layer[0, :, :, :]  # shape this into a (k, k, num_filters) array
        return show_channels(layer)


@app.route("/checkpoints/<int:checkpoint>/predict/<int:imagenum>")
@cached()
def predict_for_image(checkpoint, imagenum):
    """
    Return predictions for a particular image.
    """
    # TODO Fix for caffe/imagenet
    return 'Broken pending imagenet/caffe support', 500
    features = run_model_on_corpus_image(checkpoint, imagenum, ["probs_cudanet_out"])
    class_number_probs = enumerate(features["probs_cudanet_out"][0])
    corpus = get_image_corpus()
    class_label_probs = [{'class': corpus.label_names[l], 'prob': float(p)} for (l, p) in class_number_probs]
    return jsonify({'predictions': class_label_probs})


@app.route("/layers/<layername>/overview.svg")
@browserCacheIndefinitely
def layer_overview_svg_container(layername):
    # XXX get_models
    """
    Generates transparent SVGs that are overlaid on filter views
    to enable mouse interactions.
    """
    model = get_models()[0]
    layer = model.layers[layername]
    (num_filters, ksize, num_channels) = layer.shape
    ncols = 6 if num_channels in  (1, 3) else num_channels
    nrows = int(math.ceil(float(num_filters) / 6)) if num_channels in (1, 3) else 100
    scale = int(request.args.get('scale', 1))
    svg = images.generate_svg_filter_map(nrows * ncols, ksize, ncols, scale)
    return Response(svg, mimetype="image/svg+xml")
    
    
@app.route("/checkpoints/<checkpoints>/layers/<layernames>/filters/<filters>/channels/<channels>/overview.json")
#@pylabToJsonBase64PNGs
def layer_filters_channels_overview_json(checkpoints, layernames, filters, channels):
    # TODO Fix for caffe compat
    # XXX get_models
    return 'Broken pending caffe/imagenet stats DB support', 500
    models = [m.model for m in get_models()]
    region = select_region_query(models, times=checkpoints, layers=layernames, filters=filters, channels=channels)
    images = region
    return images
 

@app.route("/checkpoints/<checkpoints>/layers/<layernames>/filters/<filters>/channels/<channels>/apply/<int:imagenum>/overview.json")
@pylabToJsonBase64PNGs
def layer_filters_channels_image_json(checkpoints, layernames, filters, channels, imagenum):
    # TODO Fix for caffe/imagenet
    return 'Broken pending imagenet/caffe support', 500
    corpus = get_image_corpus()
    image = corpus.get_image(imagenum)
    arr = np.array(image.getdata()).reshape(1, 32, 32, 3).astype(np.float32)
    out = select_region_query(get_models(), times=checkpoints, layers=layernames, filters=filters, channels=channels, image=arr)
    images = out
    return images


@app.route("/layers.svg")
@browserCacheIndefinitely
@cached()
def layer_dag_to_svg():
    graph = get_models()[0].graph()
    pydot_graph = nx.to_pydot(graph)
    pydot_graph.set_rankdir("LR")
    svg = pydot_graph.create_svg(prog="dot")
    return Response(svg, mimetype="image/svg+xml")


@app.route("/")
def index():
    context = {'num_timesteps' : len(get_models())}
    return render_template('index.html', **context)

