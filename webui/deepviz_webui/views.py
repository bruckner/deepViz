from deepviz_webui import app, cached

from flask import render_template, request, Response

from cStringIO import StringIO
from gpumodel import IGPUModel
import networkx as nx
import numpy as np
from PIL import Image
from shownet import ShowConvNet
import os

import loaddecaf

_models = None
_model = None  # TODO: remove this once the graph is drawn from Decaf


def get_models():
    global _models
    if _models is None:
        model_path = app.config["TRAINED_MODEL_PATH"]
        checkpoints = sorted(os.listdir(model_path))
        _models = [loaddecaf.load_net(os.path.join(model_path, c)) for c in checkpoints]

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

@app.route("/checkpoints/<int:checkpoint>/layers/<layer>/overview.svg")
def layer_overview(checkpoint, layer):
    from selectmodel import select_region, get_svg
    svg = select_region(get_models(), times=checkpoint)[layer]
    return Response(svg, mimetype="image/svg+xml")


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


@cached()
def get_image_ready_filters(layer_name, input_idx=0):
    # This code is adapted from ShowCovNet
    model = get_model()
    layer_names = [l['name'] for l in model.layers]
    layer = model.layers[layer_names.index(layer_name)]
    input_idx = 0
    filters = layer['weights'][input_idx]
    if layer['type'] == 'fc': # Fully-connected layer
        num_filters = layer['outputs']
        channels = 1  # TODO: should be set from layer data.
    if layer['type'] in ('conv', 'local'): # Conv layer
        num_filters = layer['filters']
        channels = layer['filterChannels'][input_idx]
        if layer['type'] == 'local':
            filters = filters.reshape((layer['modules'], layer['filterPixels'][input_idx] * channels, num_filters))
            filters = filters.swapaxes(0,1).reshape(channels * layer['filterPixels'][input_idx], num_filters * layer['modules'])
            num_filters *= layer['modules']
    filters = filters.reshape(channels, filters.shape[0]/channels, filters.shape[1])
    # Make sure you don't modify the backing array itself here -- so no -= or /=
    filters = filters - filters.min()
    filters = filters / filters.max()
    return (filters, num_filters, channels)


@app.route("/layers/<layer_name>/filters/<int:filter_index>.png")
@cached()
def filter_image(layer_name, filter_index):
    # This code is adapted from ShowCovNet
    (filters, num_filters, channels) = get_image_ready_filters(layer_name)
    num_colors = filters.shape[0]
    filter_size = int(np.sqrt(filters.shape[1]))
    chosen_filter = filters[:,:,filter_index]
    combine_chans = request.args.get('combine_channels', True)
    if combine_chans != "false" and channels == 3:
        # Combine the channels:
        pic = chosen_filter.reshape((3, filter_size, filter_size)).swapaxes(0, 2).swapaxes(0, 1)
    else:
        # Plot the channels side-by-side:
        pic = np.concatenate([chosen_filter[c,:].reshape((filter_size, filter_size)) for c in xrange(num_colors)], axis=1)
    rescaled = (255.0 * pic).astype(np.uint8)
    png_buffer = StringIO()
    image = Image.fromarray(rescaled)
    scale = int(request.args.get('scale', 1))
    if scale != 1:
        (width, height) = image.size
        image = image.resize((width * scale, height * scale), Image.NEAREST)
    image.save(png_buffer, format="PNG")
    png = png_buffer.getvalue()
    png_buffer.close()
    return Response(png, mimetype="image/png")


@app.route("/layers/<layer_name>/filters/")
def view_all_filters(layer_name):
    context = {
        'num_filters' : get_image_ready_filters(layer_name)[1],
        'layer_name' : layer_name,
    }
    return render_template('view_all_filters.html', **context)


@app.route("/")
def index():
    context = {
        'num_timesteps' : len(get_models()),
        'model' : get_models()[0],
    }
    return render_template('index.html', **context)
