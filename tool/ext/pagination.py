# -*- coding: utf-8 -*-

"""
Pagination utilities. Based on the Werkzeug tutorial.
"""

from werkzeug import cached_property, Href
from tool.routing import BuildError, url_for


class Pagination(object):

    def __init__(self, query, per_page, page, endpoint):
        self.query = query
        self.per_page = int(per_page)
        self.page = int(page)
        self.endpoint = endpoint

    @cached_property
    def count(self):
        return len(self.query)

    @cached_property
    def entries(self):
        offset = self.per_page * (self.page - 1)
        limit = self.per_page + offset
        return self.query[offset:limit]

    def _get_page_url(self, page):
        try:
            # page is a part of URL: /foo/page1/
            return url_for(self.endpoint, page=page)
        except BuildError:
            # page is just a param: /foo?page=x
            href = Href('.')    #url_for(self.endpoint))
            return href(page=page)


    has_previous = property(lambda x: x.page > 1)
    has_next = property(lambda x: x.page < x.pages)
    previous = property(lambda x: x._get_page_url(x.page - 1))
    next = property(lambda x: x._get_page_url(x.page + 1))
    pages = property(lambda x: max(0, x.count - 1) // x.per_page + 1)
