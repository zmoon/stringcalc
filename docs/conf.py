project = "stringcalc"
copyright = "2022\u20132023 zmoon"
author = "zmoon"

release = "0.1"

extensions = [
    "sphinx.ext.autodoc",
    # "sphinx.ext.doctest",
    # "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    # "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    # "sphinx.ext.viewcode",
    # "sphinx_immaterial.theme_result",
    # "sphinx_immaterial.kbd_keys",
    "sphinx_immaterial.apidoc.format_signatures",
    # "sphinx_immaterial.apidoc.json.domain",
    "sphinx_immaterial.apidoc.python.apigen",
    # "sphinx_immaterial.graphviz",
    # "sphinx_jinja",
    "myst_parser",
    "sphinx_immaterial",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

exclude_patterns = ["_build"]

html_title = "stringcalc"
html_theme = "sphinx_immaterial"

python_apigen_modules = {
    "stringcalc.tension": "api/",
}

python_apigen_default_groups = [
    ("class:.*", "Classes"),
    (r".*:.*\.__(init|new)__", "Constructors"),
    (r".*:.*\.__eq__", "Comparison operators"),
    (r".*:.*\.__(str|repr)__", "String representation"),
]

python_apigen_rst_prolog = """
.. default-role:: py:obj

.. default-literal-role:: python

.. highlight:: python
"""
