import itertools
import numpy as np

#This is a hack.
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../scripts"))

from utils.decaf import load_from_convnet, get_layer_dimensions, reshape_layer_for_visualization

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
    return shaped_layer[(f, c)]

def select_region(model, times=ALL, layers=ALL, filters=ALL, channels=ALL):
    #Default is to treat None as "All"
    if times is ALL:
        times = range(len(model))
    
    if layers is ALL:
        #We assume all models have the same structure.
        layers = model[0].layers.keys()
        
    if filters is ALL:
        #Choose all filters for each layer.
        filters = dict([(l,get_layer_dimensions(model[0].layers[l])[0]) for l in layers])
        
    if channels is ALL:
        #Choose all channels for each layer.
        channels = dict([(l,get_layer_dimensions(model[0].layers[l])[2]) for l in layers])
        
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
            newfilters[l] = sorted(set(channels) & set(range(nchannels)))
        channels = newchannels    
    
    #We now are sure we have a list of layer names and two dicts of layer-name/filters 
    #and layer-name/channels pairs.
    
    #Request a point for each combination of layers, filters, and channels.
    region = []
    
    for t in times:
        region[t] = {}
        for l in layers:
            region[t][l] = {}
            shaped_layer = reshape_layer_for_visualization(model[t].layers[l])
            for f in filters[l]:
                region[t][l][f] = {}
                for c in channels[l]:
                    region[t][l][f][c] = select_point(shaped_layer, f, c)
    
    return region
    
    
def select_region_query(model, args):
    times = parse_range(args.get('times', ALL))
    
    #Layers are named, so we just take the names.
    layers = args.get('layers', ALL)
    if layers:
        layers = layers.split(",")
        
    filters = parse_range(args.get('filters', ALL))
    channels = parse_range(args.get('channels', ALL))
    
    return select_region(model, times, layers, filters, channels)
    
def main(args):
    '''For testing'''
    # Add the ConvNet scripts to the import path
    
    
    from utils.decaf import load_from_convnet
    model = load_from_convnet(args[0])
    
    print select_region_query(model, {"times":"0","layers":["conv1"]})
    
if __name__ == "__main__":
    import sys
    main(sys.argv)
    
    