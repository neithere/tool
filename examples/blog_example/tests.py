"""
Functional tests
================

This module tests the blog's web interface.

See also documentation for :module:`blog.commands` for command-line interface
doctests.
"""
import unittest2
from webtest import TestApp
from tool import ApplicationManager
from tool.ext.documents import default_storage


class BlogTestCase(unittest2.TestCase):
    def setUp(self):
        self.app = ApplicationManager('test_conf.yaml')
        self.www = TestApp(self.app)
        self.clear_db()

    def tearDown(self):
        self.clear_db()

    def clear_db(self):
        # clean up the test database
        db = self.app.plugins['tool.ext.documents'].env['default']
        db.clear()
        db.disconnect()

    def call(self, command):
        args = command.split()
        return self.app.dispatch(args)

    def test_adding(self):
        "User can add a note via command line and view it on the web."
        print self.www.get('/')
        assert 'There are no notes' in self.www.get('/')
        self.call('blog add hello')
        assert 'hello' in self.www.get('/')
        assert 'hello' in self.www.get('/').click('hello')

    def test_listing(self):
        "The list of notes is identical via CL and web interfaces."
        assert 'There are no notes' in self.www.get('/')

        self.call('blog add hello')
        assert 'There are 1 notes' in self.www.get('/')
        assert 'hello' in self.www.get('/')

        self.call('blog add ponies')
        assert 'There are 2 notes' in self.www.get('/')
