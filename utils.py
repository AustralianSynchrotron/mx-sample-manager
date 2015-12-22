from functools import wraps
from flask import request, render_template, current_app, json
from bson import json_util

def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint \
                    .replace('.', '_').replace('_', '/') + '.twig.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)
        return decorated_function
    return decorator

def jsonify(*args, **kwargs):
    return current_app.response_class(json.dumps(dict(*args, **kwargs), default=json_util.default),
                              mimetype='application/json')

def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])

    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']