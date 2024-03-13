Conda env setup for development:

    mamba env create -f environment.yml
    conda activate stringcalc-panel
    pip install -e ../ --no-deps

For development:

    panel serve --autoreload --show app.py

Create deployable HTML file
(first set env var `PYTHONUTF8` to `1` for Windows):

    panel convert app.py --to pyodide
