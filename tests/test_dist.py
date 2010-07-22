# -*- coding: utf-8 -*-

import unittest
from tool import dist


class DistTestCase(unittest.TestCase):
    #
    # XXX WARNING: this test assumes that all dependencies are satisfied.
    #              it is also bound to certain setup.py configuration.
    #
    def test_existing_entry_point(self):
        "existing entry point is checked correctly"
        # module
        dist.check_dependencies('tool.ext.documents')
        # module and attribute
        dist.check_dependencies('tool.ext.strings', 'slugify_i18n')

    def test_wrong_entry_point(self):
        "non-existant entry point raises NameError"
        # wrong module
        self.assertRaises(NameError,
            lambda: dist.check_dependencies('foo.bar.muahaha'))
        # correct module, wrong attribute
        self.assertRaises(NameError,
            lambda: dist.check_dependencies('tool.ext.documents', 'foobar'))
