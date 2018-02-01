from flask import Blueprint, request, json, render_template
from jinja2.exceptions import TemplateNotFound
from bson import ObjectId, json_util
import re

from .. import localtime
from ..plugins import mongo, vbl, beamline
from ..utils import templated, jsonify, request_wants_json
from .. import config

from yaml import Loader, safe_load

processing = Blueprint('processing', __name__, url_prefix='/processing')


@processing.route("/epns")
@vbl.requires_auth
@templated()
def epns():
    return {}


@processing.route("", methods=['GET', 'POST'])
@templated()
def index():
    if request.method == 'POST':
        data = json.loads(unicode(request.data), object_hook=json_util.object_hook)
        _id = mongo.db.processing.insert(data)
        return jsonify(_id=ObjectId(_id))

    if request_wants_json():
        query = {'epn':  request.args.get('epn', beamline.EPN),
                 'type': request.args.get('type'), 
                 'subtype': request.args.get('subtype')}
        query = {k: v for k, v in query.iteritems() if v}

        cursor = mongo.db.processing.find(query).sort('_id', -1)

        limit = request.args.get('limit')
        if limit:
            cursor.limit(int(limit))
        elif not query.get('epn'):
            cursor.limit(50)

        items = list(cursor)
        return jsonify(results=items)

    # for the page generation we return nothing
    # on load a json request will build the table
    return {}


@processing.route("/<ObjectId:_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def obj(_id):
    if request.method == 'GET':
        item = mongo.db.processing.find_one({'_id': _id})
        return jsonify(**item)

    if request.method == 'PATCH':
        data = json.loads(unicode(request.data))
        mongo.db.processing.update({'_id': _id}, {'$set': data})

    if request.method == 'DELETE':
        mongo.db.processing.remove({'_id': _id})

    if request.method == 'PUT':
        data = json.loads(unicode(request.data), object_hook=json_util.object_hook)
        mongo.db.processing.update({'_id': _id}, data, upsert=True)

    return jsonify(result=True)


@processing.route("/view/<ObjectId:_id>")
@templated()
def view(_id):
    item = mongo.db.processing.find_one({'_id': _id})

    try:
        collection = mongo.db.collections.find_one({'_id': item['collection_id'].id})
    except KeyError:
        # expected if no collection is available - for visits before now
        collection = None
    started_at = localtime.normalize(_id.generation_time.astimezone(localtime))
    item['started_at'] = started_at.strftime('%Y-%m-%d %H:%M:%S %Z')
    item['sample'] = item['sample']['name']

    name_unit = {}
    degree = u'\u00b0'
    angstrom = u'\u00c5'
    name_unit['start_angle'] = degree
    name_unit['exposure_time'] = 's'
    name_unit['attenuation'] = '%'
    name_unit['energy'] = 'KeV'
    name_unit['distance'] = 'mm'
    name_unit['oscillation'] = degree
    name_unit['wedge'] = degree
    name_unit['resolution'] = angstrom
    name_unit['average_mosaicity'] = degree
    name_unit['mosaicity'] = degree
    name_unit['low_resolution'] = angstrom
    name_unit['high_resolution'] = angstrom
    name_unit['low_resolution_limit'] = angstrom
    name_unit['high_resolution_limit'] = angstrom
    name_unit['completeness'] = '%'
    name_unit['anomalous_completeness'] = '%'
    name_unit['indexing_refined_rmsd'] = angstrom

    if collection is not None:
        item['start_angle'] = collection['start_angle']
        item['exposure_time'] = collection['exposure_time']
        try:
            if collection['wedge']:
                item['wedge'] = collection['wedge']
        except KeyError:
            pass # KeyError is expected if wedge is not populated, such as for old collections
        item['attenuation'] = collection['attenuation_readback']
        item['energy'] = collection['energy_readback']
        item['oscillation'] = collection['delta']
        item['distance'] = collection['distance_readback']

    context = dict(item=item, keys=item.keys(), values=item.values(), name_unit=name_unit)
    context['field_collection'] = ['epn', 'exposure_time', 'start_angle', 'oscillation', 'no_frames', 'wedge',
                                   'last_frame', 'attenuation', 'energy', 'distance']
    context['field_processing_overall'] = ['started_at', 'status', 'sample', 'directory', 'resolution', 'space_group',
                                           'unit_cell', 'processing_dir', 'run_label']
    context['field_retrigger'] = ['first_frame', 'last_frame', 'low_resolution', 'high_resolution', 'unit_cell',
                                  'space_group', 'ice', 'weak', 'slow', 'brute', 'from_start']

    if str(item['type']) == 'dataset' or str(item['type']) == 'screening':
        context['field_order'] = [f for f in ['low_resolution_limit', 'high_resolution_limit', 'completeness', 'i/sigma', 'rmerge', 'rpim(i)', 'multiplicity'] if f in item.keys()]
        context['field_order'].extend(sorted([key for key, value in item.iteritems()
                                              if key not in context['field_order'] and isinstance(value, list) and len(value) <= 3]))
        context['field_processing_overall'].append('average_mosaicity')
    elif str(item['type']) == 'indexing':
        context['field_processing_overall'].extend(['mosaicity', 'indexing_refined_rmsd'])

    template = 'processing/view_%s.twig.html' % str(item['type'])
    try:
        return render_template(template, **context)
    except TemplateNotFound:
        print "Failed to find template for %s" % (template, )
        return context

@processing.route("/retrigger/<ObjectId:_id>")
@templated()
def retrigger(_id):
    item = mongo.db.processing.find_one({'_id':_id})
    item['sample'] = item['sample']['name']

    name_unit = {}
    angstrom = u'\u00c5'
    name_unit['resolution'] = angstrom

    context = dict(item=item, name_unit=name_unit)
    return context

from rq import Queue
def sanitize_uc(uc):
    # return a valid unit cell or nothing
    # some valid formats include  h,k,l,a,b,g [h k l a b g]
    # there must be 6 numbers
    values = re.split('[\[\(\)\]\,\ ]', uc)
    uc_values = [float(value) for value in values if value != '']
    if len(uc_values) != 6:
        return None, 'Unit cell must have 6 values'
    for value in uc_values:
    	if value <= 0:
            return None, 'Unit cell value must be positive'
    return '[{0[0]}, {0[1]}, {0[2]}, {0[3]}, {0[4]}, {0[5]}]'.format(uc_values), None

def sanitize_uc_sg(uc, sg):
    with open('sg.yaml', 'r') as sg_text:
        sg_dict = safe_load(sg_text)
        good_sg = sg_dict.get(sg)
        uc, error = sanitize_uc(uc)
        return uc, good_sg, error
    
@processing.route("/retrigger/submit", methods=['POST'])
def retrigger_submit():
    r = beamline.redis[beamline.current]
    q = Queue(config.REDIS_QUEUE_NAME, connection=r)
    kwargs = request.form.to_dict(flat=True)
    uc, sg, error = sanitize_uc_sg(kwargs['unit_cell'], kwargs['space_group'])
    if not error:
        kwargs['unit_cell'] = uc
        kwargs['space_group'] = sg
        q.enqueue_call(func='mx_auto_dataset.dataset',
                   kwargs=kwargs,
                   timeout=1800)
        return jsonify(result=request.form['dataset_id'])
    raise ValueError('Unit cell or space group not defined correctly: %s' % error)


@processing.route("/merging/submit", methods=['POST'])
def merge_submit():
    r = beamline.redis[beamline.current]

    q = Queue(config.MERGE_REDIS_QUEUE_NAME, connection=r)
    k = {}
    for key, value in request.values.items():
        k[key] = value
    q.enqueue_call(func=config.MERGE_REDIS_METHOD_NAME, kwargs=k, timeout=3600)
    return jsonify(result=request.values)
