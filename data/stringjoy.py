"""
Get Stringjoy data
used in https://tension.stringjoy.com/
"""

import sys
from pathlib import Path

import pandas as pd
import requests

if sys.version_info < (3, 10):
    print("Python version >= 3.10 required.")
    raise SystemExit(0)

HERE = Path(__file__).parent

# %% Load source code that it is in

url = "https://tension.stringjoy.com/static/js/main.4e22ff30.chunk.js"

r = requests.get(url)
r.raise_for_status()
s = r.text

# Get the data snippet
start = "y="
a = s.find(start)
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
assert chunk[0] == "{" and chunk[-1] == "}"
print(chunk)

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

for k, data in data_raw.items():
    df_ = pd.DataFrame(data).assign(key=k)
    if df_.dtypes["mass"] != "float64":
        print(f"Converting mass from str to float for {k}")
        df_["mass"] = df_["mass"].astype("float64")
    dfs.append(df_)

df = pd.concat(dfs)
df0 = df.copy()

df["gauge"] = df.name.str.rstrip("wp").astype(float)

# Looks like "mass" is just UW (lbm/in) already
df = df.rename(columns={"mass": "uw"})

group_stuff = {
    # original group name: (new group name, group ID pref)
    "bassNickel": ("Bass Nickel", "BN"),
    "brass": ("80/20 Bronze", "B"),
    "bronze": ("Phosophor Bronze", "PB"),
    "nickel": ("Nickel", "N"),
    "plain": ("Plain Steel", "PL"),
    "pure": ("Pure Nickel", "PN"),
}
assert set(group_stuff) == set(df.key.unique())

# D'Addario-like IDs
df["group"] = df.key.map({k: v[0] for k, v in group_stuff.items()})
df["group_id"] = df.key.map({k: v[1] for k, v in group_stuff.items()})
df = df.drop(columns=["key", "name"])
df0.name.str.startswith(".").all()
df.insert(0, "id", df.group_id + df0.name.str.rstrip("wp").str.lstrip("."))

# %% Save

fn = "stringjoy.csv"
fp = HERE / "../stringcalc/data" / fn
assert fp.parent.is_dir()

df.to_csv(fp, index=False, float_format="%.5g")

# Reload
dfr = pd.read_csv(fp, header=0)
