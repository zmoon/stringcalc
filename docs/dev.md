<!--pytest-codeblocks:skipfile-->

# Development

## Setup

Using [uv](https://docs.astral.sh/uv/), prepare the Python venv:

```sh
uv sync --all-groups --all-extras
```

To update an existing venv, add `--upgrade`.

Install frontend dependencies (requires Node.js 20+):

```sh
npm --prefix frontend ci
```

## Testing

Run the Python tests:

```sh
uv run pytest
```

Run frontend typecheck and unit tests:

```sh
npm --prefix frontend run typecheck
npm --prefix frontend test
```

## Web app & widgets

Build the `anywidget` bundle (`stringcalc/widget/_bundle.js`) and standalone web apps (with local wheel for Pyodide):

```sh
uv run python scripts/build_web.py --source local --out docs/_static/app
```

To target the PyPI release of `stringcalc` instead of the local wheel, pass `--source pypi`.
For live frontend development with Vite HMR:

```sh
uv run python scripts/build_web.py --wheel-only
npm --prefix frontend run dev
```

## Docs & versioning

Regenerate the committed CLI example SVGs (only needed when updating them):

```sh
uv run python docs/make_cli_svgs.py
```

Build the docs:

```sh
uv run sphinx-build docs docs/_build/html
```

To preview the built docs locally (serving over HTTP so the embedded web app loads):

```sh
uv run python -m http.server --directory docs/_build/html
```

Check the version:

```sh
uv run stringcalc --version
```

After adding a new annotated version tag,
you may need to touch one of the files
in order for uv/hatch to detect that a rebuild is needed,
or use:

```sh
uv run --reinstall-package stringcalc stringcalc --version
```
