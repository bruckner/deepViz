import loaddecaf, sys, os
from matplotlib import pyplot, cm
import numpy as np
import StringIO


"""
This module serves as the backend query interface to query models and get image objects.

All methods expect a "model" object as input, and we assume that models have a time dimension, and
each time point has a layers associated with it, each of which consists of filters.

Queries are supported with a filtering syntax. The default filter for all layers is None
"""

#Converts results of decaf viz to an svg.
def get_svg(dat, format='svg'):
    if dat is None:
        return None
        
    imgdata = StringIO.StringIO()
    print dat
    pyplot.imsave(imgdata, dat, cmap = cm.gray, format=format)
    #print np.array(dat).shape
    #print np.array(dat).shape[::-1]
    #pyplot.imsave("stuff%d.png" % i, dat, cmap = cm.gray)
    imgdata.seek(0)
    return imgdata.buf 

#Entry point for API. Right now just a stub but returns enough info for a useful viz.
def select_region(model, times=None, layers=None, filters=None):
    if times is not None:
        result = dict([(l,loaddecaf.visualize_complex_layer(model[times].layers[l])) for l in model[times].layers.keys()])
        result = dict([(k,get_svg(v)) for k,v in result.items()])
    else:
        result = [[loaddecaf.visualize_complex_layer(m.layers[l]) for l in m.layers.keys()] for m in model]
    return result
    
def main(args):
    inp = args
    models = [loaddecaf.load_net("%s/%s" % (args[1], f)) for f in os.listdir(args[1])]
    x = select_region(models, 7)
    print result
    
if __name__ == "__main__":
    main(sys.argv)