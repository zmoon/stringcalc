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

Build the `anywidget` bundle (`stringcalc/widget/_bundle.js`),
packaged local web assets (`stringcalc/_web/`),
and standalone Pyodide web apps for the docs:

```sh
uv run python scripts/build_web.py --out docs/_static/app
```

## Web app & widgets

For live frontend development with Vite HMR:

```sh
uv run python scripts/build_web.py --wheel-only
npm --prefix frontend run dev
```

To run the local Python-backed web app (no Pyodide or wheel rebuild needed after Python edits):

```sh
uv run stringcalc app
```

## Testing

Run the Python tests:

```sh
uv run pytest
```

Run frontend type-check and unit tests:

```sh
npm --prefix frontend run typecheck
npm --prefix frontend test
```

## Docs

Regenerate the committed CLI example SVGs (only needed when updating them):

```sh
uv run python docs/make_cli_svgs.py
```

Build the docs:

```sh
uv run sphinx-build docs docs/_build/html
```

To preview the built docs locally (serving over HTTP so the standalone web apps load):

```sh
uv run python -m http.server --directory docs/_build/html
```

## Releases & deployment

### PyPI

Pushing an annotated `v*` tag triggers Trusted Publishing to PyPI in GitHub Actions,
assuming the build and test jobs pass.

For example (on the `main` branch):

```sh
git tag -a v0.2.0 -m "v0.2.0"
git push --follow-tags
```

Note that for the tag to be picked up in your local `stringcalc` by uv/hatch,
you may need to use `--reinstall-package` or similar.
For example:

```sh
uv run --reinstall-package stringcalc stringcalc --version
```

### GitHub Pages

Pushes to `main` (and manual `workflow_dispatch` runs on `main`) deploy the standalone Pyodide web apps.

### Read the Docs

Read the Docs builds documentation and versioned copies of the standalone web apps.
