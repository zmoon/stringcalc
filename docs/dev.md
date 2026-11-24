# Development

Using [uv](https://docs.astral.sh/uv/), prepare the venv:

```sh
uv sync --all-groups --all-extras
```

To update an existing venv, add `--upgrade`.

Run the tests:

```sh
uv run pytest
```

Install frontend dependencies (requires Node.js 20+):

<!--pytest.mark.skip-->

```sh
npm --prefix frontend ci
```

Build the `anywidget` bundle and standalone web apps (with local wheel for Pyodide):

<!--pytest.mark.skip-->

```sh
uv run python scripts/build_web.py --source local --out docs/_static/app
```

To target the PyPI release of `stringcalc` instead of the local wheel, pass `--source pypi`.
For live frontend development with Vite HMR:

<!--pytest.mark.skip-->

```sh
uv run python scripts/build_web.py --wheel-only
npm --prefix frontend run dev
```

Run frontend checks:

<!--pytest.mark.skip-->

```sh
npm --prefix frontend run typecheck
npm --prefix frontend test
```

Regenerate the committed CLI example SVGs (only needed when updating them):

```sh
uv run python docs/make_cli_svgs.py
```

Build the docs:

```sh
uv run sphinx-build docs docs/_build/html
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
