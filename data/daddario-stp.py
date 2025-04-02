"""
D'Addario String Tension Pro

It's back---got the beta email notice on 2024-06-12.
"""
import re
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd
import requests

HERE = Path(__file__).parent

url_app = "https://www.daddario.com/string-tension-pro"
url_rec_js = (
    "https://embed.cartfulsolutions.com/daddario-string-tension-finder/recommendation.min.js"
)
url_data = (
    "https://embed.cartfulsolutions.com/daddario-string-tension-finder/data/strings_dataset.json"
)

r = requests.get(url_app)
r.raise_for_status()
p = urlsplit(url_rec_js)
assert p.netloc in r.text
assert p.path in r.text

r = requests.get(url_rec_js)
data_urls = re.findall(
    r"\"(https://[a-z\./]*/daddario-string-tension-finder/data/[a-z_\./]*)\"", r.text
)
data_urls.sort()
print("data URLs:")
print("\n".join(f"- {url}" for url in data_urls))
assert len(data_urls) > 0
assert url_data in data_urls

r = requests.get(url_data)
r.raise_for_status()
raw_data = r.json()

# List of entries, for example:
#
#  {'SetItemNumber': 'EJ13',
#   'ComponentItemNumber': 'PL011',
#   'SubComponent': 'U1AGFPL011-NP',
#   'SequenceNumber': 1,
#   'ItemClassPosition1': 'A',
#   'ItemClassPosition2': 'B',
#   'ItemClassPosition3': 'J',
#   'ItemClassPosition4': 'A',
#   'SizeInInches(gauge)': 11,
#   'SizeInMillimeters(gauge)': 279.4,
#   'StringConstruction': 'Plain Steel',
#   'MassPerUnitLength': 2.68184e-05,
#   'Instrument': 'Acoustic Guitar',
#   'Material': 'Tin Coated Steel',
#   'EndType': 'Small Ball End'},
#
# Individual string data is duplicated, for the sake of sets.

df = (
    pd.DataFrame(raw_data)
    .drop(
        columns=[
            "SequenceNumber",
            "ItemClassPosition1",
            "ItemClassPosition2",
            "ItemClassPosition3",
            "ItemClassPosition4",
        ]
    )
    .rename(
        columns={
            "SetItemNumber": "set",
            "ComponentItemNumber": "id",
            "SubComponent": "sub_comp",  # like a long ID?
            "SizeInInches(gauge)": "gauge",
            "SizeInMillimeters(gauge)": "gauge_mm",
            "StringConstruction": "construction",
            "MassPerUnitLength": "uw",
            "Instrument": "instrument",
            "Material": "material",
            "EndType": "end_type",
        }
    )
)

assert all(c == c.lower() for c in df.columns)

df0 = df.copy()

# Fix NYS008 for U2AGFPL008-NP (factor of 10 too high)
sub_comp = "U2AGFPL008-NP"
row = df[df.sub_comp == sub_comp]
assert len(row) == 1
assert (row.gauge == 80).all()
assert (row.gauge_mm == 2032.0).all()
df.loc[df.sub_comp == sub_comp, "gauge"] /= 10
df.loc[df.sub_comp == sub_comp, "gauge_mm"] /= 10

# Use sub-component for IDs for MISC??
df["id"] = df["sub_comp"].where(df["id"] == "MISC", df["id"])

# Move to one row per ID
assert not df["id"].is_unique
rows = []
for id_, g in df.groupby("id"):
    if g.duplicated().any():
        # print(f"ID {id_} has duplicate rows")
        g = g.drop_duplicates(keep="first")

    nu = g.nunique()

    if nu["uw"] != 1:
        print(f"ID {id_} has {nu['uw']} unique values of unit weight")
        continue

    if nu["material"] != 1:
        print(f"ID {id_} has {nu['material']} unique values of string material")
        continue

    if nu["gauge"] != 1:
        print(f"ID {id_} has {nu['gauge']} unique values of string gauge")
        continue

    uniques = [
        "id",
        "gauge",
        "gauge_mm",
        "construction",
        "uw",
        "material",
        "end_type",
    ]
    assert all(nu[col] == 1 for col in uniques)

    non_uniques = [
        "instrument",
        "set",
        "sub_comp",
    ]
    assert nu["set"] > 1 or len(g) == 1

    row = g[uniques].iloc[0]
    for col in non_uniques:
        row[col] = sorted(g[col].unique())

    rows.append(row)

df = pd.DataFrame(rows).sort_values(by="id").reset_index(drop=True)

# Fix gauge
assert df.gauge.min() > 1
df["gauge"] = df["gauge"] / 1000
df["gauge_mm"] = df["gauge_mm"] / 1000

# Group IDs like original
s_re = r"(?P<id_pref>[A-Z]+)(?P<id_gauge>[0-9]+)(?P<id_suff>[A-Z]*)"
is_simple_id = df["id"].str.fullmatch(s_re)
n = is_simple_id.value_counts()[False]
if n > 0:
    print(f"{n}/{len(df)} IDs do not match the group ID pattern")
df_ = df.loc[is_simple_id, "id"].str.extract(s_re)
df_["group_id"] = df_["id_pref"] + df_["id_suff"]

df = df.join(df_.drop(columns=["id_pref", "id_suff"]), how="left")

# Material is mostly unique for a group ID, though different group IDs may have the same material
nmat = df.groupby("group_id").material.nunique()
nmat_is_not_unique = nmat.gt(1)
set(nmat[nmat_is_not_unique].index) == {"J", "JC", "NYL"}
assert set(df.query("group_id == 'NYL'").material.unique()) == {"Clear Nylon"}

df.loc[df["group_id"] == "J", "material"] = "Various"
df.loc[df["group_id"] == "JC", "material"] = "Various"

# Use material for group name
group = df.groupby("group_id").material.first().rename("group")
df = df.join(group, on="group_id", how="left")

# Write
fn = "daddario-stp.csv"
fp = HERE / "../stringcalc/data" / fn
assert fp.parent.is_dir()
(
    df[["id", "uw", "gauge", "group_id", "group"]]
    .dropna(subset="group_id")
    .sort_values(by=["group_id", "gauge"])
    .to_csv(fp, index=False, float_format="%.5g")
)

# Reload
dfr = pd.read_csv(fp, header=0)
