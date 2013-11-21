#! /usr/bin/env python

import argparse
import os
import sys
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

# Add the ConvNet scripts to the import path
sys.path.append(os.path.join(os.path.dirname(__file__), "../scripts"))

from deepviz_webui import app

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, required=True)
args = parser.parse_args()

app.config["TRAINED_MODEL_PATH"] = args.model
app.debug = True

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(5000)
IOLoop.instance().start()
