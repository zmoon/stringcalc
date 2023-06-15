"""
Examine the NNG (New Nylgut) equivalence data from Aquila

Table retrieved from https://aquilacorde.com/en/string-gauge-converter/ on 25-Apr-2022
with additional data from https://aquilacorde.com/wp-content/uploads/2019/09/conversion.pdf added
"""
import sys
from pathlib import Path

sys.path.append("../")

# import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from stringcalc.tension import load_data

plt.close("all")

HERE = Path(__file__).parent


# %% Load

df = pd.read_csv(HERE / "aquila-nng-equiv.csv").convert_dtypes()

df = df.rename(
    columns={
        # From the web table:
        "AQUILA NEW NYLGUT CODE": "id",
        "NEW NYLGUT EQUIVALENT GUT/ACTUAL GAUGE": "gauge",
        "NYLON GAUGES": "gauge_nylon_web",
        "CARBON GAUGES": "gauge_carbon_web",
        # From the PDF:
        "NYLON 2 (mm)": "gauge_nylon_pdf",
        "PVF Carbon (mm)": "gauge_carbon_pdf",
        "Aquila D (gut-equiv mm * 100)": "gauge_d",
    }
)

# Convert gauge to inches
for name in ["gauge", "gauge_nylon_web", "gauge_carbon_web"]:
    df[name] = df[name].str.slice(stop=-3).astype("Float64") / 25.4

for name in ["gauge_nylon_pdf", "gauge_carbon_pdf"]:
    df[name] = df[name].astype("Float64") / 25.4

for name in ["gauge_d"]:
    df[name] = df[name].astype("Float64") / 100 / 25.4

df = df.dropna(subset=["id"])


# %% Calculate and plot

# Aquila NNG is ~ 1300 kg/m3 / 1.3 g/cm3
# nylon is generally lower density, ~ 1100 kg/m3
#
# What do the data suggest that we are comparing to?

(1300 / df[["gauge_nylon_web", "gauge_nylon_pdf"]].pow(2).div(df.gauge.pow(2), axis="rows")).plot(
    ylabel="estimated nylon density",
    marker=".",
)

# Estimate density of D'Addario NYL strings
df2 = load_data().query("group_id == 'NYL'").copy()
df2["rho"] = df2.uw / (np.pi * df2.gauge**2 / 4) * 1 / (2.54**3) * 1e6 / 2.205
# The data suggest rho ~ 995.8 kg/m3, unless there is something wrong with my calculation...

assert df2.rho.std() / df2.rho.mean() < 0.001
rho_bar = df2.rho.mean()

df2.plot(x="gauge", y="rho", ylabel="Computed D'Addario NYL density")

# rho ~ 1/gauge^2 => rho gauge^2 = c
df["gauge_da_nylon"] = np.sqrt(1300 * df.gauge**2 / rho_bar)

# Compute UW (depends on density assumption)
# -> lbm/in3, apply cross-sectional area
df["uw"] = 1300 * 2.205 / 1e6 * (2.54**3) * (np.pi * df.gauge**2 / 4)


# %% Save

fn = "aquila-nng.csv"
fp = HERE / "../stringcalc/data" / fn
assert fp.parent.is_dir()

# Not UW, so that NNG density can be an input
df.drop(columns="uw").to_csv(fp, index=False, float_format="%.3g")

# Reload
dfr = pd.read_csv(fp, header=0)
