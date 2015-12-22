from flask import Blueprint, current_app, request, flash, redirect, url_for, render_template
from collections import OrderedDict

from ..plugins import db
from ..utils import templated
from forms import HolderForm


holders = Blueprint('holders', __name__, url_prefix='/holders')


@holders.route("")
@templated()
def index():
    return dict(holders=db.Holder.find())


@holders.route('/add', methods=['GET', 'POST'])
@templated('holders/form.twig.html')
def add():
    form = HolderForm(request.form)
    if request.method == 'POST':
        holder = db.Holder()
        holder.name = form.name.data
        holder.type = form.type.data
        holder.save()
        flash('Holder <strong>%s</strong> added' % (holder.name, ), 'success')
        return redirect(url_for('.list'))
    return dict(form=form, page='Add', submit='Add')


@holders.route('/view/<ObjectId:_id>')
def view(_id):
    from operator import itemgetter

    holder = db.Holder.get_from_id(_id)
    samples = OrderedDict({})

    sorted_samples = sorted(holder.samples, key=itemgetter('position'))
    for sample in sorted_samples:
        samples[sample['position']] = sample['sample']

    if holder.type == 'Puck':
        return holders_view_puck(holder=holder, samples=samples)

    if holder.type == 'Cassette':
        return holders_view_cassette(holder=holder, samples=samples)


def holders_view_puck(**context):
    size = 300
    pin_radius, coords = generate_puck(size/2.0)
    width = height = pin_radius * 2.0

    context.update(coords=coords,
                   width=width,
                   height=height,
                   puck_size=size)

    return render_template('holders/puck/view.twig.html', **context)


def holders_view_cassette(**context):
    context.update(letters=dict([(x, str(unichr(65+x))) for x in range(8)]))
    return render_template('holders/cassette/view.twig.html', **context)


@holders.route('/<ObjectId:_id>/sample/add/<pos>')
@templated()
def sample_add(_id, pos):
    samples = db.Sample.find({'holder': None})
    if not samples.count() > 0:
        flash('No Samples', 'error')
        return redirect(url_for('.view', _id=_id))
    current_app.logger.info([_id])
    return dict(_id=_id, pos=pos, samples=samples)


@holders.route('/<ObjectId:_id>/sample/add/<pos>/<ObjectId:sample_id>')
def sample_add_test(_id, pos, sample_id):
    holder = db.Holder.get_from_id(_id)
    sample = db.Sample.get_from_id(sample_id)

    holder.samples.append({
        'position': int(pos),
        'sample': sample
    })
    sample.holder = holder._id

    holder.save()
    sample.save()
    return redirect(url_for('.view', _id=_id))


@holders.route('/<ObjectId:_id>/sample/remove/<pos>/<ObjectId:sample_id>')
def sample_remove_test(_id, pos, sample_id):
    holder = db.Holder.get_from_id(_id)

    for item in holder.samples:
        if item['position'] == pos:
            break
    else:
        holder.samples.remove(item)
        item['sample'].holder = None
        holder.save()
        item['sample'].save()

    return redirect(url_for('.view', _id=_id))


@holders.route("/delete/<ObjectId:_id>")
def delete(_id):
    holder = db.Holder.get_from_id(_id)
    flash('Holder <strong>%s</strong> deleted' % (holder.name, ), 'success')
    holder.delete()
    return redirect(url_for('.list'))


def generate_xy(radius, count):
    from math import pi, sin, cos

    angle = (2.0 * pi) / count

    # this is funky so the points get generated in the correct order for numbering
    points = [0] + range(1, count)[::-1]

    return [(radius * sin((i * angle) - pi/2),
             radius * cos((i * angle) - pi/2)) for i in points]


def generate_puck(radius=200):
    inner_radius = radius * 0.34
    outer_radius = radius * 0.73

    inner = generate_xy(inner_radius, 5)
    outer = generate_xy(outer_radius, 11)

    pin_radius = round(radius * 0.36, 2) / 2.0

    # adjust for top,left position
    offset = radius - pin_radius
    coords = [(i,
               round(x+offset, 2),
               round(y+offset, 2)) for i, (x, y) in enumerate(inner + outer)]

    return (pin_radius, coords)
