import hvplot.pandas  # noqa: F401
from pyabc2 import Pitch

import panel as pn
from stringcalc.tension import load_data, suggest_gauge

WIDTH = 450

DATA_ALL = load_data()
# TYPE_OPTIONS = sorted(DATA_ALL.group_id.cat.categories)
TYPE_OPTIONS = ["PB", "PL", "LE", "LEW", "NYL", "NYLW"]
TYPE_DEFAULTS = ["PB", "PL"]


# tension_input = pn.widgets.TextInput(name="Tension", placeholder="Enter tension in lbf...")
tension_input = pn.widgets.FloatSlider(
    name="Tension (lbf)", start=1, end=40, step=0.2, value=16, width=int(WIDTH * 2 / 3)
)

# length_input = pn.widgets.TextInput(name="Scale length", placeholder="Enter scale length in inches...")
length_input = pn.widgets.FloatSlider(
    name="Scale length (in)", start=10, end=50, step=0.1, value=22.5, width=int(WIDTH * 2 / 3)
)

# pitch_input = pn.widgets.TextInput(name="Pitch", placeholder="Enter SPN pitch...")
pkn_input = pn.widgets.DiscreteSlider(
    name="Pitch (piano key number)", options=list(range(1, 101)), value=35, width=int(WIDTH * 2 / 3)
)

types_input = pn.widgets.CheckBoxGroup(
    name="String types", options=TYPE_OPTIONS, value=TYPE_DEFAULTS, inline=True
)

n_input = pn.widgets.IntSlider(
    name="Number of suggestions", start=1, end=10, value=5, width=int(WIDTH / 3)
)


@pn.depends(tension_input, length_input, pkn_input, types_input, n_input)
def table(T, L, pkn, types, n):
    pitch = Pitch(pkn + 8).name
    df = suggest_gauge(T=T, L=L, pitch=pitch, types=types, n=n)

    return pn.Column(
        pn.pane.Markdown(f"**Pitch:** {pitch}"),
        df.hvplot.table(sortable=True, selectable=True, width=WIDTH),
    )


pn.Column(
    tension_input,
    length_input,
    pkn_input,
    n_input,
    types_input,
    table,
    width=WIDTH,
).servable()
