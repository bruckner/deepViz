import os
import logging
import cPickle as pickle
import numpy as np
from multiprocessing import Pool
import time


_log = logging.getLogger("ModelStatsDB")
_shared_data = None


def _process_model(x):
    # Import is here so that we don't need to have the convnet scripts
    # on PYTHONPATH in order to interact with already-built databases.
    from deepviz_webui.utils.decaf import load_from_convnet
    (timestep, model_filename) = x
    (directory, image_data, image_classes, num_classes) = _shared_data
    _log.info("Processing model for timestep %i" % timestep)
    model = load_from_convnet(model_filename)
    stats = ModelStats.create(model, image_data, image_classes, num_classes)
    stats.save(os.path.join(directory, str(timestep)))


class ModelStatsDB(object):
    """
    Persistent database of model statistics.
    """
    def __init__(self, directory):
        self._directory = directory
        self._stats = {}

    def get_stats(self, timestep):
        if timestep not in self._stats:
            stats_filename = os.path.join(self._directory, str(timestep))
            if not os.path.isfile(stats_filename):
                raise ValueError("Don't have statistics for timestep %i" % timestep)
            else:
                self._stats[timestep] = ModelStats.load(stats_filename)
        return self._stats[timestep]

    @classmethod
    def create(cls, directory, model_filenames, image_data, image_classes, num_classes):
        """
        Warning: this `create` method is not threadsafe!
        """
        global _shared_data
        _shared_data = (directory, image_data, image_classes, num_classes)
        pool = Pool(2)  # TODO: make pool size configurable
        pool.map(_process_model, enumerate(model_filenames), 1)
        _shared_data = None
        return ModelStatsDB(directory)


class ModelStats(object):
    """
    Provides access to statistics gathered while applying a model
    to an image corpus.
    """

    def __init__(self, confusion_matrix, images_by_classification, probs_by_image, top_k_images_by_cluster):
        self._confusion_matrix = confusion_matrix
        self._images_by_classification = images_by_classification
        self._probs_by_image = probs_by_image
        self._top_k_images_by_cluster = top_k_images_by_cluster

    @property
    def confusion_matrix(self):
        """
        Return a confusion matrix, where entry `C[i, j]` gives the number
        of images of true class `i` that were classified as class `j`.
        """
        return self._confusion_matrix

    @property
    def images_by_classification(self):
        """
        Returns a matrix of lists, where entry `A[i, j]` gives the ids
        of images of true class `i` that were classified as class `j`.
        """
        return self._images_by_classification

    @property
    def probs_by_image(self):
        """
        Returns a list of class probabilities, indexed by image id.
        """
        return self._probs_by_image
        
    @property
    def top_k_images_by_cluster(self):
        """
        Returns a matrix of image ids, where entry `A[i, j]` gives the id
        of an image in cluster `i` that is the `j`'th closest to the cluster centroid
        by Euclidean distance.
        """
        return self._top_k_images_by_cluster

    @classmethod
    def load(cls, filename):
        with open(filename) as f:
            return pickle.load(f)

    def save(self, filename):
        """
        Persist the database to a file.
        """
        with open(filename, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def create(cls, model, image_data, image_classes, num_classes, num_clusters=30, num_neighbors=20):
        """
        Create a new ModelStatsDatabase by applying a trained model
        to a collection of images.
        """
        BATCH_SIZE = 2000
        image_data = image_data.astype(np.float32)
        confusion_matrix = np.zeros((num_classes, num_classes))
        images_by_classification = [[[] for _ in xrange(num_classes)] for _ in xrange(num_classes)]
        probs_by_image = None
        fc10_features = []

        for chunk_start in xrange(0, len(image_data), BATCH_SIZE):
            images = image_data[chunk_start:chunk_start + BATCH_SIZE]
            start_time = time.time()
            outputs = model.predict(data=images, output_blobs=["probs_cudanet_out", "fc10_cudanet_out"])
            end_time = time.time()
            _log.info("Processed batch of %i images in %f seconds" %
                     (len(images), end_time - start_time))
            probs = outputs["probs_cudanet_out"]
            if probs_by_image is None:
                probs_by_image = probs
            else:
                probs_by_image = np.concatenate((probs_by_image, probs))
            for (offset, image_probs) in enumerate(probs):
                image_num = chunk_start + offset
                true_class = image_classes[image_num]
                predicted_class = np.argmax(image_probs)
                confusion_matrix[true_class][predicted_class] += 1
                images_by_classification[true_class][predicted_class].append(image_num)
            
            fc10_features.append(outputs["fc10_cudanet_out"])
        
        #Code to do top k clusters    
        _log.info("Starting clustering")
        fc10_features = np.vstack(fc10_features)
        _log.info("Features have shape: %s" % str(fc10_features.shape))
        _log.info("Starting K-means")
        from sklearn.cluster import KMeans
        km = KMeans(n_clusters = num_clusters)
        fit = km.fit(fc10_features)
        
        #For each point, get its distance from its cluster center.
        _log.info("Computing distances.")
        dists = np.linalg.norm(fc10_features - fit.cluster_centers_[fit.labels_] , ord=2, axis=1)
        
        #Build a matrix of kNN by point.
        top_k_images_by_cluster = [[] for _ in xrange(num_clusters)]
        for k in xrange(0, num_clusters):
            #Get indexes of elements with this label.
            inds = np.where(fit.labels_ == k)
            
            #Reorder indexes according to closest distance.
            tab = np.column_stack((inds[0],dists[inds]))
            topNeighbors = tab[tab[:,1].argsort()][0:num_neighbors,0]
            top_k_images_by_cluster[k] = map(int, list(topNeighbors))
        
        return ModelStats(confusion_matrix, images_by_classification, probs_by_image, top_k_images_by_cluster)
