# -*- coding: utf-8 -*-
"""
Distribution internals
======================

These are some distribution-related routines. It is doubtful that you would
ever need them unless you are developing Tool itself.
"""
import pkg_resources


DEFAULT_GROUP = 'extensions'


def _get_entry_points(module_name, attr_name=None):
    """
    Returns an iterator on entry points for given module name and, optionally,
    attribute name.
    """
    group = DEFAULT_GROUP
    for entry_point in pkg_resources.iter_entry_points(group):
        if not entry_point.module_name == module_name:
            continue
        if attr_name and not attr_name in entry_point.attrs:
            continue
        yield entry_point

def check_dependencies(module_name, attr_name=None):
    """
    Checks module or attribute dependencies. Raises NameError if setup.py does
    not specify dependencies for given module or attribute.

    :param module_name:
        e.g. "tool.ext.jinja"
    :param attr_name:
        e.g. "slugify_i18n" from "tool.ext.strings:slugify_i18n"

    """
    entry_points = list(_get_entry_points(module_name, attr_name))
    if not entry_points:
        msg = 'There are no entry points for module "{module_name}"'
        if attr_name:
            msg += 'and attribute "{attr_name}"'
        raise NameError(msg.format(**locals()))
    for entry_point in entry_points:
        entry_point.require()
