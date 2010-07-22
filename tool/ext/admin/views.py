# -*- coding: utf-8 -*-

from functools import wraps
from werkzeug import Response
from tool import context
from tool.routing import url, url_for, BuildError, redirect_to
from tool.signals import called_on
from tool.ext.templating import as_html, templating_ready
from tool.ext.documents import db
from tool.ext.pagination import Pagination
from tool.ext.breadcrumbs import entitled


# FIXME STUBS!!!!
login_required = lambda f: f

#from glasnaegel.bundles.auth import setup_auth, login_required
from docu.ext.forms import document_form_factory


DEFAULT_NAMESPACE = 'main'


# TODO: use tool.context?
_registered_models = {}
_urls_for_models = {}
_excluded_names = {}
_ordering = {}
_list_names = {}

def register(model, namespace=DEFAULT_NAMESPACE, url=None, exclude=None, ordering=None,
             list_names=None):
    """
    :param model:
        a Docu document class
    :param namespace:
        a short string that will be part of the URL. Default is "main".
    :param url:
        a function that gets a model instance and returns an URL
    :param ordering:
        a dictionary in this form: ``{'names': ['foo'], 'reverse': False}``.
        See Docu query API for details on ordering.
    :param list_names:
        a list of field names to be displayed in the list view.

    Usage::

        from docu import Document
        from tool.ext import admin

        class Item(Document):
            ...
        admin.register(Item)

    """
    # TODO: model should provide a slugified version of its name itself
    name = model.__name__ #.lower()
    _registered_models.setdefault(namespace, {})[name] = model
    _urls_for_models[model] = url
    _excluded_names[model] = exclude
    _ordering[model] = ordering
    _list_names[model] = list_names
    return model


class DocAdmin(object):
    """
    Description of admin interface for given Document class.
    """
    namespace = DEFAULT_NAMESPACE
    url = None
    exclude = None
    order_by = None
    ordering_reversed = False
    list_names = None

    @classmethod
    def register_for(cls, doc_class):
        if cls.order_by:
            ordering = dict(names=cls.order_by, reverse=cls.ordering_reversed)
        else:
            ordering = None
        register(doc_class,
            namespace = cls.namespace,
            url = cls.url,
            exclude = cls.exclude,
            ordering = ordering,
            list_names = cls.list_names,
        )


def register_for(doc_class):
    """
    Decorator for DocAdmin classes. Usage::

        @admin.register_for(Note)
        class NoteAdmin(admin.DocAdmin):
            namespace = 'notepad'
            url = lambda d: d.get_url()
            exclude = ['foo']
            ordering = {'names': ['date_time'], 'reverse': True}

    """
    @wraps(doc_class)
    def inner(admin_class):
        admin_class.register_for(doc_class)
        return admin_class
    return inner


def admin_url_for_query(query, namespace=DEFAULT_NAMESPACE):
    """
    Returns admin URL for given document query. Usage (in templates)::

        <a href="{{ admin_url_for_query(object_list) }}">View in admin</a>

    :param query:
        A docu query adapter instance. The related document class must be
        already registered with admin.
    :param namespace:
        The admin namespace (optional).

    """
    model_name = query.model.__name__
    return url_for('tool.ext.admin.views.object_list',
                   namespace=namespace, model_name=model_name)

def admin_url_for(obj, namespace=DEFAULT_NAMESPACE):
    """
    Returns admin URL for given object. Usage (in templates)::

        <a href="{{ admin_url_for(obj) }}">View {{ obj.title }} in admin</a>

    :param obj:
        A docu.Document instance. Must have the primary key. The document class
        must be already registered with admin.
    :param namespace:
        The admin namespace (optional).

    """
    model_name = obj.__class__.__name__
    return url_for('tool.ext.admin.views.object_detail',
                   namespace=namespace, model_name=model_name, pk=obj.pk)

@called_on(templating_ready)
def setup_templating(**kwargs):
    context.templating_env.globals.update(
        admin_url_for = admin_url_for,
        admin_url_for_query = admin_url_for_query,
    )

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
@entitled(u'Admin site')
@as_html('admin/index.html')
def index(request):
    return {
        'namespaces': _registered_models,
    }

@url('/<string:namespace>/')
@login_required
@entitled(lambda **kw: kw['namespace'])
@as_html('admin/namespace.html')
def namespace(request, namespace):
    return {
        'namespace': namespace,
        'models': _registered_models[namespace],
    }

@url('/<string:namespace>/<string:model_name>/')
@login_required
@entitled(lambda **kw: _get_model(kw['namespace'], kw['model_name'])
                       .meta.label_plural)
@as_html('admin/object_list.html')
def object_list(request, namespace, model_name):
    model = _get_model(namespace, model_name)
    query = model.objects(db)

    ordering = _ordering.get(model)
    if 'sort_by' in request.values:
        sort_field = request.values.get('sort_by')
        sort_reverse = bool(request.values.get('sort_reverse', False))
        ordering = dict(ordering, names=[sort_field])
    if ordering:
        query = query.order_by(**ordering)

    #pagin_args =  {'namespace': namespace, 'model_name': model_name}
    #objects, pagination = paginated(query, req, pagin_args)
    page = request.values.get('page', 1)
    per_page = request.values.get('per_page', 20)
    pagination = Pagination(query, per_page, page, 'tool.ext.admin.object_list')

    list_names = _list_names[model] or ['__unicode__']

    return {
        'namespace': namespace,
        'query': query,
        #'objects': objects,
        'pagination': pagination,
        'list_names': list_names,
    }

@url('/<string:namespace>/<string:model_name>/<string:pk>')
@url('/<string:namespace>/<string:model_name>/add')
@login_required
@entitled(lambda **kw: (u'Editing {0}' if 'pk' in kw else u'Adding {0}').format(
    _get_model(kw['namespace'], kw['model_name']).meta.label))
@as_html('admin/object_detail.html')
def object_detail(request, namespace, model_name, pk=None):
    model = _get_model(namespace, model_name)
    if pk:
        obj = db.get(model, pk)
        creating = False
    else:
        obj = model()
        creating = True

    if not creating and request.form.get('DELETE'):
        # TODO: confirmation screen.
        # List related objects, ask what to do with them (cascade/ignore/..)
        obj.delete()
        return redirect_to('tool.ext.admin.object_list', namespace=namespace,
                        model_name=model_name)

    DocumentForm = document_form_factory(model, db)
    form = DocumentForm(request.form, obj)

    for name in _get_excluded_names(model):
        del form[name]

    message = None
    if request.method == 'POST' and form.validate():
        form.populate_obj(obj)

        #assert 0==1, 'DEBUG'
        #if not __debug__:

        obj.save(db)    # storage can be omitted if not creating obj

        # TODO: move this to request.session['messages'] or smth like that
        message = u'%s has been saved.' % obj.__class__.__name__
        #if creating:
        # redirect to the same view but change URL
        # from ".../my_model/add/" to
        # to the editing URL ".../my_model/123/"
        # ...hmm, we *should* redirect even after editing an existing item
        return redirect_to('tool.ext.admin.object_detail',
                           namespace=namespace, model_name=model_name,
                           pk=obj.pk)
    obj_url = _get_url_for_object(obj)

    # objects of other models that are known to reference this one
    references = {}
    for model, attrs in model.meta.referenced_by.iteritems():
        for attr in attrs:
            qs = model.objects(db).where(**{attr: obj.pk})
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
