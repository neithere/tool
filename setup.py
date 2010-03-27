#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import tool


setup(
    name = "tool",
    version = tool.__version__,
    packages = find_packages(),

    install_requires = [
        'opster >= 0.9.9',  # console interface
        'werkzeug >= 0.6',  # web interface
        'pyyaml >= 3.08',   # configuration
    ],

    # metadata for upload to PyPI
    author = "Andrey Mikhaylenko",
    author_email = "andy@neithere.net",
    description = "A compact modular web/console framework.",
    license = "GPL3",
    keywords = "web framework",
)
