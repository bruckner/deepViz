from deepviz_webui import app

from flask import render_template


_model = None

def get_model():
    global _model
    if _model is None:
        from shownet import ShowConvNet
        from gpumodel import IGPUModel
        # This code is adapted from gpumodel.py and shownet.py
        load_dic = IGPUModel.load_checkpoint(app.config["TRAINED_MODEL_PATH"])
        op = ShowConvNet.get_options_parser()
        old_op = load_dic["op"]
        old_op.merge_from(op)
        op = old_op
        _model = ShowConvNet(op, load_dic)
    return _model


@app.route("/")
def index():
    context = {
        'model' : get_model(),
    }
    return render_template('index.html', **context)
