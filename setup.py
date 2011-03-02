#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from _version import version


setup(
    name = 'tool',
    version = version,
    packages = find_packages(),
    package_data = {
        'tool': ['ext/*/*/*.html'],
    },

    install_requires = [
        'argh >= 0.2.0',         # console interface
        'pydispatcher >= 2.0.1', # signals
        'pyyaml >= 3.08',        # configuration
    ],
    test_suite = 'nose.collector',
    tests_require = ['coverage >= 3.3', 'nose >= 0.11'],

    # optional features
    extras_require = {
        'dark': ['dark >= 0.7'],
        'doqu': ['doqu >= 0.25'],
        'jinja': ['jinja2 >= 2.5'],
        'repoze.who': ['repoze.who >= 1.0'], #2.0a2'],
        'repoze.what': ['repoze.what >= 1.0'],
        'unidecode': ['unidecode >= 0.04.1'],
        'werkzeug': ['werkzeug >= 0.6'],       # web interface
        'wtforms': ['wtforms >= 0.6'],
        'colorama': ['colorama >= 0.1.18'],    # CLI colors
    },
    entry_points = {
        'extensions': [
            'admin = tool.ext.admin [doqu, wtforms]',
            'analysis = tool.ext.analysis [dark, doqu, wtforms]',
            'documents = tool.ext.documents [doqu]',
            'templating = tool.ext.templating [jinja]',
            'slugify_i18n = tool.ext.strings:slugify_i18n [unidecode]',
            'who = tool.ext.who [repoze.who]',
            'what = tool.ext.what [repoze.what]',
        ]
    },

    # metadata for upload to PyPI
    author = 'Andrey Mikhaylenko',
    author_email = 'andy@neithere.net',
    description = 'A compact modular conf/web/console framework.',
    long_description='A compact modular conf/web/console framework.',
    license = 'GPL3',
    keywords = 'wsgi web framework',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
