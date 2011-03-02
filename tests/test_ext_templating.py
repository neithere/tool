# -*- coding: utf-8 -*-

import jinja2
import pydispatch#.errors import DispatcherKeyError
import unittest
import werkzeug
from tool import Application
#from tool.application import app_manager_ready, request_ready
#from tool import signals
from tool.ext.templating import render_response, as_html


PLUGIN = 'tool.ext.templating.JinjaPlugin'


class FunctionsTestCase(unittest.TestCase):
    def setUp(self):
        conf = {
            'extensions': {
                PLUGIN: {
                    'searchpaths': ['tests/data_ext_templating/']}}}
        # this should trigger tool.ext.templating.setup:
        self.app = Application(conf)
        self.ext = self.app.get_extension(PLUGIN)

    def test_initialized(self):
        assert 'templating_env' in self.ext.env

    def test_render_template(self):
        "file + context = html"
        result = self.ext.render_template('tmpl.html', dict(foo='bar'))
        self.assertEquals(result, 'foo is "bar".')

    def test_render_response(self):
        "file + context = response object"
        result = render_response('tmpl.html', foo='bar')
        assert isinstance(result, werkzeug.Response)
        self.assertEquals(result.data, 'foo is "bar".')

    def test_as_html_dictionary(self):
        @as_html('tmpl.html')
        def my_view(foo=None):
            if foo:
                return {'foo': foo}
            else:
                return werkzeug.Response('no foo!')

        # magic attributes must be kept
        self.assertEquals(my_view.__name__, 'my_view')

        # try the branch that returns the context
        result = my_view(foo='bar')
        assert isinstance(result, werkzeug.Response)
        self.assertEquals(result.data, 'foo is "bar".')

        # try the branch that returns a Response object
        result = my_view()
        assert isinstance(result, werkzeug.Response)
        self.assertEquals(result.data, 'no foo!')

        # we've only tested cases when a Response object is returned; the view
        # function can return anything else and it will come as is. We just
        # consider these cases not valuable and not worth even being
        # documented so `as_html` can change the implementation freely.

    def test_templating_env(self):
        "Jinja environment is updated when Request object is ready"
        #assert hasattr(context, 'templating_env')

        # the Jinja env is expected to be not populated yet
        tmpl = self.ext.env['templating_env'].from_string('request: {{ request }}')
        expected = 'request: '
        self.assertEquals(tmpl.render(), expected)

        """ TODO(?):

        # let's compile the WSGI app by calling the app manager the 1st time
        fake_env = werkzeug.create_environ()
        start_response = lambda x,y:None #werkzeug.Response()
        self.app(fake_env, start_response)

        # not we expect the Jinja environment to be populated
        # because it has been waiting for the request_ready signal
        tmpl = self.ext.env['templating_env'].from_string('request: {{ request }}')
        expected = '''request: <Request 'http://localhost/' [GET]>'''
        self.assertEquals(tmpl.render(), expected)

        """
