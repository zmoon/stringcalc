---
file_format: mystnb
kernelspec:
  name: python3
---

# Compare data

In this example, we compare data from different manufacturers
for common ball-end string types:

- plain steel
- phosphor bronze
- nickel-wound

```{code-cell} ipython3
import pandas as pd

from stringcalc.tension import load_data
```

First we load all of the available data with the {func}`~stringcalc.tension.load_data` function.

```{code-cell} ipython3
data = load_data()
data
```

## Plain steel

Plain steel ball-end strings.

```{code-cell} ipython3
def make_table(title, group_ids):
    table = (
        data
        .query("group_id in @group_ids")
        .pivot_table(
            index="gauge",
            columns="group_id",
            values=["uw"],
            observed=True,
        )
        .mul(1000)
    )

    # single unique value -> neutral midpoint (instead of vmin),
    # while keeping NaNs as NaN
    vmin = table.min(axis=1)
    gmap = (
        table
        .sub(vmin, axis=0)
        .div(table.max(axis=1) - vmin, axis=0)
        .fillna(0.5)
        .mask(table.isna())
    )

    return (
        table
        .style
        .set_caption(title)
        .background_gradient(
            cmap="RdBu_r",
            gmap=gmap,
            vmin=0,
            vmax=1,
            axis=None,
        )
    )


make_table("Plain steel", ["DA:PL", "STP:PL", "GHS:PL", "SJ:PL"])
```

```{note}
We multiplied `uw`, the unit weight (mass per unit length) [lbm/in]
by 1000 to facilitate easier comparison.
```

```{note}
Within a given row, a red cell background indicates higher values and blue lower.
For example, Stringjoy plain steel strings are generally heavier than the others (red),
and D'Addario original and STP are always quite close (same color).
The lack of a number in a cell indicates that we don't have data for that gauge.
```

## Phosphor bronze

Phosphor bronze ball-end strings.

```{code-cell} ipython3
make_table("Phosphor bronze", ["DA:PB", "STP:PB", "GHS:B", "SJ:PB"])
```

## Nickel-wound

Nickel-wound ball-end strings.

- `DA:NW` and `STP:NW`: D'Addario nickel-plated steel
- `GHS:N`: GHS Nickel Rockers (pure nickel, semi-flattened)
- `GHS:DY`: GHS Boomers (nickel-plated steel)
- `SJ:N`: Stringjoy nickel ("Signatures"; nickel-plated steel?)
- `SJ:PN`: Stringjoy pure nickel ("Broadways")

```{code-cell} ipython3
make_table("Nickel-wound", ["DA:NW", "STP:NW", "GHS:N", "GHS:DY", "SJ:N", "SJ:PN"])
```
