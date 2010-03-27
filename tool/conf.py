# -*- coding: utf-8 -*-

"""
The configuration is just a dictionary. It may come from different sources and
in different formats, so we just provide some shortcuts to simplify things.
"""

import yaml


YAML = 'yaml'
FORMATS = [YAML]


def load(source, format=YAML):
    assert format in FORMATS, 'unknown format %s' % format

    # dict -> :)
    if isinstance(source, dict):
        return source

    # file -> string
    if isinstance(source, file):
        source = source.read()

    # string -> dict -> :)
    if isinstance(source, basestring):
        conf = yaml.load(source)
        assert isinstance(conf, dict), (
            'expected dict from deserialized config, got %s' % conf)
        return conf
