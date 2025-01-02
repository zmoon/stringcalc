"""
Parsing the D'Addario extracted string tension data
converting to a DataFrame
"""

import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent

# e.g. `PL009 .00001794 18.6 14.7 13.1 10.4 8.3 7.4 5.8 4.6`
re_entry = re.compile(r"(?P<id>[A-Z0-9]+) (?P<uw>\.[0-9]+) (?P<tens>(.+){8})")


# The larger categories, in the red boxes
cats = [
    "Acoustic or Electric Guitar",
    "Pedal Steel Guitar",
    "Acoustic Guitar",
    "Classical Guitar",
    "FOLK GUITAR",
    "ELECTRIC BASS GUITAR",
    "Acoustic Bass Guitar",
    "Mandolin Family Strings",
    "Mandolin Family Strings (cont.)",
    "Banjo & Loop End String Tensions",
]

lengths = """
Acoustic/Electric/Classical Guitar = 25 1/2"
Electric Bass Guitar (Superlong Scale) = 36"
Electric Bass Guitar (Long Scale) = 34"
Electric Bass Guitar (Medium Scale) = 32"
Electric Bass Guitar (Short Scale) = 30"
Mandolin = 13 7/8"
Mandola = 15 7/8"
Mandocello = 25"
Mandobass = 42"
Banjo = 26 1/4" (19 5/8" for 5th string)
""".strip()


def convert_note(s: str) -> str:
    """Convert note from the D'Addario format to SPN.

    Pitch Notation
    --------------
    c' (Middle c) = 261.6 Hz
    Note Above = d'
    Note Below = b
    Octave Above = c"
    Octave Below = c
    2 Octaves Below = C
    3 Octaves Below = C'
    """
    dn_vals = {"": 0, "'": 1, '"': 2, "''": 2}

    x = 2 if "#" in s else 1
    c, apos = s[:x], s[x:]
    assert c[0].upper() in "ABCDEFG" and apos in dn_vals, s

    dn = dn_vals[apos]
    if c.islower():
        n = 3 + dn
    else:
        n = 2 - dn

    return f"{c.upper()}{n}"


for s, expected in [
    ("c'", "C4"),  # middle C
    ("d'", "D4"),
    ('c"', "C5"),
    ("C", "C2"),
    ("C'", "C1"),
]:
    got = convert_note(s)
    assert got == expected, f"{got=}, {expected=}"


rows = []
cat = None
subcat = None
notes = None
with open(HERE / "daddario-tension.txt", encoding="utf-8") as f:
    for line in f:
        line = line.strip()

        if " & -F6" in line:
            # There are just two of these, in the bass section
            # Not sure what means so just removing
            line = line.replace(" & -F6", "")

        if line.endswith("Scale"):
            continue  # used to group some of the bass strings

        # Category?
        if line in cats:
            cat = line

        # Table heading
        elif line.startswith("Item# Unit Weight"):
            notes_ = line[17:].split()
            notes = [convert_note(x) for x in notes_]

        # Table entry
        elif (m := re_entry.fullmatch(line)) is not None:
            d = m.groupdict()

            # Create row corresponding to this entry
            row = {
                "id": d["id"],
                "uw": float(d["uw"]),
                "category": cat,
                "group": subcat,
                "notes": notes,
                "tens": [None if x == "-" else float(x) for x in d["tens"].split()],
            }

            rows.append(row)

        else:
            subcat = line
            print(subcat)

df = pd.DataFrame(rows).convert_dtypes()

assert df.id.unique().size == len(df)

# Split ID parts
df = df.join(
    df.id.str.extract("(?P<id_pref>[A-Z]+)(?P<id_gauge>[0-9]+)(?P<id_suff>[A-Z]*)"), how="left"
)
df["gauge"] = "." + df["id_gauge"]  # I think this should always be the case but maybe not
df["group_id"] = df["id_pref"] + df["id_suff"]
df = df.drop(columns="id_gauge")

# Fix PB056
assert len(df.loc[df.id == "PB056D"]) == 1
assert (df.loc[df.id == "PB056D", "group_id"] == "PBD").all()
df.loc[df.id == "PB056D", "group_id"] = "PB"

# Fix categories that are uppercase for some reason
df.loc[df.category.str.isupper(), "category"] = df.category.str.title()

# Fix continued categories
cont = " (cont.)"
df.loc[df.category.str.lower().str.endswith(cont), "category"] = df.category.str.slice(
    stop=-len(cont)
)
df.loc[df.group.str.lower().str.endswith(cont), "group"] = df.group.str.slice(stop=-len(cont))

# Group ID counts
group_id_counts = df.groupby("group").apply(lambda g: g.group_id.value_counts().to_dict())
# Multiples in a certain group mostly come from different bass scale length subgroups

# Check some of the tension calculations
import numpy as np
from pyabc2 import Pitch

# pip install --no-deps https://github.com/zmoon/pyabc2/archive/main.zip

cats = ["Acoustic or Electric Guitar", "Acoustic Guitar", "Folk Guitar", "Classical Guitar"]
L = 25.5  # scale length, used for the non-bass guitar categories (inches)
df_ = df[df.category.isin(cats)]
for i, row in df_.iterrows():
    UW = row.uw
    F = np.array([Pitch.from_name(note).etf if note is not None else np.nan for note in row.notes])
    # ^ frequency (Hz)
    T = UW * (2 * L * F) ** 2 / 386.4
    # ^ tension (lb)
    T0 = np.array([ten if ten is not None else np.nan for ten in row.tens])
    np.testing.assert_allclose(
        T[~np.isnan(T0)], T0[~np.isnan(T0)], atol=0.07, rtol=0, equal_nan=True
    )

# Save
fn = "daddario-tension.csv"
fp = HERE / "../stringcalc/data" / fn
assert fp.parent.is_dir()
df.to_csv(fp, index=False)

# Reload
df2 = pd.read_csv(fp, header=0)
