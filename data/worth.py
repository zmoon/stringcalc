"""
Examine and save the Worth data.
This is a subset of the data from Brauchli.
"""
import sys
from pathlib import Path

sys.path.append("../")

# import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# from stringcalc.tension import load_data

plt.close("all")

HERE = Path(__file__).parent


# %%

df0 = pd.read_csv(HERE / "worth-uke.csv").convert_dtypes()

# Don't have real IDs, let's make some up
ids = ["Aa", "Ab", "E", "Ca", "Cb", "Ga", "Gb", "Gc", "Glo", "GloHD"]
assert len(df0) == len(ids)
assert all(id_[0] == s[0] for s, id_ in zip(df0.String, ids))

# Gauge (in)
g = df0["Diameter (cm)"] / 2.54

# Compute UW (lbm/in)
w = df0["Sample Weight (g)"] / 1000 * 2.205
l = df0["Sample Length (cm)"] / 2.54  # noqa: E741
uw = w / l

# Compute density (kg/m3) ~ 1800
m = df0["Sample Weight (g)"] / 1000
l = df0["Sample Length (cm)"] / 100  # noqa: E741
d = df0["Diameter (cm)"] / 100
rho = m / (l * (np.pi * d**2 / 4))

df = pd.DataFrame(
    {
        "id": ids,
        "gauge": g,
        "uw": uw,
        "rho": rho,
    },
)


# %% Save

fn = "worth.csv"
fp = HERE / "../stringcalc/data" / fn
assert fp.parent.is_dir()

df.to_csv(fp, index=False, float_format="%.4g")

# Reload
dfr = pd.read_csv(fp, header=0)
