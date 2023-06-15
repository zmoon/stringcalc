project = "stringcalc"
copyright = "2022\u20132023 zmoon"
author = "zmoon"

release = "0.1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    # "sphinx.ext.doctest",
    # "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    # "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    # "sphinx.ext.viewcode",
    # "sphinx_jinja",
    "sphinx_click",
    "myst_parser",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

exclude_patterns = ["_build"]

html_title = "stringcalc"
html_theme = "sphinx_book_theme"

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_preprocess_types = True
napoleon_use_param = True
napoleon_use_rtype = False


autodoc_typehints = "description"
autosummary_generate = True
