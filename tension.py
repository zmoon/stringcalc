"""
String tension calculations

e.g.
- For specified strings, calculate tensions
- For specified total or per-string tension, suggest strings
"""
import re
from typing import NamedTuple

import pandas as pd


def load_data(*, drop_sample_tensions=True):
    """Load the data (currently only D'Addario) needed for the calculations."""

    df = pd.read_csv("data/daddario-tension.csv", header=0)
    
    if drop_sample_tensions:
        df = df.drop(columns=["notes", "tens"])

    # Set categorical columns
    df = df.convert_dtypes()
    for name in ["category", "group", "group_id"]:
        df[name] = df[name].astype("category")

    return df


_re_string_spec = re.compile(
    r"(?P<L>[\.0-9]+)"
    r" *(?P<Lu>\"|m{2})"
    r" +(?P<type>[A-Z]+)"
    r" +(?P<gauge>[\.[0-9]+)"
    r" *(?P<pw>[pPwW])?"
)

class String(NamedTuple):
    L: float
    type: str
    gauge: float
    wound: bool
    
    @classmethod
    def from_spec(cls, s: str):
        m = _re_string_spec.match(s.strip())
        if m is None:
            raise ValueError(
                f"input {s!r} did not match the spec. "
                "Some valid examples are:\n"
                "  `22.9\" PB .042w`"
            )
        
        d = m.groupdict()
        
        try:
            L = float(d["L"])
        except Exception as e:
            raise ValueError(
                f"detected string length {d['L']!r} could not be coerced to float"
            ) from e
            
        type_ = d["type"]

        try:
            gauge = float(d["gauge"])
        except Exception as e:
            raise ValueError(
                f"detected string gauge {d['gauge']!r} could not be coerced to float"
            ) from e            
        
        pw = d["pw"]
        if pw is None:
            wound = True  # maybe should be configurable
        else:
            pw_ = pw.lower()
            if pw_ == "p":
                wound = False
            elif pw_ == "w":
                wound = True
            else:
                raise ValueError(f"invalid p/w {pw}")
        
        return cls(L, type_, gauge, wound)
