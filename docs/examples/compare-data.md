---
file_format: mystnb
kernelspec:
  name: python3
---

# Compare data

In this example, we compare data from different manufacturers
for two common string types: plain steel and phosphor bronze ball-end strings.

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

```{code-cell} ipython3
group_ids = ["DA:PL", "GHS:PL", "SJ:PL"]
(
    data.query("group_id in @group_ids")
    .pivot_table(
        index="gauge",
        columns="group_id",
        values=["uw"],
    )
    .mul(1000)
)
```

```{note}
We multiplied `uw`, the unit weight (mass per unit length) [lbm/in]
by 1000 to facilitate easier comparison.
```

## Phosphor bronze

```{code-cell} ipython3
group_ids = ["DA:PB", "GHS:B", "SJ:PB"]
(
    data.query("group_id in @group_ids")
    .pivot_table(
        index="gauge",
        columns="group_id",
        values=["uw"],
    )
    .mul(1000)
)
```
