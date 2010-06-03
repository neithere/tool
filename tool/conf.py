# -*- coding: utf-8 -*-

"""
The configuration is just a dictionary. It may come from different sources and
in different formats, so we just provide some shortcuts to simplify things.
"""

import os.path
from tool.importing import import_attribute

__all__ = ['ConfigurationError', 'load']


FORMATS = {
    'yaml': 'yaml.load',
    'json': 'json.loads',
}


class ConfigurationError(Exception):
    pass


def load(path, format=None):
    """
    Expects a filename, returns a dictionary. Raises ConfigurationError if
    the file could not be read or parsed.

    :param path: path to the file.
    :param format: format in which the configuration dictionary in serialized
        in the file (one of: "yaml", "json").

    """
    if not os.path.exists(path):
        raise ConfigurationError('File "%s" does not exist' % path)

    # guess file format
    if not format:
        for known_format in FORMATS:
            if path.endswith('.%s' % known_format):
                format = known_format
                break
        else:
            raise ConfigurationError('Could not guess format for "%s"' % path)
    assert format in FORMATS, 'unknown format %s' % format

    # deserialize file contents to a Python dictionary
    try:
        f = open(path)
    except IOError as e:
        raise ConfigurationError('Could not open "%s": %s' % (path, e))
    data = f.read()
    try:
        loader = import_attribute(FORMATS[format])
    except ImportError as e:
        raise ConfigurationError('Could not import "%s" format loader: %s'
                                 % (format, e))
    try:
        conf = loader(data)
    except Exception as e:
        raise ConfigurationError('Could not deserialize config data: %s' % e)

    if not isinstance(conf, dict):
        raise ConfigurationError('Deserialized config must be a dict, got "%s"'
                                 % conf)
    return conf
