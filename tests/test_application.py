# -*- coding: utf-8 -*-

import unittest
import tool


class ApplicationSettingsTestCase(unittest.TestCase):
    def test_empty(self):
        "Empty settings"
        m = tool.ApplicationManager()
        assert m.settings == {}

    def test_dict(self):
        "Settings as a dictionary"
        m = tool.ApplicationManager({})
        assert m.settings == {}

        m = tool.ApplicationManager({'foo': 123})
        assert m.settings == {'foo': 123}

    def test_filepath(self):
        "Settings as a path to a file"
        m = tool.ApplicationManager('tests/test_settings.yaml')
        assert m.settings == {'foo': 123, 'bar': ['baz', 'quux']}

    def test_wrong_type(self):
        "Settings type is checked"
        self.assertRaises(TypeError, lambda: tool.ApplicationManager(123))
