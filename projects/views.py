from flask import Blueprint, request, flash, redirect, url_for
from bson import ObjectId

from ..plugins import db
from ..utils import templated
from forms import SampleForm, ProjectForm


projects = Blueprint('projects', __name__, url_prefix='/projects')


def samples_form(_id=None, project_id=None):
    if _id:
        sample = db.Sample.get_from_id(_id)
    else:
        sample = db.Sample()

    form = SampleForm(request.form, sample)
    form.project.choices = [(project._id, project.name) for project in db.Project.find()]

    if len(form.project.choices) == 0:
        raise Exception('Cannot add samples no projects defined')

    if _id:
        form.project.data = form.project.coerce(sample.project._id)

    if request.method == 'POST':
        sample.name = form.name.data
        sample.description = form.description.data
        sample.priority = form.priority.data
        if project_id:
            sample.project = db.Project.get_from_id(project_id)
        else:
            sample.project = db.Project.get_from_id(ObjectId(form.project.data))
        sample.save()
        return (True, sample.name)
    return (False, form)


@projects.route("")
@templated()
def index():
    return dict(projects=db.Project.find())


def projects_form(_id=None):
    if _id:
        project = db.Project.get_from_id(_id)
    else:
        project = db.Project()

    form = ProjectForm(request.form, project)
    if request.method == 'POST':
        project.name = request.form['name']
        project.description = request.form['description']
        project.sequence = request.form['sequence']
        project.save()
        return (True, project.name)
    return (False, form)


@projects.route('/add', methods=['GET', 'POST'])
@templated('projects/form.twig.html')
def add():
    status, data = projects_form()
    if status:
        flash('Project <strong>%s</strong> added' % (data, ), 'success')
        return redirect(url_for('.index'))
    return dict(form=data, page='Add', submit='Add')


@projects.route('/edit/<ObjectId:_id>', methods=['GET', 'POST'])
@templated('projects/form.twig.html')
def edit(_id):
    status, data = projects_form(_id)
    if status:
        flash('Project <strong>%s</strong> updated' % (data, ), 'success')
        return redirect(url_for('.index'))
    return dict(form=data, page='Edit', submit='Update')


@projects.route("/delete/<ObjectId:_id>")
def delete(_id):
    project = db.Project.get_from_id(_id)
    #[ item.delete() for item in db.Sample.find({'project.$id':project._id})]
    if db.Sample.find({'project.$id': project._id}).count() > 0:
        flash('Project cant be deleted has referenced samples', 'error')
        return redirect(url_for('.index'))
    flash('Project <strong>%s</strong> deleted' % (project.name, ))
    project.delete()
    return redirect(url_for('.index'))


@projects.route("/<ObjectId:project_id>/samples")
@templated()
def samples_list(project_id):
    samples = db.Sample.find({'project.$id': project_id})
    project = db.Project.get_from_id(project_id)
    priority_map = {
        u'None': '',
        u'Low': 'label-success',
        u'Medium': 'label-warning',
        u'High': 'label-important',
    }
    return locals()


@projects.route('/<ObjectId:project_id>/samples/add', methods=['GET', 'POST'])
@templated('projects/samples/form.twig.html')
def samples_add(project_id):
    try:
        status, data = samples_form(project_id=project_id)
    except Exception, e:
        flash(str(e), 'error')
        return redirect(url_for('.samples_list', project_id=project_id))
    if status:
        flash('Sample <strong>%s</strong> added' % (data), 'success')
        return redirect(url_for('.samples_list', project_id=project_id))
    return dict(form=data, page='Add', submit='Add', project_id=project_id)


@projects.route('/<ObjectId:project_id>/samples/edit/<ObjectId:_id>', methods=['GET', 'POST'])
@templated('projects/samples/form.twig.html')
def samples_edit(_id, project_id):
    status, data = samples_form(_id)
    if status:
        flash('Sample <strong>%s</strong> updated' % (data), 'success')
        return redirect(url_for('.samples_list', project_id=project_id))
    return dict(form=data, page='Edit', submit='Update', project_id=project_id)


@projects.route("/<ObjectId:project_id>/samples/delete/<_id>")
def samples_delete(_id, project_id):
    sample = db.Sample.get_from_id(ObjectId(_id))
    flash('Sample <strong>%s</strong> deleted' % (sample.name, ), 'success')
    sample.delete()
    return redirect(url_for('.samples_list', project_id=project_id))
