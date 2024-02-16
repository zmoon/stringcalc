"""
Get GHS data
from the calculator https://www.ghsstrings.com/pages/tension-calc
"""
import re
import sys
from pathlib import Path

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

# group_stuff = {
#     # original group name: (new group name, group ID pref)
#     "bassNickel": ("Bass Nickel", "BN"),
#     "brass": ("80/20 Bronze", "B"),
#     "bronze": ("Phosophor Bronze", "PB"),
#     "nickel": ("Nickel", "N"),
#     "plain": ("Plain Steel", "PL"),
#     "pure": ("Pure Nickel", "PN"),
# }
# assert set(group_stuff) == set(df.key.unique())

# # D'Addario-like IDs
# df["group"] = df.key.map({k: v[0] for k, v in group_stuff.items()})
# df["group_id"] = df.key.map({k: v[1] for k, v in group_stuff.items()})
# df = df.drop(columns=["key", "name"])
# df0.name.str.startswith(".").all()
# df.insert(0, "id", df.group_id + df0.name.str.rstrip("wp").str.lstrip("."))

# %% Save

# fn = "ghs.csv"
# fp = HERE / "../stringcalc/data" / fn
# assert fp.parent.is_dir()

# df.to_csv(fp, index=False, float_format="%.5g")

# # Reload
# dfr = pd.read_csv(fp, header=0)
