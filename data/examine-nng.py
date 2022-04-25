"""
Examine the NNG (New Nylgut) equivalence data from Aquila

Table retrieved from https://aquilacorde.com/en/string-gauge-converter/ on 25-Apr-2022
with additional data from https://aquilacorde.com/wp-content/uploads/2019/09/conversion.pdf added
"""
# from pathlib import Path
import sys; sys.path.append("../")

# import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tension import load_data

plt.close("all")


# %% Load

df = pd.read_csv("aquila-nng-equiv.csv").convert_dtypes()

df = df.rename(columns={
    # From the web table:
    'AQUILA NEW NYLGUT CODE': "id",
    'NEW NYLGUT EQUIVALENT GUT/ACTUAL GAUGE': "gauge",
    'NYLON GAUGES': "gauge_nylon",
    'CARBON GAUGES': "gauge_carbon",
    # From the PDF:
    "NYLON 2 (mm)": "gauge_nylon2",
    "PVF Carbon (mm)": "gauge_carbon2",
    "Aquila D (gut-equiv mm * 100)": "gauge_d",
    }
)

# Convert to inches
for name in ["gauge", "gauge_nylon", "gauge_carbon"]:
    df[name] = df[name].str.slice(stop=-3).astype("Float64") / 25.4

for name in ["gauge_nylon2", "gauge_carbon2"]:
    df[name] = df[name].astype("Float64") / 25.4

for name in ["gauge_d"]:
    df[name] = df[name].astype("Float64") / 100 / 25.4

df = df.dropna(subset=["id"])


# %% Plot

# Aquila NNG is ~ 1300 kg/m3 / 1.3 g/cm3
# nylon is generally lower density, ~ 1100 kg/m3
#
# What do the data suggest that we are comparing to?

(1300 / df[["gauge_nylon", "gauge_nylon2"]].div(df.gauge, axis="rows")).plot(
    ylabel="estimated nylon density",
    marker=".",
)

# Estimate density of D'Addario NYL strings
df2 = load_data().query("group_id == 'NYL'").copy()
df2["rho"] = (df2.uw / (np.pi * df2.gauge**2 / 4) * 1/(2.54**3) * 1e6 / 2.205)
# The data suggest rho ~ 995.8 kg/m3, unless there is something wrong with my calculation...
