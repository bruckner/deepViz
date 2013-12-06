import itertools
import numpy as np

#This is a hack.
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../scripts"))

from utils.decaf import load_from_convnet, get_layer_dimensions, reshape_layer_for_visualization, flatten_filters
from decaf.util.visualize import show_channels

#This may be the worst thing I have ever done.
ALL=None

#From http://darklaunch.com/2012/11/05/python-parse-range-and-parse-group-range
def parse_range(astr):
    """
    Return a range list given a string.
    e.g. parse_range('1,3,5-12') returns [1, 3, 5, 6, 7, 8, 9, 10, 11, 12]
    """
    if astr is ALL:
        return ALL
    
    result = set()
    for part in astr.split(','):
        x = part.split('-')
        result.update(range(int(x[0]), int(x[-1]) + 1))
    return sorted(result)
    

def select_point(shaped_layer, f, c):
    return shaped_layer[f,:,:,c]


def select_region(model, times=ALL, layers=ALL, filters=ALL, channels=ALL, apply_prediction=None):
    #Default is to treat None as "All"
    if times is ALL:
        times = range(len(model))
    
    if layers is ALL:
        #We assume all models have the same structure.
        layers = model[0].layers.keys()
        
    if filters is ALL:
        #Choose all filters for each layer.
        filters = dict([(l,range(get_layer_dimensions(model[0].layers[l])[0])) for l in layers])
        
    if channels is ALL:
        #Choose all channels for each layer.
        channels = dict([(l,range(get_layer_dimensions(model[0].layers[l])[2])) for l in layers])
        
    #Do something reasonable if filters is a list.
    if isinstance(filters, list):
        newfilters = {}
        for l in layers:
            (nfilters, ksize, nchannels) = get_layer_dimensions(model[0].layers[l])
            newfilters[l] = sorted(set(filters) & set(range(nfilters)))
        filters = newfilters
    
    #Do something reasonable if channels is a list.
    if isinstance(channels, list):
        newchannels = {}
        for l in layers:
            (nfilters, ksize, nchannels) = get_layer_dimensions(model[0].layers[l])
            newchannels[l] = sorted(set(channels) & set(range(nchannels)))
        channels = newchannels    
    
    #We now are sure we have a list of layer names and two dicts of layer-name/filters 
    #and layer-name/channels pairs.
    
    #Request a point for each combination of layers, filters, and channels.
    print "Times: %s" % times
    print "Layers: %s" % layers
    print "Filters: %s" % filters
    print "Channels: %s" % channels
    
    #Initialize output.
    region = dict([(t,{}) for t in times])
    
    for t in times:
        #If the user asks for a prediction, apply it to the whole set of models and persist the intermediate results.
        if apply_prediction is not None:
            #FIXME: This assumes that output blobs will have the same name as the user selected layers, 
            #with "_cudanet_out" at the end of them. 
            blobs = ["%s_cudanet_out" % l for l in layers]
            predicted_model = model[t].predict(data=apply_prediction, output_blobs=blobs)
            print predicted_model
            
        for l in layers:
            region[t][l] = {}
            
            if apply_prediction is not None:
                
                #FIXME
                shaped_layer = predicted_model["%s_cudanet_out" % l]
                shaped_region = shaped_layer[:,:,:,filters[l]]
                flat_region = flatten_filters(shaped_region, len(filters[l]), 1, shaped_layer.shape[1])
                
                #Todo - need to figure out the shape of a prediction and then map that to our output image shape.
            else:
                shaped_layer = reshape_layer_for_visualization(model[t].layers[l], preserve_dims=True)
            
                #I believe I am somehow abusing numpy's indexing here, but this seems to work.
                shaped_region = shaped_layer[filters[l],:,:,:][:,:,:,channels[l]]
                flat_region = flatten_filters(shaped_region, len(filters[l]), len(channels[l]), shaped_layer.shape[1])
            
            region[t][l] = flat_region
            
            #This was here when we wanted one image per filter.
            # for f in filters[l]:
            #     region[t][l][f] = {}
            #     for c in channels[l]:
            #         region[t][l][f][c] = select_point(shaped_layer, f, c)
    
    #Region shoudl be a dict of {time: {layer: image}}
    return region
    
    
def select_region_query(model, args):
    times = parse_range(args.get('times', ALL))
    
    #Layers are named, so we just take the names.
    layers = args.get('layers', ALL)
    if layers:
        layers = layers.split(",")
        
    filters = parse_range(args.get('filters', ALL))
    channels = parse_range(args.get('channels', ALL))
    
    apply_prediction=args.get('image',None)
    
    return select_region(model, times, layers, filters, channels, apply_prediction)



def main(args):
    '''For testing'''
    # Add the ConvNet scripts to the import path
    from utils.decaf import load_from_convnet
    
    #Take the directory and run through it to get a single "model"
    model_path = args[1]
    checkpoints = sorted(os.listdir(model_path))
    model = [load_from_convnet(os.path.join(model_path, c)) for c in checkpoints]
    
    #print select_region_query(model, {"times":"0","layers":"conv1"})
    #print select_region_query(model, {"times":"0-4", "layers":"conv1,conv2", "filters":"1-5", "channels":"1,3"})
    from imagecorpus import CIFAR10ImageCorpus
    corpus = CIFAR10ImageCorpus("cifar-10-py-colmajor")
    image = corpus.get_image("dog_s_001795.png")
    arr = np.array(image.getdata()).reshape(1, 32, 32, 3).astype(np.float32)
    print model[7].blobs.keys()
    print model[0].layers.keys()
    blobs = set(model[0].blobs) & set(["%s_cudanet_out" % s for s in model[0].layers.keys()])
    print model[7].predict(data=arr, output_blobs=blobs)
    
    print select_region_query(model, {"times":"0-4", "layers":"conv1,conv2", "filters":"1-5", "channels":"1,3", "image":arr})
    
    print
    
if __name__ == "__main__":
    import sys
    main(sys.argv)
    
    