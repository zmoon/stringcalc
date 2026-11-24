# Web app & notebook widgets

stringcalc ships interactive tools built as shared Web Components:

- **Standalone web apps** powered by Python in the browser (via Pyodide):
  - <a href="_static/app/index.html" target="_blank" rel="noopener">Open Gauge Suggest app (full screen)</a>
  - <a href="_static/app/misc.html" target="_blank" rel="noopener">Open Misc Tools app (Exact gauge, Frets, Scale length)</a>
- **Local web app** backed directly by your local Python installation (instant startup, works offline):
  `stringcalc app` (requires `pip install stringcalc[cli]`; pass `--no-open` to skip opening the browser).
- **Notebook widgets** via `anywidget` (`pip install stringcalc[widget]`), using the same UI backed by your live Python kernel.

## Embedded Gauge Suggest app

```{raw} html
<iframe
  src="_static/app/index.html"
  title="stringcalc Gauge Suggest app"
  style="width: 100%; height: 760px; border: 1px solid rgba(128, 128, 128, 0.25); border-radius: 8px;"
></iframe>
```

## Notebook widgets (`anywidget`)

Install the optional `widget` extra:

```
pip install stringcalc[widget]
```

Then display any widget in JupyterLab, VS Code notebooks, or Marimo:

<!--pytest.mark.skip-->

```python
from stringcalc.widget import (
    ExactGaugeWidget,
    FretsWidget,
    GaugeSuggestWidget,
    ScaleLengthWidget,
)

w = GaugeSuggestWidget(preset="tenor-banjo-4-irish")
w
```

Changes made in the widget stay synced with Python.
For example, you can inspect the suggested gauges as pandas DataFrames with `w.to_dataframes()`,
or update inputs from another cell (such as `w.tension_unit = "kgf"`).
