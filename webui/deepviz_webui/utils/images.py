"""
Utility functions for working with image data.
"""


def normalize(imagedata):
    # No -= or /= to avoid accidentally modifying the input:
    imagedata = imagedata - imagedata.min()
    imagedata = imagedata / imagedata.max()
    return imagedata