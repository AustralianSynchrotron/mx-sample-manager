from flask.ext.mongokit import MongoKit
from flask.ext.pymongo import PyMongo
from flask.ext.vbl import VBL
from flask.ext.beamline import Beamline
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