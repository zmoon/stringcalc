"""
String tension calculations

e.g.
- For specified strings, calculate tensions
- For specified total or per-string tension, suggest strings
"""
import re
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import pandas as pd

HERE = Path(__file__).parent
DATA = HERE / "../data"


@lru_cache(2)
def load_data(*, drop_sample_tensions=True):
    """Load the data (currently only D'Addario) needed for the calculations."""

    df = pd.read_csv(DATA/"daddario-tension.csv", header=0)

    if drop_sample_tensions:
        df = df.drop(columns=["notes", "tens"])

    # Set categorical columns
    df = df.convert_dtypes()
    for name in ["category", "group", "id_pref", "group_id"]:
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
    """Scale length."""
    type: str
    """Currently D'Addario string type abbreviation, such as 'PB', 'PL', or 'NYL'."""
    gauge: float
    """String gauge."""
    wound: bool
    """Whether the string is wound (as opposed to plain)."""
    
    # TODO: `wound` isn't really relevant for single string, since `type` tells us whether wound or not
    # i.e., `wound` can be a property (as well as winding and core materials, loop vs ball, ...?)
    # OR: store core and winding material, keeping it more general, instead of using D'Addario IDs
    # TODO: unit support (pint?)

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

        sgauge = d["gauge"]
        if "." not in sgauge and sgauge.startswith("0"):  # leading 0 implies decimal
            sgauge = f".{sgauge}"
        try:
            gauge = float(sgauge)
        except Exception as e:
            raise ValueError(
                f"detected string gauge {sgauge!r} could not be coerced to float"
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

    def __str__(self):
        sgauge = str(self.gauge)
        if sgauge.startswith("0."):
            sgauge = sgauge[1:]

        return f"{self.L}\" {self.type} {sgauge}{'p' if not self.wound else ''}"

    # TODO: .tune_to() method, returning a TunedString

# TODO: TunedString class with Pitch


def ten(s: String):
    """Compute tension for :class:`String`."""
    
    t = s.type
    g = s.gauge
    L = s.L

    if t in {"PL", "S", "PS"}:  # plain steel
        tda = "PL"
    elif t in {"PB"}:  # phosphor bronze
        tda = "PB"
    else:
        raise ValueError(f"string type {t!r} invalid or not supported")

    data = load_data().query(f"id_pref == '{tda}'")

    rows = data.loc[data.gauge == g]
    if len(rows) == 0:
        raise ValueError(
            f"gauge {g} not found. "
            f"Available {tda} gauges are: {', '.join(data.gauge.astype(str))}"
        )
        # TODO: use closest instead with warning?
    elif len(rows) > 1:
        raise ValueError("multiple matching gauges\n{rows.to_string()}")

    UW = float(rows.uw)
    F = 440.  # for testing

    T = UW * (2 * L * F)**2 / 386.

    return T


def from_ten(T: float, L: float, pitch: str, *, type: str = "PB", n: int = 3):
    """For target tension and given scale length, return suggested gauge(s)."""
    from pyabc2 import Pitch

    t = type

    if t == "PB":  # implying PB | PL
        tda = ["PB", "PL"]
    else:
        raise ValueError(f"string type {t!r} invalid or not supported")

    data = load_data().query(f"id_pref in @tda")
    UW = data.uw
    F = Pitch.from_name(pitch).etf
    T_all = UW * (2 * L * F)**2 / 386.

    # Find closest ones
    data_sort = data.iloc[(T_all - T).abs().argsort()[:n]].copy()
    data_sort["T"] = T_all[data_sort.index]
    data_sort["T - T_in"] = data_sort["T"] - T

    # TODO: warning if edge is one of the closest

    df = data_sort[["id", "T", "T - T_in"]].sort_values(by="id").reset_index(drop=True)

    return df
