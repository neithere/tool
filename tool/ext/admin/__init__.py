# -*- coding: utf-8 -*-
"""
Web Admin
=========

:state: beta
:dependencies: `Docu`_

Administrative interface for `Docu`_. Requires :mod:`tool.ext.documents` to be
properly set up.

Complete configuration example (see :doc:`application` for details)::

    settings = dict(
        bundles = {'tool.ext.documents': None}
    )
    app = ApplicationManager(settings)
    app.add_urls('tool.ext.admin', '/admin/')

.. _Docu: http://pypi.python.org/pypi/docu

"""
import os

from tool import dist
dist.check_dependencies(__name__)

#from tool.application import app_manager_ready
from tool import context
from tool import routing
from tool.ext.templating import register_templates

from views import *


register_templates(__name__)


