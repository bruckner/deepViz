import numpy as n
import numpy.random as nr

def makew(name, idx, shape, params=None):
    stddev, mean = float(params[0]), float(params[1])
    rows, cols = shape
    return n.array(mean + stddev * nr.randn(rows, cols), dtype=n.single)

def makeb(name, shape, params=None):
    stddev = float(params[0])
    return n.array(stddev * nr.randn(shape[0], shape[1]), dtype=n.single)

