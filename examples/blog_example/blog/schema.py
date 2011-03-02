# -*- coding: utf-8 -*-

import datetime
from docu import Document
from docu.validators import required

from tool.routing import url_for
from tool.ext.admin import register
from tool.ext.strings import slugify


@register
class Note(Document):
    structure = {
        'slug': unicode,
        'text': unicode,
        'date': datetime.date,
    }
    validators = {
        'text': [required()],
    }
    defaults = {
        'date': datetime.date.today,
        'slug': lambda obj: slugify(obj.text),
    }
    use_dot_notation = True

    def __unicode__(self):
        return unicode(self.text[:50] or 'empty')

    def get_url(self):
        # NOTE: you can call `url_for` directly from the templates
        if not self.date:
            return ''
        return url_for('blog.views.note',
                       year=self.date.year,
                       month='{0:02}'.format(self.date.month),
                       slug=self.slug)
