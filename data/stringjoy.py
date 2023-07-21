"""
Get Stringjoy data
used in https://tension.stringjoy.com/
"""
# import json
# import re

import pandas as pd
import requests

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

# # Make keys strings?? (so can load as JSON)
# chunk_json = re.sub(r"[a-z]{2,}", lambda m: f"\"{m.group()}\"", chunk)
# data_raw = json.loads(chunk)

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

# gauge: df.name.str.rstrip("wp").astype(float)
