For development:

    uv run panel serve --autoreload --show app.py

Create deployable HTML file
(first set env var `PYTHONUTF8` to `1` for Windows):

    uv run panel convert app.py --to pyodide
