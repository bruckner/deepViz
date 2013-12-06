import sys, loaddecaf, pickle
import numpy as np

def load_data(fname):
    return np.array(pickle.load(open(x))['data'])
    
def select_image(data, id):
    return np.reshape(data[:,id], (3,32,32))

def main():
    args = loaddecaf.parse_args()
    print "Loading model: %s" % args.model
    net = loaddecaf.load_net(args.model)
    print "Showing off: %s" % net.layers.keys()
    #visualize_layer(net.layers['conv1'])
    image = load_data("/Users/sparks/Downloads/cifar-10-py-colmajor/data_batch_1")
    for m in net:
        
    
if __name__ == "__main__":
    main()