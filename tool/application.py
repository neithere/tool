# -*- coding: utf-8 -*-

from werkzeug import Response, Request, responder, run_simple

from tool.commands import command
from tool.context import context


def make_app(url_map, with_commands=True):
    def find_and_call_view(endpoint, v):
        # NOTE: this supports only callable endpoints
        assert hasattr(endpoint, '__call__')
        return endpoint(context.request, **v)
        #f = context.views.get_view(endpoint)
        # return f(request, **v)

    @responder
    def app(environ, start_response):
        context.request = Request(environ)
        context.urls = url_map.bind_to_environ(environ)

        return context.urls.dispatch(find_and_call_view,
                                     catch_http_exceptions=True)

    if with_commands:
        register_commands(app)

    return app

def register_commands(app):
    """
    Registers default commands for application management.
    """
    @command()
    def run(host=('h', 'localhost', 'host'), port=('p', 6060, 'port')):
        """
        Runs development server for your application.
        """
        run_simple(host, port, app)
