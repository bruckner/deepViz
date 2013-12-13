#! /usr/bin/env python

import argparse
import os
import sys
from tornado import autoreload
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

# Add the ConvNet scripts to the import path
sys.path.append(os.path.join(os.path.dirname(__file__), "../scripts"))

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, required=True)
parser.add_argument("--cifar", type=str, required=True)
parser.add_argument("--model-stats", type=str, required=True)
parser.add_argument("--port", type=int, default=5000)
parser.add_argument("--debug", action="store_true")
parser.set_defaults(debug=False)
args = parser.parse_args()

# Needed in order to run on a server without an X GUI:
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
pyplot.ioff()

from deepviz_webui.app import app

app.config["TRAINED_MODEL_PATH"] = args.model
app.config["CIFAR_10_PATH"] = args.cifar
app.config["MODEL_STATS_DB"] = args.model_stats
app.debug = args.debug

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(args.port)
ioloop = IOLoop.instance()
if args.debug:
    autoreload.start(ioloop)
ioloop.start()
