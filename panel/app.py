import hvplot.pandas  # noqa: F401
from bokeh.models.formatters import PrintfTickFormatter
from pyabc2 import Pitch

import panel as pn
from stringcalc.tension import load_data, suggest_gauge

WIDTH = 450

DATA_ALL = load_data()
# TYPE_OPTIONS = sorted(DATA_ALL.group_id.cat.categories)
TYPE_OPTIONS = ["PB", "PL", "LE", "LEW", "NYL", "NYLW", "NNG", "WFC"]
TYPE_DEFAULTS = ["PB", "PL"]


tension_input = pn.widgets.FloatSlider(
    name="Tension",
    start=1,
    end=40,
    step=0.2,
    value=16,
    width=int(WIDTH * 2 / 3),
    format=PrintfTickFormatter(format="%.1f lbf"),
)

length_input = pn.widgets.FloatSlider(
    name="Scale length",
    start=10,
    end=50,
    step=0.1,
    value=22.5,
    width=int(WIDTH * 2 / 3),
    format=PrintfTickFormatter(format='%.1f"'),
)

pitch_input = pn.widgets.DiscreteSlider(
    name="Pitch",
    options=[Pitch(pkn + 8).name for pkn in range(1, 101)],
    value="D3",
    width=int(WIDTH * 2 / 3),
)

types_input = pn.widgets.CheckBoxGroup(
    name="String types",
    options=TYPE_OPTIONS,
    value=TYPE_DEFAULTS,
    inline=True,
)

n_input = pn.widgets.IntSlider(
    name="Number of suggestions",
    start=1,
    end=10,
    value=5,
    width=int(WIDTH / 3),
)


@pn.depends(tension_input, length_input, pitch_input, types_input, n_input)
def table(T, L, pitch, types, n):
    df = suggest_gauge(T=T, L=L, pitch=pitch, types=types, n=n)

    return pn.Column(
        pn.pane.Markdown(f"**Pitch:** {pitch}"),
        df.hvplot.table(sortable=True, selectable=True, width=WIDTH),
    )


pn.Column(
    tension_input,
    length_input,
    pitch_input,
    n_input,
    types_input,
    table,
    width=WIDTH,
).servable()
