from flask import Flask, request
from werkzeug.contrib.cache import SimpleCache
from functools import wraps


cache = SimpleCache()


# From http://flask.pocoo.org/docs/patterns/viewdecorators/
def cached(timeout=5 * 60, key='view/%s'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % request.url
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator


app = Flask(__name__)
import deepviz_webui.views