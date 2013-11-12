#For this part to work, you need to first make sure decaf is installed or at least on your
#PYTHONPATH. (export PYTHONPATH=.:/path/to/decaf-release)

import argparse
import pickle
from matplotlib import pyplot
from decaf.util import visualize
from decaf.util import translator


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    return parser.parse_args()
    
def load_net(fname):
    with open(fname) as f:
        cudaconv_net = pickle.load(f)
        layers = cudaconv_net["model_state"]["layers"]
        
        #Note, data dimensions are hardcoded here - not sure we have that info in the cudaconv object?
        decafnet = translator.translate_cuda_network(layers, {'data': (32, 32, 3)})
        return decafnet
        
def visualize_layer(l):
    filters = l.param()[0].data()
    _ = visualize.show_multiple(filters.T)
    pyplot.title('First layer Filters')
    pyplot.show()

def main():
    args = parse_args()
    print "Loading model: %s" % args.model
    net = load_net(args.model)
    print "Showing off: %s" % net.layers.keys()
    visualize_layer(net.layers['conv1'])
    
if __name__ == "__main__":
    main()