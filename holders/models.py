from flask_mongokit import Document
from mongokit import IS

from ..projects.models import Sample


class Holder(Document):
    __collection__ = 'holders'
    structure = {
        'name': unicode,
        'type': IS(u'Puck', u'Cassette'),
        'samples': [{
            'position': int,
            'sample': Sample
        }]
    }
    required_fields = ['name', 'type']
    use_dot_notation = True
    use_schemaless = True
    use_autorefs = True
    force_autorefs_current_db = True
