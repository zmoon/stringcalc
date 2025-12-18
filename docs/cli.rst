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

.. click:: stringcalc.cli:_typer_click_object
   :prog: stringcalc
   :nested: full
