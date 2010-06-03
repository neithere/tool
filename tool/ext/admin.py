# -*- coding: utf-8 -*-

"""
Administrative interface for PyModels. Requires :mod:`tool.ext.models` to be
properly set up.

Configuration example (in YAML)::

    bundles:
        - tool.ext.models
        - tool.ext.admin

"""

from tool.routing import url, BuildError, redirect_to
from werkzeug import Response
from tool.ext.jinja import as_html
from tool.ext.models import storage
from tool.ext.pagination import Pagination


# FIXME STUBS!!!!
login_required = lambda f: f

#from glasnaegel.bundles.auth import setup_auth, login_required
from pymodels.utils.forms import model_form_factory


_registered_models = {}
_urls_for_models = {}
_excluded_names = {}

def register(model, namespace='main', url=None, exclude=None):
    """
    :param model: a PyModels model
    :param namespace: a short string that will be part of the URL. Default
        is "main".
    :param url: a function that gets a model instance and returns an URL

    Usage::

        from pymodels import Model
        from tool.ext import admin

        class Item(Model):
            ...
        admin.register(Item)

    """
    # TODO: model should provide a slugified version of its name itself
    name = model.__name__ #.lower()
    _registered_models.setdefault(namespace, {})[name] = model
    _urls_for_models[model] = url
    _excluded_names[model] = exclude

def _get_model(namespace, name):
    if namespace not in _registered_models:
        raise NameError('There is no registered namespace "%s"' % namespace)
    try:
        return _registered_models[namespace][name]
    except KeyError:
        raise NameError('"%s" is not a registered model in namespace %s.' %
                        (name, namespace))

def _get_excluded_names(model):
    return _excluded_names[model] or []

def _get_url_for_object(obj):
    if not obj.pk:
        return
    model = type(obj)
    f = _urls_for_models[model]
    try:
        return f(obj) if f else None
    except BuildError:
        return None

#-- VIEWS ------------------------------------------------------------------

@url('/')
@login_required
@as_html('admin/index.html')
def index(req):
    return {
        'namespaces': _registered_models,
    }

@url('/<string:namespace>/')
@login_required
@as_html('admin/namespace.html')
def namespace(req, namespace):
    return {
        'namespace': namespace,
            'models': _registered_models[namespace],
    }

@url('/<string:namespace>/<string:model_name>/')
@login_required
@as_html('admin/object_list.html')
def object_list(req, namespace, model_name):
    model = _get_model(namespace, model_name)
    query = model.objects(storage)
    #pagin_args =  {'namespace': namespace, 'model_name': model_name}
    #objects, pagination = paginated(query, req, pagin_args)
    page = req.values.get('page', 1)
    per_page = req.values.get('per_page', 10)
    pagination = Pagination(query, per_page, page, 'tool.ext.admin.object_list')

    return {
        'namespace': namespace,
        'query': query,
        #'objects': objects,
        'pagination': pagination,
    }

@url('/<string:namespace>/<string:model_name>/<string:pk>/')
@url('/<string:namespace>/<string:model_name>/add/')
@login_required
@as_html('admin/object_detail.html')
def object_detail(req, namespace, model_name, pk=None):
    model = _get_model(namespace, model_name)
    if pk:
        obj = storage.get(model, pk)
        creating = False
    else:
        obj = model()
        creating = True

    if not creating and req.form.get('DELETE'):
        # TODO: confirmation screen.
        # List related objects, ask what to do with them (cascade/ignore/..)
        obj.delete()
        return redirect_to('adminsite/object_list', namespace=namespace,
                        model_name=model_name)

    ModelForm = model_form_factory(model, storage)
    form = ModelForm(req.form, obj)

    for name in _get_excluded_names(model):
        del form[name]

    message = None
    if req.method == 'POST' and form.validate():
        form.populate_obj(obj)

#    assert 0==1, 'DEBUG'
#    if not __debug__:

        obj.save(storage)    # storage can be omitted if not creating obj
        message = u'%s has been saved.' % obj.__class__.__name__
        if creating:
            # redirect to the same view but change URL
            # from ".../my_model/add/" to
            # to the editing URL ".../my_model/123/"
            return redirect_to('tool.ext.admin.object_detail',
                            namespace=namespace, model_name=model_name,
                            pk=obj.pk)
    obj_url = _get_url_for_object(obj)

    # objects of other models that are known to reference this one
    references = {}
    for model, attrs in model._meta.referenced_by.iteritems():
        for attr in attrs:
            qs = model.objects(storage).where(**{attr: obj.pk})
            if qs.count():
                references.setdefault(model, {})[attr] = qs

    return {
        'namespace': namespace,
        'object': obj,
        'object_url': obj_url,
        'form': form,
        'message': message,
        'references': references,
    }
