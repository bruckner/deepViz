#For this part to work, you need to first make sure decaf is installed or at least on your
#PYTHONPATH. (export PYTHONPATH=.:/path/to/decaf-release)

import argparse
from matplotlib import pyplot
from decaf.util import visualize
from decaf.util import translator
from gpumodel import IGPUModel
import numpy as np
import time


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    return parser.parse_args()
    
def load_net(fname):
    cudaconv_net = IGPUModel.load_checkpoint(fname)
    layers = cudaconv_net["model_state"]["layers"]
    
    #Note, data dimensions are hardcoded here - not sure we have that info in the cudaconv object?
    decafnet = translator.translate_cuda_network(layers, {'data': (32, 32, 3)})
    return decafnet
        
def visualize_layer(l):
    print l.param()
    if len(l.param()) < 1:
        return None
    filters = l.param()[0].data()
    _ = visualize.show_multiple(filters.T)
    return _
    
    
#Returns the decaf viz for an arbitrary layer.
#Infers shape and size from the layer info.
#Produces results as small multiples of kernels (with position encoding filters and channels).
def visualize_complex_layer(l):
    #Should probably just be checking if layer is a convolution.
    if len(l.param()) < 1 or 'num_kernels' not in l.spec:
        return None
    
    nfilters = l.spec['num_kernels']
    ksize = l.spec['ksize']
    channels = l.param()[0].data().shape[0]/(ksize*ksize)
    
    # make the right filter shape
    filters = l.param()[0].data()
    filters = filters.T.reshape(nfilters, ksize, ksize, channels)
    filters = filters.swapaxes(2,3).swapaxes(1,2).reshape(nfilters*channels, ksize, ksize)
    _ = visualize.show_multiple(filters, ncols=channels)
    return _

def main():
    args = parse_args()
    print "Loading model: %s" % args.model
    net = load_net(args.model)
    print "Showing off: %s" % net.layers.keys()
    visualize_layer(net.layers['conv1'])
    time.sleep(5)
    #feat = net.feature('conv1_cudanet_out')#[0,::-1, :, ::3]
    
    #visualize.show_channels(feat)
    
if __name__ == "__main__":
    main()
