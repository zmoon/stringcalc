"""
Plot the tension data for some of the string types I usually buy
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyabc2 import Pitch

plt.close("all")


# %% Load

df = pd.read_csv("daddario-tension.csv", header=0).drop(columns=["tens", "notes"]).convert_dtypes()


# %% Plot

# Compute range of freqs
# TODO: make pitch range helper in pyabc2
p0 = Pitch.from_name("C2")
p1 = Pitch.from_name("B4")
pitches = [Pitch(v) for v in range(p0.value, p1.value + 1)]
F = np.array([p.etf for p in pitches])

# Pitch labels, naturals only
xticks = []
xticklabels = []
for i, p in enumerate(pitches):
    pc = p.to_pitch_class()
    if pc.isnat:
        xticks.append(i)
        xticklabels.append(p.name)

L = 25.5

fig, ax = plt.subplots(figsize=(10, 5.5))

# PL - Plain Steel
df_ = df[df.id_pref == "PL"]
colors = plt.cm.gray_r(np.linspace(0.15, 0.8, len(df_)))
for (_, row), c in zip(df_.iterrows(), colors):
    UW = row.uw
    T = UW * (2 * L * F) ** 2 / 386.0
    ax.plot(T, label=row.id, c=c)

# PB - Phosphor Bronze
df_ = df[df.id_pref == "PB"]
colors = plt.cm.copper_r(np.linspace(0.05, 0.7, len(df_)))
for (_, row), c in zip(df_.iterrows(), colors):
    UW = row.uw
    T = UW * (2 * L * F) ** 2 / 386.0
    ax.plot(T, label=row.id, c=c)

ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels)
ax.autoscale(axis="x", tight=True)
ax.grid()
ax.set_ylabel("Tension (lb)")
ax.set_ylim((0, 30))
# ax.set_ylim((0.1, 30)); ax.set_yscale("log")

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

fig.savefig("daddario-guitar-tension.png", transparent=True, dpi=200, bbox_inches="tight")
