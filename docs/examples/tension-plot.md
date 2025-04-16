---
file_format: mystnb
kernelspec:
  name: python3
---

# Tension plot

In this example, we plot the tension of
D'Addario plain steel and phosphor bronze guitar strings
as a function of pitch
for a scale length of 25.4" (e.g. Martin Dreadnought, OM).

```{code-cell} ipython3
:tags: [hide-output]

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyabc2 import Pitch

from stringcalc.tension import load_daddario_data
```

## Load data

```{code-cell} ipython3
:tags: [hide-output]

df = (
    load_daddario_data()
    .query("group_id in ['PL', 'PB']")
    [["id", "uw", "group_id"]]
)
df
```

## Plot

```{code-cell} ipython3
# Compute range of freqs
pitches = [
    Pitch(v)
    for v in range(
        Pitch.from_name("C2").value,
        Pitch.from_name("B4").value + 1
    )
]
F = np.array([p.etf for p in pitches])

# Pitch labels, naturals only
xticks = []
xticklabels = []
for i, p in enumerate(pitches):
    pc = p.to_pitch_class()
    if pc.isnat:
        xticks.append(i)
        xticklabels.append(p.unicode())

L = 25.4

fig, ax = plt.subplots(figsize=(10, 5.5))

# PL - Plain Steel
df_ = df[df.group_id == "PL"]
colors = plt.cm.gray_r(np.linspace(0.15, 0.8, len(df_)))
for row, c in zip(df_.itertuples(), colors):
    UW = row.uw
    T = UW * (2 * L * F) ** 2 / 386.09
    ax.plot(T, label=row.id, c=c)

# PB - Phosphor Bronze
df_ = df[df.group_id == "PB"]
colors = plt.cm.copper_r(np.linspace(0.05, 0.7, len(df_)))
for row, c in zip(df_.itertuples(), colors):
    UW = row.uw
    T = UW * (2 * L * F) ** 2 / 386.09
    ax.plot(T, label=row.id, c=c)

ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels)
ax.autoscale(axis="x", tight=True)
ax.grid()
ax.set_ylabel("Tension [lbf]")
ax.set_ylim((0, 30))
# ax.set_ylim((0.3, 40)); ax.set_yscale("log")

ax.legend(ncol=2, fontsize=9, bbox_to_anchor=(1.01, 0.5), loc="center left")

ax.text(
    0.96,
    0.06,
    f"$L = {L}$ in",
    va="bottom",
    ha="right",
    transform=ax.transAxes,
    bbox=dict(boxstyle="round", facecolor="0.85", alpha=0.8),
)

fig.tight_layout()

# fig.savefig("daddario-guitar-tension.png", transparent=True, dpi=200, bbox_inches="tight")
```

👆 Note the considerable region of overlap
between the heavier plain steel and lighter phosphor bronze strings.
