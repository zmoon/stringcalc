import re
from typing import Any

import stringcalc

project = "stringcalc"
copyright = "2022\u20132026"
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

html_static_path = ["_static"]

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_preprocess_types = True
napoleon_use_param = True
napoleon_use_rtype = False

autodoc_typehints = "description"
autosummary_generate = True

nb_execution_raise_on_error = True

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True


def _inject_cli_docs(app: Any, docname: str, source: list[str]) -> None:
    if docname != "cli":
        return

    import typer
    from typer.cli import get_docs_for_click

    import stringcalc.cli

    assert stringcalc.cli.__file__ is not None
    app.env.note_dependency(stringcalc.cli.__file__, docname=docname)

    # Get CLI documentation using `typer.cli.get_docs_for_click` (backs `typer utils docs`);
    # update if Typer changes its signature or exposes a more public docs API.
    cmd = typer.main.get_command(stringcalc.cli.app)
    assert isinstance(cmd, typer.core.TyperGroup)
    ctx = typer.Context(cmd)
    md = get_docs_for_click(obj=cmd, ctx=ctx, indent=2, name="stringcalc").strip()

    # Wrap un-backticked --flags in Markdown prose so Sphinx renders them as inline code
    # instead of turning `--` into an en-dash, while keeping terminal `--help` free of backticks.
    md = re.sub(
        r"```.*?```|(`+).*?\1"
        r"""|(?<![\w`-])(?P<flag>--[a-zA-Z][\w-]*(?:=[^\s,.)'"`]+)?)(?![\w`-])""",
        lambda m: f"`{m['flag']}`" if m["flag"] else m.group(0),
        md,
        flags=re.DOTALL,
    )

    # Ensure all subcommands are documented
    for sub in cmd.list_commands(ctx):
        assert f"`stringcalc {sub}`" in md, f"Missing CLI docs for subcommand {sub!r}"

    # Inject
    placeholder = "<!-- typer-docs -->"
    if placeholder not in source[0]:
        raise RuntimeError(f"Missing {placeholder!r} placeholder in docs/cli.md")
    source[0] = source[0].replace(placeholder, md, 1)


def setup(app: Any) -> None:
    app.connect("source-read", _inject_cli_docs)
