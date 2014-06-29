import numpy as np
import re
import networkx as nx
import _caffe
from gpumodel import IGPUModel
from shownet import ShowConvNet
from decaf.util import translator
from decaf.layers import *

class ConvnetModel(object):
    """
    An interface for reading and visualizing the contents of convnet models
    """
    def __init__(self, model):
        self.model = model

    def graph(self):
        g = nx.DiGraph()
        for layer in self.model.layers:
            g.add_node(layer['name'], layer_attributes=layer)
        for layer in self.model.layers:
            for inputLayer in layer.get("inputs", []):
                g.add_edge(self.model.layers[inputLayer]['name'], layer['name'], 
                        label=self.model.layers[inputLayer]['outputs'])
        return g

    @staticmethod
    def load(path):
        load_dic = IGPUModel.load_checkpoint(path)
        op = ShowConvNet.get_options_parser()
        old_op = load_dic["op"]
        old_op.merge_from(op)
        op = old_op
        return ConvnetModel(ShowConvNet(op, load_dic))

class DecafLayer(object):
    def __init__(self, layer):
        self.layer = layer
        self.shape = self._shape()

    def for_viz(self, combine=False):
        """
        Reshape a decaf layer's data to prepare it for visualization.
        This function performs no normalization.
        """
        if self.shape == None:
            raise 'Cannot visualize layer type: %s' % (type(self.filter),)
        (num_filters, ksize, num_channels) = self.shape

        # filters is 2D matrix with rows = filters, cols = params blcoked by
        # channel, e.g., [red0, ... redN, green0, ... greenN, blue0, ... ]
        filters = self.layer.param()[0].data().T

        # Fold each filter into 3D
        filters = filters.reshape(num_filters, ksize, ksize, num_channels)

        if not combine:
            # Display each channel separately
            filters = filters.swapaxes(2,3).swapaxes(1,2)
            filters = filters.reshape(num_filters * num_channels, ksize, ksize)
        return filters

    def _shape(self):
        if isinstance(self.layer, InnerProductLayer):
            ksize = np.sqrt(self.layer._weight.data().shape[0])
            num_filters = self.layer._num_output
            num_channels = 1
        elif isinstance(self.layer, ConvolutionLayer):
            num_filters = self.layer.spec['num_kernels']
            ksize = self.layer.spec['ksize']  # The length of one side of the square filter
            num_channels = self.layer.param()[0].data().shape[0]/ (ksize * ksize)
        else:
            return None
        return (num_filters, ksize, num_channels)

class DecafModel(object):
    """
    An interface to Decaf models
    """
    def __init__(self, model, oshapes):
        self.model = model
        self.output_shapes = oshapes
        self.layers = {n: DecafLayer(model.layers[n]) for n in model.layers}

    def graph(self):
        g = self.model.graph
        h = nx.DiGraph()
        for name in self.model.layers:
            h.add_node(name)
        for e in g.edges():
            if e[0][-12:] == '_cudanet_out':
                u = e[0][:-12]
                v = e[1] if e[1][-8:] != '_flatten' else e[1][:-8] # XXX Hacky
                h.add_edge(u, v, label=self._outputs(u))
        for n in h.nodes():
            if 'flatten' in n:
                h.remove_node(n)
        root = [n for n in h.nodes() if len(h.predecessors(n)) == 0][0]
        h.add_node('data')
        h.add_edge('data', root, label=self._outputs('data'))
        return h

    def _outputs(self, layername):
        return reduce(lambda x, y: x * y, self.output_shapes[layername], 1)

    @staticmethod
    def load(path):
        return DecafModel(*DecafModel.load_from_convnet(path))

    @staticmethod
    def load_from_convnet(filename):
        cudaconv_net = IGPUModel.load_checkpoint(filename)
        layers = cudaconv_net["model_state"]["layers"]
        data_layer = [l for l in layers if l['name'] == 'data'][0]
        data_consumer = [l for l in layers 
                if data_layer in l.get('inputLayers', [])][0]
        input_dim = int(np.sqrt(data_consumer['imgPixels'][0]))  
        input_channels = data_consumer['channels'][0]  
        data_shape = (input_dim, input_dim, input_channels)
        shapes = {'data': data_shape}
        model = translator.translate_cuda_network(layers, shapes)
        return model, shapes

class CaffeLayer(object):
    def __init__(self, layer, name):
        self.layer = layer
        self.name = name
        self.type = self._type()
        try:
            self._blob = layer.blobs[0]
            self.shape = self._shape()
        except:
            self.shape = None

    def for_viz(self, combine=False, offset=0, n=100):
        if self.shape == None:
            raise 'Cannot visualize non-parametric layer'
        (num_filters, ksize, num_channels) = self.shape
        filters = self._blob.data
        if self.type == 'fc':
            filters = filters.reshape(num_filters, ksize)[offset:offset+n]
            padding = np.ceil(np.sqrt(ksize))**2 - ksize
            if padding > 0:
                filters = np.pad(filters, [(0, 0), (0, padding)], mode='constant')
        elif self.type == 'conv':
            filters = filters[offset:offset+n]
            num_filters = n
            if combine:
                filters = filters.swapaxes(1,2).swapaxes(2,3)
            else:
                filters = filters.reshape(num_filters * num_channels, ksize, ksize)
        print 'FILTERS SHAPE = ', filters.shape
        return filters

    def outputs(self):
        if self.shape == None:
            return ' '
        return self._blob.count

    def _type(self):
        return re.search('^[a-z]+', self.name).group()

    def _shape(self):
        num_filters = self._blob.num
        if self.type == 'fc':
            num_filters = self._blob.width
            num_channels = 1
            ksize = self._blob.height
        elif self.type == 'conv':
            ksize = self._blob.width
            if self._blob.width != self._blob.height:
                print 'Attention: CaffeLayer filters are not square!'
            num_channels = self._blob.channels
        else:
            return None
        return (num_filters, ksize, num_channels)

class CaffeModel(object):
    """
    An interface to Caffe trained models
    """
    def __init__(self, model):
        self.model = model
        self.layers = {l.name: CaffeLayer(l, l.name) for l in model.layers}

    def graph(self):
        g = nx.DiGraph()
        for layername in self.layers:
            g.add_node(layername)
        for i in xrange(1, len(self.model.layers)):
            u = self.model.layers[i-1].name
            v = self.model.layers[i].name
            g.add_edge(u, v, label=self.layers[u].outputs())
        return g

    @staticmethod
    def load(specpath, modelpath):
        return CaffeModel(_caffe.CaffeNet(specpath, modelpath))

