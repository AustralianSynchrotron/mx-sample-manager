from flask_mongokit import MongoKit
from flask_pymongo import PyMongo
from flask_vbl import VBL
from flask_beamline import Beamline
from functools import wraps

db = MongoKit()
mongo = PyMongo()
vbl = VBL()
beamline = Beamline()


def beamline_or_vbl(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if not (vbl.current_user or beamline.current):
            return vbl.get_login_redirect()
        return func(*args, **kwargs)
    return decorated
