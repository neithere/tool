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
        'opster >= 0.9.9',       # console interface
        'werkzeug >= 0.6',       # web interface
        'pydispatcher >= 2.0.1', # signals
        'pyyaml >= 3.08',        # configuration
    ],
    test_suite = 'nose.collector',
    tests_require = ['coverage >= 3.3', 'nose >= 0.11'],

    # optional features
    extras_require = {
        'dark': ['dark >= 0.4.1'],
        'docu': ['docu >= 0.22'],
        'jinja': ['jinja2 >= 2.5'],
        'repoze.who': ['repoze.who >= 2.0a2'],
        'unidecode': ['unidecode >= 0.04.1'],
        'wtforms': ['wtforms >= 0.6'],
    },
    entry_points = {
        'extensions': [
            'admin = tool.ext.admin [docu, wtforms]',
            'analysis = tool.ext.analysis [dark, docu, wtforms]',
            'documents = tool.ext.documents [docu]',
            'templating = tool.ext.templating [jinja]',
            'slugify_i18n = tool.ext.strings:slugify_i18n [unidecode]',
            'who = tool.ext.who [repoze.who]',
        ]
    },

    # metadata for upload to PyPI
    author = 'Andrey Mikhaylenko',
    author_email = 'andy@neithere.net',
    description = 'A compact modular web/console framework.',
    long_description='A compact modular web/console framework. Based on '
                     'Werkzeug+Pydispatcher+Opster.',
    license = 'GPL3',
    keywords = 'wsgi web framework',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
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
