# -*- coding: utf-8 -*-

"""
Template engine (Jinja2)
========================

:state: stable
:dependencies: `Jinja2`_

.. _Jinja2: http://jinja.pocoo.org/2/

Settings
--------

This bundle does not have to be explicitly loaded. Bundles that depend on
`tool.ext.templating` will usually import it first. This is enough to trigger
the setup hook. In any case, an empty configuration is fine. See sections below
for details.

Bundle templates
----------------

`Jinja2`_ provides excellent means to configure the way templates are located
and loaded. Tool looks up the template in this order:

* the project-level search paths (first full match wins);
* the registered prefixes (i.e. the path starts with a known bundle name).

The `prefixes` can be registered with :func:`register_templates`. For example,
we have created a bundle with this layout::

    my_bundle/
        templates/
            foo.html
        __init__.py


To register the bundle's templates, add this to its `__init__.py`::

    from tool.ext.templating import register_templates

    register_templates(__name__)

This will make our `foo.html` globally available as `my_bundle/foo.html`.

There are other ways to register the templates. Please consult the code to find
them out. Anyway, templates *must* be registered explicitly. Tool lets you
organize the bundles the way you want and therefore expects that you tell what
is where.

Overriding templates
--------------------

Web-oriented Tool bundles usually provide templates. Sometimes you'll want to
replace certain templates. Let's say we are not comfortable with a default
:doc:`Admin <ext_admin>` template and want to override it. Let's create a
project-level directory for templates and put our customized templates there::

    some_site/
        templates/
            admin/
                object_list.html
        conf.yaml
        manage.py

As you see, the template path within `templates/` will be
`admin/object_list.html` (`admin` is the natural template prefix for
`tool.ext.admin`, see :func:`register_templates` for details).

Now let's edit out `conf.yaml` and let the application know about the
`templates/` directory::

    bundles:
        tool.ext.templating:
            searchpaths: ['templates']

Well, actually this is the default setting. If `searchpaths` is not defined at
all, it is assumed to be ``['templates']``.

Now the template `admin/object_list.html` will be picked from the `templates/`
directory. All other admin templates remain defaults.

This way you can override any bundle's template.

API reference
-------------
"""
from copy import deepcopy
from functools import wraps
from werkzeug import Response
from tool import context
from tool import dist
from tool.routing import url_for
from tool.signals import called_on, Signal
from tool.application import app_manager_ready, request_ready

dist.check_dependencies(__name__)

from jinja2 import Environment, ChoiceLoader, FileSystemLoader, PackageLoader, PrefixLoader


__all__ = [
    'as_html', 'templating_ready', 'register_templates', 'render_template',
    'render_response'
]


DEFAULT_PATH = 'templates'


templating_ready = Signal()


def register_templates(module_name, dir_name=DEFAULT_PATH, prefix=None):
    """
    Registers given bundle's templates in the Jinja template loader.

    :param module_name:
        The dotted path to the bundle module. The absolute path to the
        templates will depend on the module location.
    :param dir_name:
        Templates directory name within given module. Default is ``templates``.
        Relative to module's ``__file__``.
    :param prefix:
        The prefix for templates. By default the rightmost part of the module
        name is used e.g. ``tool.ext.admin`` will have the prefix ``admin``.

    Simple example (assuming that the code is in `my_bundle/__init__.py`)::

        register_templates(__name__)

    In this case the absolute path to templates will be constructed from module
    location and the default name for template directory, i.e. something like
    `/path/to/my_bundle/templates/`.

    The templates will be available as ``my_bundle/template_name.html``.

    Advanced usage::

        register_templates('proj.bundle_foo', 'data/tmpl/', prefix='proj')

    In this case the absolute path to templates will be something like
    `/path/to/proj/bundle_foo/data/tmpl/`.

    The templates will be available as ``proj/template_name.html``.

    .. note::

        The templates are actually registered only when the Jinja environment
        is ready and the signal :attr:`templating_ready` fires. Usually this
        implies loading the :class:`~tool.application.ApplicationManager`
        (without compiling the WSGI stack).

    .. warning::

        This only works for bundles that are declared in settings. If a bundle
        is not in settings but still imported e.g. with `find_urls`, its
        loading occurs *after* `templating_ready` signal is broadcasted, so its
        templates are never registered. Please mind that until the issue is
        fixed here.

    """
    @called_on(templating_ready, weak=False)
    def callback(**kwargs):
        # this prefix/_prefix mess is because Python doesn't grok some
        # namespace stuff
        _prefix = module_name.split('.')[-1] if prefix is None else prefix
        jinja_env = kwargs['sender']
        loaders = jinja_env.loader.loaders
        assert len(loaders) == 2
        assert isinstance(loaders[1], PrefixLoader)
        loader = PackageLoader(module_name, dir_name)
        loaders[1].mapping[_prefix] = loader


# Template rendering

def render_template(template_path, **extra_context):
    """
    Renders given template file with given context.

    :template_path:
        path to the template; must belong to one of directories listed in
        `searchpaths` (see configuration).
    """
    assert hasattr(context, 'templating_env'), (
        'Jinja environment must be initialized. Make sure the bundle\'s setup '
        'function is called.')
    template = context.templating_env.get_template(template_path)
    return template.render(extra_context)

def render_response(template_path, mimetype='text/html', **extra_context):
    """TODO

    Internally calls :func:`render_template`.
    """
    return Response(
        render_template(template_path, **extra_context),
        mimetype=mimetype,
    )

def as_html(template_path):
    """
    Decorator for views. If the view returns a dictionary, given template is
    rendered with that dictionary as the context. If the returned value is not
    a dictionary, it is passed further as is.

    Internally calls :func:`render_response`.
    """
    def wrapper(f):
        @wraps(f)
        def inner(*args, **kwargs):
            result = f(*args, **kwargs)
            if isinstance(result, dict):
                return render_response(template_path, **result)
            return result
        return inner
    return wrapper


@called_on(app_manager_ready)
def setup(sender, **kwargs):
    """
    Setup the ApplicationManager to use Jinja2.
    """
    manager = sender #kwargs['sender']

    try:
        conf = manager.get_settings_for_bundle(__name__, {})
    except KeyError:
        return False

    #conf = manager.settings['bundles']['jinja']
    #conf = deepcopy(manager.settings.get('templates', {}))

    # TODO: per bundle?
    #conf = dict(conf).setdefault('paths', ['templates'])

    #tmpl_paths = conf.get('paths', [])    #getattr(context, 'template_paths', [])
    #tmpl_paths.append('templates')    # TODO: per bundle?
    #context.template_paths = tmpl_paths

    paths = conf.pop('searchpaths', [DEFAULT_PATH])
    #fs_loader = FileSystemLoader(paths)

    # TODO: think of the best way to use http://jinja.pocoo.org/2/documentation/api#jinja2.PrefixLoader
    # and related stuff (they can be nested).
    # Requirements:
    # * /mybundle/templates/foo.html   (no /mybundle/templates/mybundle/foo.html)
    # * /templates/mybundle/foo.html   (appman-level override)
    #p=PackageLoader('tool.ext.admin', 'templates')
    #c=ChoiceLoader([p])
    #pref=PrefixLoader({'admin': c})
    #pref.list_templates()

    """
ChoiceLoader(
    FileSystemLoader([path_one, path_two]),
    PrefixLoader(
        PackageLoader(), .., N
    )
)
    """

    loader = ChoiceLoader([
        FileSystemLoader(paths),
        PrefixLoader({})
    ])




    # (also, mb jinja provides a signal and listens to it; when a bundle wants
    # to register a template, it just emits the signal and jinja either
    # collects the info until it's ready or processes immediately)

    #loader = FileSystemLoader(paths)
    #loader = ChoiceLoader([FileSystemLoader(path) for path in paths])

    context.templating_env = Environment(loader=loader, **conf)

    templating_ready.send(context.templating_env)

@called_on(request_ready)
def update_jinja_env(*args, **kwargs):
    try:
        settings = context.app_manager.get_settings_for_bundle(__name__, {})
    except KeyError:
        # probably not the right app for us, just ignore
        return False
    default_globals = dict(
        url_for=url_for,
        request=context.request
    )
    #_globals = dict(default_globals)  #, **conf.get('globals', {}))
    #if 'globals' in settings:
    default_globals.update(settings.get('globals', {}))
    context.templating_env.globals.update(default_globals)

    #signals.connect(init_jinja_env, signal='request_ready', weak=False)

    #tmpl_loaders = {
    #}

    #tmpl_globals = {
    #}

    #tmpl_filters = {
    #}
    #context.template_env = create_template_environment(
    #    paths   = tmpl_paths,
    #    loaders = tmpl_loaders,
    #    globals = tmpl_globals,
    #    filters = tmpl_filters,
    #)
"""
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, TemplateNotFound

def create_template_environment(searchpaths, loaders, globals, filters,
                                tests, env_kw):
    if not env_kw:
        env_kw = {}
    base_loader = FileSystemLoader(searchpaths)
    env_kw['loader'] = ChoiceLoader([base_loader] + loaders)
    if 'extensions' not in env_kw:
        env_kw['extensions']=['jinja2.ext.i18n', 'jinja2.ext.do',
                              'jinja2.ext.loopcontrols']

    loader = FileSystemLoader(paths)
    extensions = ['jinja2.ext.
    env = Environment(loader=loader, extensions=extensions)
    env.globals.update(globals)
    env.filters.update(filters)
    env.tests.update(tests)
    return env
"""
