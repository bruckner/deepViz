def mapterminals(f, d):
    """
    Map a value to all terminal items of a nested object.
    Has the nice property of maintaining its input's shape.
    """
    if isinstance(d, dict):
        return dict([(k, mapterminals(f, v)) for k,v in d.iteritems()])
    if isinstance(d, list):
        return [mapterminals(f, v) for v in d]
    else:
        return f(d)