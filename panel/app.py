import hvplot.pandas  # noqa: F401
from bokeh.models.formatters import PrintfTickFormatter
from pyabc2 import Pitch

import panel as pn
from stringcalc.frets import distances
from stringcalc.tension import DENSITY_LB_IN, gauge, load_data, suggest_gauge

WIDTH = 450

DATA_ALL = load_data()
# TYPE_OPTIONS = sorted(DATA_ALL.group_id.cat.categories)
TYPE_OPTIONS = ["PB", "PL", "LE", "LEW", "NYL", "NYLW", "NNG", "WFC"]
TYPE_DEFAULTS = ["PB", "PL"]


def suggest_gauge_pane():
    info = pn.pane.Markdown(
        "Suggest strings based on string tension data. "
        "Most of the data is "
        "[from D'Addario](https://www.daddario.com/globalassets/pdfs/accessories/tension_chart_13934.pdf)."
    )

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
        df = df.rename(columns=df.attrs["fancy_col"])

        # TODO: highlight best option
        return pn.Column(
            df.hvplot.table(sortable=True, selectable=True, width=WIDTH),
        )

    return pn.Column(
        info,
        tension_input,
        length_input,
        pitch_input,
        n_input,
        types_input,
        table,
        width=WIDTH,
    )


def exact_gauge_pane():
    info = pn.pane.Markdown("Compute exact gauge based on material density.")

    # TODO: could duplicate or link to these 3 widgets in suggest-gauge?
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

    type_input = pn.widgets.RadioBoxGroup(name="String type", options=DENSITY_LB_IN, inline=True)

    @pn.depends(tension_input, length_input, pitch_input, type_input)
    def res(T, L, pitch, dens):
        g = gauge(dens, T=T, L=L, pitch=pitch)
        return pn.pane.Markdown(f'**Gauge:** {g:.4g}" = {g*25.4:.4g} mm')

    return pn.Column(
        info,
        tension_input,
        length_input,
        pitch_input,
        type_input,
        res,
        width=WIDTH,
    )


def frets_pane():
    info = pn.pane.Markdown(
        "Compute fret positions. " "This uses the equal-temperament 12th-root-of-2 method."
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

    n_input = pn.widgets.IntSlider(
        name="Number of frets",
        start=1,
        end=30,
        value=17,
        width=int(WIDTH / 3),
    )

    @pn.depends(length_input, n_input)
    def res(L, N):
        df = distances(N=N, L=L)
        df = df.reset_index(drop=False).rename(columns=df.attrs["fancy_col"])
        return pn.Column(
            df.hvplot.table(sortable=False, selectable=True, width=WIDTH),
        )

    return pn.Column(
        info,
        length_input,
        n_input,
        res,
    )


app = pn.Tabs(
    ("Suggest strings", suggest_gauge_pane()),
    ("Exact gauge", exact_gauge_pane()),
    ("Frets", frets_pane()),
)
app.servable()
