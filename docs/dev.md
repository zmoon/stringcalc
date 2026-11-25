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

The [Lit Web Components](https://lit.dev/) in `frontend/src/components/` are shared across three surfaces,
all talking to `stringcalc/_app.py` (`METHODS` / `dispatch`) via `frontend/src/backend/index.ts`:

- **Standalone Pyodide apps**
  (`frontend/dist/app/`, copied to `docs/_static/app/` and deployed to GitHub Pages).
  Pass `?pkg=pypi` or `?pkg=local` in the URL to override `app-config.json` at runtime.
- **Local Python app**
  (`stringcalc/_web/`, served by `stringcalc app` via `stringcalc/_server.py`).
- **Notebook widgets**
  (`stringcalc/widget/_bundle.js`, loaded by `anywidget` wrappers in `stringcalc/widget/__init__.py`).

To run the local Python-backed web app
(fastest loop for Python edits, no JS or wheel rebuild needed):

```sh
uv run stringcalc app
```

After editing `frontend/src/`,
rebuild both packaged JS targets for `stringcalc app` and notebooks:

```sh
npm --prefix frontend run build
```

For live frontend development with Vite HMR (Pyodide mode):

```sh
uv run python scripts/build_web.py --wheel-only
npm --prefix frontend run dev
```

Things to keep in mind when modifying the frontend or widgets:

- **Adding an RPC method or tool**:
  update `METHODS` in `stringcalc/_app.py`,
  `MethodName` + `createBackend` in `frontend/src/backend/index.ts`,
  and `WIDGET_SPECS` in `frontend/src/entries/widgets-esm.ts` (for `anywidget`).
- **Synced defaults**:
  standalone apps read Lit `@property` defaults (`frontend/src/components/sc-*.ts`)
  and `DEFAULT_FANNED` (`frontend/src/types.ts`),
  while notebooks read traitlet defaults
  and `_DEFAULT_FANNED_IN` in `stringcalc/widget/__init__.py`.
  Keep them aligned.
- **Packaging**:
  `stringcalc/widget/_bundle.js` and `stringcalc/_web/` are gitignored
  and included via `[tool.hatch.build] artifacts`, which Hatch silently skips if missing.
  Run `npm --prefix frontend run build` before a manual `uv build`
  (CI verifies both wheel and sdist contents).
  `vite.config.ts` sets `publicDir: false` on build
  so `frontend/public/wheels/` never leaks into `stringcalc/_web/`.

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

Pushes to `main`, `v*` tags, and manual `workflow_dispatch` runs on `main`,
deploy the standalone Pyodide web apps.

### Read the Docs

Read the Docs builds documentation and versioned copies of the standalone web apps.
