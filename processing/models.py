from flask.ext.mongokit import Document
from mongokit import IS

from ..projects.models import Sample, Retrigger


class Processing(Document):
    __collection__ = 'processing'

    structure = {
        'sample': Sample,
        'start_angle': float,
        'type': IS(u'indexing', u'dataset'),
        'epn': unicode,
        'resolution': float,
        'space_group': unicode,
        'unit_cell': (float, float, float),
        'no_frames': int,
        'directory': unicode,
        'status': unicode,
        'success': bool,
        'completed': bool,
        'processing_dir': unicode,
        'retrigger' : Retrigger,
	'rmerge_plot' : unicode
    }

    required_fields = ['sample', 'type', 'epn']
    use_dot_notation = True
    use_schemaless = True
    use_autorefs = True
    force_autorefs_current_db = True
