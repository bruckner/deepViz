from __future__ import absolute_import
from decaf.util import visualize, translator
from gpumodel import IGPUModel
from math import sqrt


def load_from_convnet(filename):
    cudaconv_net = IGPUModel.load_checkpoint(filename)
    layers = cudaconv_net["model_state"]["layers"]
    data_layer = [l for l in layers if l['name'] == 'data'][0]
    data_consumer = [l for l in layers if data_layer in l.get('inputLayers', [])][0]
    input_dim = int(sqrt(data_consumer['imgPixels'][0]))  # The width/height of the square images
    input_channels = data_consumer['channels'][0]  # The number of channels in the input images
    return translator.translate_cuda_network(layers,
                                             {'data': (input_dim, input_dim, input_channels)})


def get_layer_dimensions(layer):
    num_filters = layer.spec['num_kernels']
    ksize = layer.spec['ksize']  # The length of one side of the square filter
    num_channels = layer.param()[0].data().shape[0]/ (ksize * ksize)
    return (num_filters, ksize, num_channels)


def flatten_filters(filters, num_filters, num_channels, ksize):
    return filters.swapaxes(2,3).swapaxes(1,2).reshape(num_filters * num_channels, ksize, ksize)


def reshape_layer_for_visualization(layer, combine_channels=False, preserve_dims=False, prediction=None):
    """
    Reshape a decaf layer's data to prepare it for visualization.
    This function performs no normalization.

    If `combine_channels` is True and this layer's filters have three channels,
    the output will be a numpy array with one row per filter, where each row is
    a square matrix of (r, g, b) triples.

    Otherwise, we output each filter channel as its own matrix, one per row,
    for a total of `num_filters` * `num_channels` rows.
    """
    (num_filters, ksize, num_channels) = get_layer_dimensions(layer)

    # Here, we have a two dimensional array, where each row represents one filter
    # and the columns are the filter's values laid out channel-by-channel.
    # For example, given 32 RGB 5x5 image filters, this would be a 32 x 75
    # array, where each row is [red0, ... red25, green0, ..., green24, blue0, ..., blue24]
    if prediction is not None:
        filters = prediction.T
    else:
        filters = layer.param()[0].data().T

    # Here, we reshape each row into a filter-shaped matrix, where each entry contains
    # the values of that pixel in each channel.  For our 5x5 RGB example,
    # the shape would be (32, 5, 5, 3)
    filters = filters.reshape(num_filters, ksize, ksize, num_channels)

    if combine_channels:
        return filters
    else:
        # Display each channel separately - we may want to preserve dimensions for future subsetting.
        if preserve_dims:
            return filters
        return flatten_filters(filters, num_filters, num_channels, ksize)
        
    