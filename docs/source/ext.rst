Extensions
==========

Tool is a general purpose framework. It does not impose a certain stack of
technologies related to data storage, templating and so on. Still, Tool has
some batteries included. The glue code comes in "bundles" (Python modules with
optional setup functions). When you need to activate a certain extension, just
include its dotted path in the configuration like this (a YAML example)::

    bundles:
        - tool.ext.models
        - tool.ext.jinja

Below is the full list of bundled extensions.

.. toctree::

   ext_admin
   ext_auth
   ext_jinja
   ext_models
   ext_pagination
