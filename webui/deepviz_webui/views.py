from deepviz_webui.app import app, cached
from deepviz_webui.globalresources import get_image_corpus, get_model, get_models
from deepviz_webui.utils.decaf import reshape_layer_for_visualization, \
    get_layer_dimensions
from deepviz_webui.utils.images import normalize, generate_svg_filter_map
from deepviz_webui.utils.misc import mapterminals
from deepviz_webui.selectmodels import select_region_query
from deepviz_webui.viewdecorators import pylabToJsonBase64PNGs, pylabToPNG

from decaf.util.visualize import show_multiple, show_channels, show_single

from flask import render_template, request, Response, jsonify

from cStringIO import StringIO
import json
import networkx as nx
import numpy as np
from PIL import Image


@app.route("/imagecorpus/<filename>")
def get_image_from_corpus(filename):
    corpus = get_image_corpus()
    image = corpus.get_image(filename)
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
    corpus = get_image_corpus()
    results = list(corpus.find_images(query))
    return Response(json.dumps(results), mimetype="application/json")




@app.route("/checkpoints/<int:checkpoint>/layers/<layername>/overview.png")
@pylabToPNG
def layer_overview_png(checkpoint, layername):
    model = get_models()[checkpoint]
    layer = model.layers[layername]
    (num_filters, ksize, num_channels) = get_layer_dimensions(layer)
    reshaped = reshape_layer_for_visualization(layer, combine_channels=(num_channels == 3))
    ncols = 1 if num_channels == 3 else num_channels
    return show_multiple(normalize(reshaped), ncols=ncols)


def run_model_on_corpus_image(checkpoint, imagename, output_blobs):
    # This is based on decaf's "imagenet" script:
    corpus = get_image_corpus()
    image = corpus.get_image(imagename + ".png")
    model = get_models()[checkpoint]
    arr = np.array(image.getdata()).reshape(1, 32, 32, 3).astype(np.float32)
    return model.predict(data=arr, output_blobs=output_blobs)


@app.route("/checkpoints/<int:checkpoint>/layers/<layername>/apply/<imagename>/overview.png")
@pylabToPNG
def convolved_layer_overview_png(checkpoint, imagename, layername):
    """
    Visualizes the applications of a layer's filters to an image.
    """
    # This is based on decaf's "imagenet" script:
    classified = run_model_on_corpus_image(checkpoint, imagename, [layername + "_cudanet_out"])
    layer = classified[layername + "_cudanet_out"]
    if layername.startswith("fc") and layername.endswith("_neuron"):
        # For fcN, the layer's shape is (1, N).
        return show_single(layer[0])
    else:
        layer = layer[0, :, :, :]  # shape this into a (k, k, num_filters) array
        return show_channels(layer)


@app.route("/checkpoints/<int:checkpoint>/predict/<imagename>")
@cached()
def predict_for_image(checkpoint, imagename):
    """
    Return predictions for a particular image.
    """
    features = run_model_on_corpus_image(checkpoint, imagename, ["probs_cudanet_out"])
    class_number_probs = enumerate(features["probs_cudanet_out"][0])
    corpus = get_image_corpus()
    class_label_probs = [(corpus.label_names[l], float(p)) for (l, p) in class_number_probs]
    return Response(json.dumps(dict(class_label_probs)), mimetype="application/json")


@app.route("/layers/<layername>/overview.svg")
def layer_overview_svg_container(layername):
    """
    Generates transparent SVGs that are overlaid on filter views
    to enable mouse interactions.
    """
    model = get_models()[0]
    layer = model.layers[layername]
    (num_filters, ksize, num_channels) = get_layer_dimensions(layer)
    ncols = 1 if num_channels == 3 else num_channels
    scale = int(request.args.get('scale', 1))
    svg = generate_svg_filter_map(num_filters * ncols, ksize, ncols, scale)
    return Response(svg, mimetype="image/svg+xml")
    
    
@app.route("/checkpoints/<checkpoints>/layers/<layernames>/filters/<filters>/channels/<channels>/overview.json")
@pylabToJsonBase64PNGs
def layer_filters_channels_overview_json(checkpoints, layernames, filters, channels):
    region = select_region_query(get_models(), times=checkpoints, layers=layernames, filters=filters, channels=channels)
    images = mapterminals(show_multiple, region)
    #todo need to apply show_multiple to each one of these.
    return images
    
    
@app.route("/checkpoints/<checkpoints>/layers/<layernames>/filters/<filters>/channels/<channels>/apply/<imagename>/overview.json")
@pylabToJsonBase64PNGs
def layer_filters_channels_image_json(checkpoints, layernames, filters, channels, imagename):
    corpus = get_image_corpus()
    image = corpus.get_image("%s.png" % imagename)
    arr = np.array(image.getdata()).reshape(1, 32, 32, 3).astype(np.float32)
    
    out = select_region_query(get_models(), times=checkpoints, layers=layernames, filters=filters, channels=channels, image=arr)
    #todo need to apply show_multiple to each one of these.
    images = mapterminals(show_multiple, out)
    return images


@app.route("/layers.svg")
@cached()
def layer_dag_to_svg():
    model = get_model()
    graph = nx.DiGraph()
    for layer in model.layers:
        graph.add_node(layer['name'], layer_attributes=layer)
    for layer in model.layers:
        for inputLayer in layer.get("inputLayers", []):
            graph.add_edge(inputLayer['name'], layer['name'])
    pydot_graph = nx.to_pydot(graph)
    pydot_graph.set_rankdir("LR")
    svg = pydot_graph.create_svg(prog="dot")
    return Response(svg, mimetype="image/svg+xml")


@app.route("/")
def index():
    context = {
        'num_timesteps' : len(get_models()),
        'model' : get_models()[0],
    }
    return render_template('index.html', **context)
