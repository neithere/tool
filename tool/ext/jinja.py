# -*- coding: utf-8 -*-

"""
Configuration example (in YAML)::

    bundles:
        - tool.ext.jinja
    templates:
        searchpaths:
            - /home/www/some_site/templates/

"""

from copy import deepcopy
from functools import wraps
from jinja2 import Environment, FileSystemLoader
from werkzeug import Response
from tool import context
from tool.routing import url_for
from tool import signals
from tool.application import request_ready


DEFAULT_PATH = 'templates'


# Template rendering

def render_template(template_path, **extra_context):
    assert hasattr(context, 'jinja_env'), (
        'Jinja environment must be initialized. Make sure the bundle\'s setup '
        'function is called.')
    template = context.jinja_env.get_template(template_path)
    return template.render(extra_context)

def render_response(template_path, mimetype='text/html', **extra_context):
    return Response(
        render_template(template_path, **extra_context),
        mimetype=mimetype,
    )

def as_html(template_path):
    """
    Decorator for views. Renders
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

def setup(app):
    conf = deepcopy(app.settings.get('templates', {}))

    # TODO: per bundle?
    #conf = dict(conf).setdefault('paths', ['templates'])

    #tmpl_paths = conf.get('paths', [])    #getattr(context, 'template_paths', [])
    #tmpl_paths.append('templates')    # TODO: per bundle?
    #context.template_paths = tmpl_paths

    try:
        paths = conf.pop('searchpaths')
    except IndexError:
        paths = []
    paths.append(DEFAULT_PATH)

    loader = FileSystemLoader(paths)

    context.jinja_env = Environment(loader=loader, **conf)

    @signals.connected(request_ready, weak=False)
    def update_jinja_env(*args, **kwargs):
        default_globals = dict(
            url_for=url_for,
            request=context.request
        )
        globals = dict(default_globals, **conf.get('globals', {}))

        if globals:
            context.jinja_env.globals.update(globals)

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
