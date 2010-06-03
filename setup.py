#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import tool


setup(
    name = 'tool',
    version = tool.__version__,
    packages = find_packages(),

    install_requires = [
        'opster >= 0.9.9',       # console interface
        'werkzeug >= 0.6',       # web interface
        'pydispatcher >= 2.0.1', # signals
        'pyyaml >= 3.08',        # configuration
    ],

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
