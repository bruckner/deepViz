"""
Decorators for Flask views.
"""
import base64
from cStringIO import StringIO
from deepviz_webui.utils.misc import mapterminals
from flask import request, Response
from functools import wraps
from matplotlib import pyplot, cm
from PIL import Image
import json


def _image_to_png(image_data):
    png_buffer = StringIO()
    pyplot.imsave(png_buffer, image_data, cmap=cm.gray, format='png')
    png_buffer.reset()
    image = Image.open(png_buffer)
    scale = int(request.args.get('scale', 1))
    if scale != 1:
        (width, height) = image.size
        image = image.resize((width * scale, height * scale), Image.NEAREST)
    png_buffer = StringIO()
    image.save(png_buffer, format="PNG")
    png = png_buffer.getvalue()
    png_buffer.close()
    return png


def pylabToPNG(view_func):
    """
    Decorator for creating views that return pylab images as PNGs.
    Adds querystring options for performing scaling.
    """
    def _decorator(*args, **kwargs):
        image_data = view_func(*args, **kwargs)
        png = _image_to_png(image_data)
        return Response(png, mimetype="image/png")
    return wraps(view_func)(_decorator)


def pylabToJsonBase64PNGs(view_func):
    """
    Decorator for creating views that return pylab images as a JSON object filled with base64 encoded pngs.
    Adds querystring options for performing scaling.
    """
    def _decorator(*args, **kwargs):
        images_data = view_func(*args, **kwargs)
        transformer = lambda buf: "data:image/png;base64,%s" % base64.b64encode(_image_to_png(buf)).decode("ascii")
        images_data = mapterminals(transformer, images_data)

        return Response(json.dumps(images_data), mimetype="application/json")
    return wraps(view_func)(_decorator)