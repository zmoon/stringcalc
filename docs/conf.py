import stringcalc

project = "stringcalc"
copyright = "2022\u20132025"
author = "zmoon"

version = stringcalc.__version__.split("+")[0]
release = stringcalc.__version__

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
    "sphinx_copybutton",
    # "myst_parser",
    "myst_nb",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "pint": ("https://pint.readthedocs.io/en/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

exclude_patterns = ["_build"]

suppress_warnings = [
    "autosummary.import_cycle",
]

html_title = "stringcalc"
html_theme = "sphinx_book_theme"

html_theme_options = {
    "path_to_docs": "docs/",
    "repository_url": "https://github.com/zmoon/stringcalc",
    "repository_branch": "main",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "use_download_button": False,
    "extra_footer": f"""\
    <span style="font-size: 0.8em;">stringcalc version in this docs build:
    <strong>{version}</strong>.</span>
    """,
}

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_preprocess_types = True
napoleon_use_param = True
napoleon_use_rtype = False

autodoc_typehints = "description"
autosummary_generate = True

nb_execution_raise_on_error = True
