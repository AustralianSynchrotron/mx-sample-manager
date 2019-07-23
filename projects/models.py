from flask_mongokit import Document
from mongokit import ObjectId, IS


class Project(Document):
    __collection__ = 'projects'
    structure = {
        'name': unicode,
        'description': unicode,
        'sequence': unicode,
    }
    required_fields = ['name']
#    default_values = {'creation': datetime.utcnow}
    use_dot_notation = True
    use_schemaless = True


class Sample(Document):
    __collection__ = 'samples'
    structure = {
        'name': unicode,
        'description': unicode,
        'project': Project,
        'holder': ObjectId,
        'priority': IS(u'None', u'Low', u'Medium', u'High'),
    }
    required_fields = ['name', 'project']
#    default_values = {'creation': datetime.utcnow}
    use_dot_notation = True
    use_schemaless = True
    use_autorefs = True
    force_autorefs_current_db = True

class Retrigger(Document):
    __collection__ = 'retrigger'
    structure = {
        'first_frame' : int,
        'last_frame' : int,
        'low_resolution' : float,
        'high_resolution': float,
        'unit_cell': (float, float, float),
        'space_group' : unicode,
        'ice' : bool,
        'weak' : bool,
        'slow' : bool,
        'brute' : bool
    }
    use_dot_notation = True
    use_schemaless = True
