# -*- coding: utf-8 -*-
"""
Authentication
==============

:state: alpha
:dependencies: Docu_

.. _Docu: http://pypi/python.org/pypi/docu

"""

# python
from functools import wraps
from werkzeug import Response
from schema import User
from tool import context

# FIXME let user configure databases per bundle
from tool.ext.documents import db


# taken from / inspired by: http://flask.pocoo.org/snippets/8/

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    accounts = User.objects(db).where(username=username)
    assert len(accounts) <= 1, (
        'Expected 0 or 1 users with username {username}'.format(**locals()))
    if not accounts:
        return False
    u = accounts[0]
    return u.check_password(password)


def authenticate():
    """Sends a 401 response that enables basic auth"""
    # TODO: make this configurable:
    # * basic auth (available now)
    # * redirect to a login view with form (N/A)
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(request, *args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(request, *args, **kwargs)
    return decorated
