===
CLI
===

For example, ``stringcalc gauge --suggest`` can be used to suggest strings.
``-T``, ``-L``, ``-P`` (tension, scale length, pitch)
can be specified more than once to get results for multiple strings.

.. click:: stringcalc.cli:_typer_click_object
   :prog: stringcalc
   :nested: full
