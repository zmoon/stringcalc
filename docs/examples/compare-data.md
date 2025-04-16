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
group_ids = ["DA:PL", "GHS:PL", "SJ:PL"]
(
    data.query("group_id in @group_ids")
    .pivot_table(
        index="gauge",
        columns="group_id",
        values=["uw"],
        observed=True,
    )
    .mul(1000)
)
```

```{note}
We multiplied `uw`, the unit weight (mass per unit length) [lbm/in]
by 1000 to facilitate easier comparison.
```

## Phosphor bronze

Phosphor bronze ball-end strings.

```{code-cell} ipython3
group_ids = ["DA:PB", "GHS:B", "SJ:PB"]
(
    data.query("group_id in @group_ids")
    .pivot_table(
        index="gauge",
        columns="group_id",
        values=["uw"],
        observed=True,
    )
    .mul(1000)
)
```

## Nickel-wound

Nickel-wound ball-end strings.

- `DA:NW`: D'Addario nickel-plated steel
- `GHS:N`: GHS Nickel Rockers (pure nickel, semi-flattened)
- `GHS:DY`: GHS Boomers (nickel-plated steel)
- `SJ:N`: Stringjoy nickel ("Signatures"; nickel-plated steel?)
- `SJ:PN`: Stringjoy pure nickel ("Broadways")

```{code-cell} ipython3
group_ids = ["DA:NW", "GHS:N", "GHS:DY", "SJ:N", "SJ:PN"]
(
    data.query("group_id in @group_ids")
    .pivot_table(
        index="gauge",
        columns="group_id",
        values=["uw"],
        observed=True,
    )
    .mul(1000)
)
```
