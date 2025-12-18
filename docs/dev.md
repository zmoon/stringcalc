# Development

Using [uv](https://docs.astral.sh/uv/), prepare the venv:

```sh
uv sync --all-groups --all-extras
```

Run the tests:

```sh
uv run pytest
```

Build the Panel app (for inclusion in the docs):

```sh
uv run panel convert panel/app.py --to pyodide --out docs/_static/panel/
```

Build the docs:

```sh
uv run sphinx-build docs docs/_build/html
```
