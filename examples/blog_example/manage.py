#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tool import WebApplication

app = WebApplication('conf.yaml')

if __name__ == '__main__':
    from tool.debug import print_url_map
    print_url_map(app.get_feature('routing').env['url_map'])
    app.dispatch()
