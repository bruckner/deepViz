from deepviz_webui import app, cached

from flask import render_template, Response

from cStringIO import StringIO
from gpumodel import IGPUModel
import networkx as nx
from shownet import ShowConvNet
import xml.etree.ElementTree as ElementTree


_model = None


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
        'model' : get_model(),
    }
    return render_template('index.html', **context)
