# -*- coding: utf-8 -*-

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from werkzeug import generate_password_hash, check_password_hash
from docu import *
# FIXME: commented out to avoid circular import; reorganize the code there
#from tool.ext.admin import with_admin


#@with_admin(namespace='auth')
class User(Document):
    username = Field(unicode, required=True)
    password = Field(unicode, required=True)

    validators = {
        'username': [validators.Length(min=2, max=16)],
    }

    def __unicode__(self):
        return u'{username}'.format(**self)

    def set_password(self, raw_password):
        self.password = unicode(generate_password_hash(raw_password))

    def check_password(self, raw_password):
        assert self.password and '$' in self.password, 'bad stored password'
        return check_password_hash(self.password, raw_password)
