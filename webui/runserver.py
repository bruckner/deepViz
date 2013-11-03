#! /usr/bin/env python

import argparse
import os
import sys

# Add the ConvNet scripts to the import path
sys.path.append(os.path.join(os.path.dirname(__file__), "../scripts"))

from deepviz_webui import app

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, required=True)
args = parser.parse_args()

app.config["TRAINED_MODEL_PATH"] = args.model
app.run(debug=True)
