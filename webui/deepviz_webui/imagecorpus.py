import cPickle
import os
from math import sqrt
import numpy as np
from PIL import Image

from decaf.util.translator import conversions

class CIFAR10ImageCorpus(object):
    """
    Class for loading images from the Python version of the CIFAR-10
    corpus: http://www.cs.toronto.edu/~kriz/cifar-10-py-colmajor.tar.gz
    """
    def __init__(self, root_folder):
        with open(os.path.join(root_folder, "batches.meta")) as metafile:
            meta = cPickle.load(metafile)
            self.label_names = meta['label_names']
        batches = sorted(os.listdir(root_folder))[1:]  # Skip batches.meta.
        self._image_data = None
        self._image_labels = None
        self._filenames = None
        for batch in batches:
            with open(os.path.join(root_folder, batch)) as batchfile:
                data = cPickle.load(batchfile)
                # data.keys() == ['batch_label', 'labels', 'data', 'filenames']
                if self._image_data is None:
                    offset = 0
                    self._image_data = data['data'].T  # colmajor version
                    self._image_labels = data['labels']
                    self._filenames = data["filenames"]
                else:
                    offset = self._image_data.shape[0]
                    self._image_data = np.concatenate((self._image_data, data['data'].T))
                    self._image_labels.extend(data['labels'])
                    self._filenames.extend(data["filenames"])
        ksize = sqrt(len(self._image_data[0]) / 3)
        self._image_data = conversions.imgs_cudaconv_to_decaf(self._image_data, ksize, 3)

    def find_images(self, query):
        """
        Return the names of images that match a query
        """
        for (image_num, image_name) in enumerate(self._filenames):
            if query in image_name:
                yield (image_name, image_num)

    def get_image(self, image_num):
        return Image.fromarray(self._image_data[image_num])

    def get_all_images_data(self):
        return self._image_data

