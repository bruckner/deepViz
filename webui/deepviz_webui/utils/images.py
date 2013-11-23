"""
Utility functions for working with image data.
"""
from cStringIO import StringIO
from math import ceil, floor
import svgwrite


def normalize(imagedata):
    # No -= or /= to avoid accidentally modifying the input:
    imagedata = imagedata - imagedata.min()
    imagedata = imagedata / imagedata.max()
    return imagedata


def generate_svg_filter_map(num_filters, ksize, num_cols, scale=1, padding_px=1):
    """
    Returns an SVG that functions like an HTML image map.
    """
    num_rows = int(ceil((1.0 * num_filters / num_cols)))
    max_cols = int(floor(1.0 * num_filters / num_rows))
    img_width  = ((max_cols - 1) * padding_px) + (ksize * max_cols)
    img_height = ((num_rows - 1) * padding_px) + (ksize * num_rows)
    filter_img_size = (ksize * scale, ksize * scale)
    svg_size = (img_width * scale, img_height * scale)

    svg = svgwrite.Drawing(size=svg_size)
    svg.add_stylesheet("/static/svg-styles.css", "noname")
    for row in range(num_rows):
        for col in range(num_cols):
            x = col * (ksize + padding_px) * scale
            y = row * (ksize + padding_px) * scale
            svg.add(svg.rect(insert=(x, y), size=filter_img_size, fill="none"))
    out = StringIO()
    svg.write(out)
    return out.getvalue()