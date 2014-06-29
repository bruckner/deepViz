
class Pipeline(object):
    """
    Read-only interface to CNN model
    """
    def __init__(self, layers):
        self._layers = layers
        self._layersByName = { l.name(): l for l in layers }

    def getlayer(self, name):
        return _layers_by_name[name]

class Pipe(object):
    """
    A node in a pipeline
    """
    def __init__(self, name, inputs, outputs, params):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self._params = params

    def shape(self):
        return _params.shape


