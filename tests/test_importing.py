# -*- coding: utf-8 -*-

import unittest
from tool.importing import *


class ImportingTestCase(unittest.TestCase):
    def test_import_module(self):
        "import_module works"
        mod = import_module('os.path')
        assert hasattr(mod, 'abspath')

    def test_import_attribute(self):
        "import_attribute works"
        attr = import_attribute('os.path.abspath')
        assert attr.__name__ == 'abspath'
        assert hasattr(attr, '__call__')
        self.assertRaises(AttributeError, lambda: import_attribute('os'))

    def test_import_whatever(self):
        "import_whatever works"
        mod = import_whatever('os.path')
        assert hasattr(mod, 'abspath')

        attr = import_whatever('os.path.abspath')
        assert attr.__name__ == 'abspath'
        assert hasattr(attr, '__call__')

        self.assertRaises(ImportError, lambda: import_whatever('os.llama'))

