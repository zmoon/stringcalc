===
CLI
===

For example, ``stringcalc gauge --suggest`` can be used to suggest strings.
``-T``, ``-L``, ``-P`` (tension, scale length, pitch)
can be specified more than once to get results for multiple strings.

With `uv <https://docs.astral.sh/uv/>`__, you can install ``stringcalc`` globally with::

   uv tool install stringcalc[cli]

or run it in an ephemeral environment with::

   uvx stringcalc[cli]

Commands
--------

.. typer:: stringcalc.cli:app
   :prog: stringcalc
   :width: 87
   :show-nested:
   :make-sections:
   :preferred: html
   :iframe-height: 380
   :markup-mode: markdown

SVG export
----------

Set the ``STRINGCALC_RICH_EXPORT`` environment variable
to save a command's output as an SVG
(``1`` for ``stringcalc-rich-export.svg``, or a path).

If `fontTools <https://fonttools.readthedocs.io/>`__ is installed,
the font (subset to the characters used) is embedded in the SVG,
so that it renders correctly where remote fonts are blocked,
e.g. when the SVG is shown as an image in a GitHub or PyPI README.
Set ``STRINGCALC_RICH_EXPORT_EMBED_FONT=0`` to disable this
or ``=1`` to error if embedding is not possible.
