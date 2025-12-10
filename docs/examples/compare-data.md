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
group_ids = ["DA:PL", "STP:PL", "GHS:PL", "SJ:PL"]
(
    data.query("group_id in @group_ids")
    .pivot_table(
        index="gauge",
        columns="group_id",
        values=["uw"],
        observed=True,
    )
    .mul(1000)
    .style
    .set_caption("Plain steel")
    .background_gradient(axis=1, cmap="RdBu_r")
)
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
group_ids = ["DA:PB", "STP:PB", "GHS:B", "SJ:PB"]
(
    data.query("group_id in @group_ids")
    .pivot_table(
        index="gauge",
        columns="group_id",
        values=["uw"],
        observed=True,
    )
    .mul(1000)
    .style
    .set_caption("Phosphor bronze")
    .background_gradient(axis=1, cmap="RdBu_r")
)
```

## Nickel-wound

Nickel-wound ball-end strings.

- `DA:NW` and `STP:NW`: D'Addario nickel-plated steel
- `GHS:N`: GHS Nickel Rockers (pure nickel, semi-flattened)
- `GHS:DY`: GHS Boomers (nickel-plated steel)
- `SJ:N`: Stringjoy nickel ("Signatures"; nickel-plated steel?)
- `SJ:PN`: Stringjoy pure nickel ("Broadways")

```{code-cell} ipython3
group_ids = ["DA:NW", "STP:NW", "GHS:N", "GHS:DY", "SJ:N", "SJ:PN"]
(
    data.query("group_id in @group_ids")
    .pivot_table(
        index="gauge",
        columns="group_id",
        values=["uw"],
        observed=True,
    )
    .mul(1000)
    .style
    .set_caption("Nickel-wound")
    .background_gradient(axis=1, cmap="RdBu_r")
)
```
