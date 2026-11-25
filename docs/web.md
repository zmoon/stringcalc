# Web

_Web app and notebook widgets_

stringcalc ships interactive tools built as shared Web Components:

- **Standalone web apps** powered by Python in the browser (via Pyodide):
  <!-- Keep raw HTML <a> tags: Sphinx rewrites Markdown links to _static/ into _downloads/<hash>/, breaking relative JS/CSS paths. -->
  - <a href="_static/app/index.html" target="_blank" rel="noopener">Open Gauge Suggest app</a>
  - <a href="_static/app/misc.html" target="_blank" rel="noopener">Open Misc Tools app</a> (Exact gauge, Frets, Scale length)
- **Local web app** backed directly by your local Python installation (instant startup, works offline):
  ```{code} console
  $ stringcalc app
  ```
  (requires `stringcalc[cli]`; pass `--no-open` to skip opening the browser)
- **Notebook widgets** via `anywidget` (`stringcalc[widget]`), using the same UI.

## Notebook widgets

Install the optional `widget` extra:

```{code} console
$ pip install stringcalc[widget]
```

Then display any widget from {mod}`stringcalc.widget` in JupyterLab, VS Code notebooks, or Marimo.
For example:

```{code} python
from stringcalc.widget import FretsWidget

w = FretsWidget(L=25)
w
```

Changes made in the widget stay synced with Python.
For example, you can inspect the fret positions as a pandas DataFrame with `w.to_dataframe()`,
or update inputs from another cell (such as `w.length_unit = "mm"` or `w.N = 22`).
