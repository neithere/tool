# -*- coding: utf-8 -*-

import unittest
from tool.ext import strings


class SlugifyTestCase(unittest.TestCase):
    def test_slugify(self):
        "slugify() converts the string correctly"
        self.assertEqual(strings.slugify(u' Hello world!..  '), u'hello-world')

    def test_slugify_i18n(self):
        "slugify_i18n() transliterates and slugifies the string"
        self.assertEqual(strings.slugify_i18n(u' Hello! Привет, мир!..  '),
                         u'hello-priviet-mir')
