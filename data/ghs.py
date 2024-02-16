"""
Get GHS data
from the calculator https://www.ghsstrings.com/pages/tension-calc
"""
import re
import string
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

if sys.version_info < (3, 10):
    print("Python version >= 3.10 required.")
    raise SystemExit(0)

HERE = Path(__file__).parent

# %% Load from the embedded JavaScript

url = "https://www.ghsstrings.com/pages/tension-calc"

r = requests.get(url)
r.raise_for_status()
s = r.text

# Get the data snippet
# Top-level keys are 'Acoustic', 'Electric', 'Bass'
start = "const weights = "
a = s.find(start)
assert a != -1
b = None
n = 0
for i, c in enumerate(s[a + len(start) :]):
    if c == "{":
        n += 1
    elif c == "}":
        n -= 1
    if n == 0:
        b = a + len(start) + i
        break

# %% Parse

chunk = s[a + len(start) : b + 1]
print(chunk)
assert chunk[0] == "{" and chunk[-1] == "}"

# Remove comments
chunk = re.sub(r" ?// ?[^\n]*", "", chunk)

# Hack: add key names to globals
while True:
    try:
        data_raw = eval(chunk)
    except NameError as e:
        print(e.name)  # `.name` only in 3.10+
        globals().update({e.name: e.name})
    except Exception:
        raise
    else:
        break

# %% Construct DataFrame

dfs = []

for meta_group, group_data in data_raw.items():
    for group, id_to_uw in group_data.items():
        df_ = pd.DataFrame(id_to_uw.items(), columns=["id", "uw"])
        df_["group"] = group
        df_["meta_group"] = meta_group

        # Manipulate IDs for plain to normalize
        # - replace dot
        # - zero-pad those with gauge less than 10 (D'Addario would have two zeros)
        # - add 'PL' prefix
        # Technically, the SKUs are like '008', '008 1/2', etc.
        # https://www.ghsstrings.com/products/21932-plain-steel-strings
        if group == "Plain":
            df_["id"] = df_["id"].where(df_["id"].astype(float).gt(9.999), "0" + df_["id"])
            df_["id"] = df_["id"].str.replace(".", "")
            df_["id"] = "PL0" + df_["id"]

        dfs.append(df_)

df = pd.concat(dfs, ignore_index=True)
df0 = df.copy()

# There are some bass strings with no group ID pref
# some of these seem like just duplicates for other scale lengths
# but not all
for group, pref in {
    "Balanced Nickel": "NB",
    "Boomers": "DYB",
    "Brite Flats": "BF",
    "Phosphor Bronze": "PHB",
    "Precision Flats": "FB",
    "Pressurewounds": "PWB",
    "Progressives": "PRB",
    "Super Steels": "STB",
    "Tapewound": "TW",  # made this ID up
}.items():
    loc = (df["group"] == group) & (df["meta_group"] == "Bass")
    assert loc.any()
    sel = df[loc]
    df.loc[loc, "id"] = sel["id"].where(
        ~sel["id"].str.startswith(tuple(string.digits)), pref + sel["id"]
    )

assert df[df["id"].str.startswith(tuple(string.digits))].empty, "all have ID pref"

# A few have ID suffs
df_id_suffs = df[~df.id.str.endswith(tuple("0123456789"))]

# Parse IDs to get group IDs and compute gauge
id_parts = df["id"].str.extract(
    r"(?P<id_pref>[A-Z]+)(?P<gauge_ish>[0-9]+)(?P<id_suff>[A-Z]+)?", expand=True
)
assert id_parts["id_pref"].isnull().sum() == 0
group_id = id_parts["id_pref"] + id_parts["id_suff"].fillna("")

# PL is already properly zero-padded for just `.` to be prepended
# But for the others, need to check number of digits, and assume no half-gauges
df["gauge"] = 0.0
loc = df["group"] == "Plain"
df.loc[loc, "gauge"] = ("." + id_parts.loc[loc, "gauge_ish"]).astype(float)

loc = (df["group"] != "Plain") & (id_parts["gauge_ish"].str.len().isin((2, 3)))
df.loc[loc, "gauge"] = ("." + id_parts.loc[loc, "gauge_ish"].str.zfill(3)).astype(float)

# For the 4-digit ones, gauge is not related to this part of the ID
loc = (df["group"] != "Plain") & (id_parts["gauge_ish"].str.len() == 4)
df.loc[loc, "gauge"] = np.nan

assert df["gauge"].eq(0).sum() == 0, "all gauges set"
assert 0.009 <= df["gauge"].min() < df["gauge"].max() < 0.2

df_gauge_null = df[df["gauge"].isnull()]

# Some group names are shared between meta groups, bass and electric, e.g.
assert df.groupby("group").meta_group.nunique().max() > 1

df = df.assign(
    group=df["meta_group"] + " - " + df["group"],
    group_id=group_id,
).drop(columns=["meta_group"])

# Note that group ID and group names are stil not 1:1
# Mostly bass-related
# But also note PL is duplicated for electric
# Note acoustic PB is 'B', not 'PB', as 'PB' is used for higher strings in some bass sets
group_multi_ids = df.groupby("group")["group_id"].unique()
group_multi_ids = group_multi_ids[group_multi_ids.apply(len) > 1]
group_id_multi_groups = df.groupby("group_id")["group"].unique()
group_id_multi_groups = group_id_multi_groups[group_id_multi_groups.apply(len) > 1]

col_order = [
    "id",
    "uw",
    "gauge",
    "group",
    "group_id",
]
assert set(df.columns) == set(col_order)

df = df[col_order]

# %% Save

fn = "ghs.csv"
fp = HERE / "../stringcalc/data" / fn
assert fp.parent.is_dir()

df.to_csv(fp, index=False, float_format="%.5g")

# Reload
dfr = pd.read_csv(fp, header=0)
