"""
String tension calculations

e.g.
- For specified strings, calculate tensions
- For specified total or per-string tension, suggest strings
"""
from __future__ import annotations

import math
import re
import warnings
from functools import lru_cache
from typing import Callable, NamedTuple

import pandas as pd


def _get_data():
    from importlib.resources import files

    from . import data

    return files(data)


DATA = _get_data()


@lru_cache(1)
def load_data() -> pd.DataFrame:
    """Load all string data.

    Use the individual `load_*_data` functions for more control.
    """
    df = pd.concat(
        [fn() for fn in _DATA_LOADERS],
        ignore_index=True,
    )

    for name in ["group", "group_id"]:
        df[name] = df[name].astype("category")

    return df


@lru_cache(2)
def load_daddario_data(*, drop_sample_tensions: bool = True) -> pd.DataFrame:
    """Load the data (currently only D'Addario) needed for the calculations."""

    df = pd.read_csv(DATA.joinpath("daddario-tension.csv"), header=0).convert_dtypes()

    if drop_sample_tensions:
        df = df.drop(columns=["notes", "tens"])

    # Set categorical columns
    for name in ["category", "group", "id_pref", "id_suff", "group_id"]:
        df[name] = df[name].astype("category")

    return df


@lru_cache
def load_aquila_data(*, nng_density: float = 1300, drop_gauge_eqvs: bool = True) -> pd.DataFrame:
    """Load Aquila NNG (New Nylgut) data.

    Parameters
    ----------
    nng_density
        Assumed density of Aquila NNG strings, in kg/m3.
        They are supposed to be the same density as gut.
        https://www.cs.helsinki.fi/u/wikla/mus/Calcs/wwwscalc.html says gut is 1276 kg/m3;
        I have seen 1300 elsewhere.
    """
    import numpy as np

    df = pd.read_csv(DATA.joinpath("aquila-nng.csv"), header=0).convert_dtypes()

    # Compute UW
    # TODO: use Pint
    df["uw"] = nng_density * 2.205 / 1e6 * (2.54**3) * (np.pi * df.gauge**2 / 4)

    # Set group ID (used to select string type)
    df["group"] = "Aquila New Nylgut"
    df["group_id"] = "NNG"
    for name in ["group", "group_id"]:
        df[name] = df[name].astype("category")

    # Include gauge equivalents?
    gauge_eqv_cols = [col for col in df.columns if col.startswith("gauge_")]
    if drop_gauge_eqvs:
        df = df.drop(columns=gauge_eqv_cols)
    else:
        df = df.rename(columns={col: col.replace("gauge_", "gauge_eqv_") for col in gauge_eqv_cols})

    return df


@lru_cache(1)
def load_worth_data() -> pd.DataFrame:
    """Load Worth fluorocarbon data."""

    df = pd.read_csv(DATA.joinpath("worth.csv"), header=0).convert_dtypes()

    # Set group ID (used to select string type)
    df["group"] = "Worth Fluorocarbon"
    df["group_id"] = "WFC"
    for name in ["group", "group_id"]:
        df[name] = df[name].astype("category")

    return df


@lru_cache(1)
def load_stringjoy_data() -> pd.DataFrame:
    """Load Stringjoy data.

    https://tension.stringjoy.com/
    """

    df = pd.read_csv(DATA.joinpath("stringjoy.csv"), header=0).convert_dtypes()

    # Differentiate from D'Addario
    df["id"] = "SJ" + df["id"]
    df["group"] = "Stringjoy " + df["group"]
    df["group_id"] = "SJ" + df["group_id"]
    for name in ["group", "group_id"]:
        df[name] = df[name].astype("category")

    return df


@lru_cache(1)
def load_ghs_data() -> pd.DataFrame:
    """Load GHS data.

    https://www.ghsstrings.com/pages/tension-calc
    """

    df = pd.read_csv(DATA.joinpath("ghs.csv"), header=0).convert_dtypes()

    # Drop ID dupes (e.g. PL which is included for both acoustic and electric)
    df = df.drop_duplicates(subset=["id"])

    # Drop where we don't have gauge (bass strings for different scale lengths)
    df = df.dropna(subset=["gauge"])

    # Differentiate from D'Addario
    df["id"] = "GHS" + df["id"]
    df["group"] = "GHS - " + df["group"]
    df["group_id"] = "GHS" + df["group_id"]
    for name in ["group", "group_id"]:
        df[name] = df[name].astype("category")

    return df.reset_index(drop=True)


_DATA_LOADERS: list[Callable[[], pd.DataFrame]] = [
    load_daddario_data,
    load_aquila_data,
    lambda: load_worth_data().drop(columns="rho"),
    load_stringjoy_data,
    load_ghs_data,
]


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
                '  `22.9" PB .042w`'
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


def tension(s: String, pitch: str = "A4") -> float:
    """Compute tension for :class:`String`.

    Results are for a single type, e.g. plain steel or phosphor bronze.
    """
    from pyabc2 import Pitch

    t = s.type
    g = s.gauge
    L = s.L

    if t in {"PL", "S", "PS"}:  # plain steel
        tda = "PL"
    elif t in {"PB"}:  # phosphor bronze
        tda = "PB"
    elif t in {"NYL", "N"}:  # plain "rectified" nylon
        tda = "NYL"
    elif t in {"NYLW", "NW"}:  # standard silver-wrapped nylon
        tda = "NYLW"
    else:
        raise ValueError(f"string type {t!r} invalid or not supported")

    data = load_data().query(f"group_id == '{tda}'")

    rows = data.loc[data.gauge == g]
    if len(rows) == 0:
        raise ValueError(
            f"gauge {g} not found. "
            f"Available {tda} gauges are: {', '.join(data.gauge.astype(str))}"
        )
        # TODO: use closest instead with warning?
    elif len(rows) > 1:
        raise ValueError("multiple matching gauges\n{rows.to_string()}")

    # Starting from
    # 1 / v^2  = mu / T
    # (derivation at https://phys.libretexts.org/Bookshelves/University_Physics/Book%3A_University_Physics_(OpenStax)/Book%3A_University_Physics_I_-_Mechanics_Sound_Oscillations_and_Waves_(OpenStax)/16%3A_Waves/16.04%3A_Wave_Speed_on_a_Stretched_String)
    # => T = mu v^2        [mass / length] * [length time-1]^2 = [mass length time-2]]
    # => T = mu (f wl)^2   since v = f wl
    # => T = mu (2 f L)^2  since the primary mode has wl = 2 L
    #
    # In the D'Addario formula:
    # - UW: "unit weight", really linear density (mu; mass / length) [lbm/in]
    # - L: scale length [in]
    # - F: frequency [Hz := s-1]
    # - T: "tension" [lb] (technically lbf)
    #
    # The scaling factor comes from the conversion from lb (lbm) to lbf
    # i.e., it is gravity in the units of the RHS (seconds and inches)
    # gc = (9.80665 m s-2) * (3.28084 ft m-1) * (12 in ft-1)
    #    = 386.09 in s-2  (technically [in lbm lbf-1 s-2])
    #
    # At g0, 1 lbm exerts a force of 1 lbf => lbf = g0 lbm = 32.174 lbm ft s-2
    # https://en.wikipedia.org/wiki/Gc_(engineering)

    UW = float(rows.uw.iloc[0])
    F = Pitch.from_name(pitch).etf

    T = UW * (2 * L * F) ** 2 / 386.09

    return T


def unit_weight(T: float, L: float, pitch: str) -> float:
    """From scale length, pitch, and desired tension, compute unit weight."""
    from pyabc2 import Pitch

    F = Pitch.from_name(pitch).etf

    UW = (T * 386.09) / (2 * L * F) ** 2

    return UW


DENSITY_LB_IN = {
    "plain steel": 0.285,
    "plain nylon": 0.0412,  # 1.14 g/cm3
}

_STRING_TYPE_ALIASES = {
    "plain steel": {"PL", "PS", "S"},
    "plain nylon": {"N", "NYL"},
    # "silver-wound nylon": {"NW", "NYLW"},
}

_STRING_TYPE_ALIAS_TO_VERBOSE = {
    alias: k for k, aliases in _STRING_TYPE_ALIASES.items() for alias in aliases
}


def gauge(density: float, T: float, L: float, pitch: str) -> float:
    """From density, scale length, pitch, and desired tension, compute gauge.
    Not nominal gauge, precise diameter.
    """

    UW = unit_weight(T, L, pitch)

    # mu = rho pi r^2
    # => r = sqrt(mu / (rho pi))
    # => d = 2 sqrt(mu / (rho pi))
    d = 2 * math.sqrt(UW / (density * math.pi))

    return d


def suggest_gauge(
    T: float, L: float, pitch: str, *, types: set[str] | None = None, n: int = 3
) -> pd.DataFrame:
    """For target tension and given scale length, return suggested gauge(s).

    Results may include two types commonly used to make string sets, e.g.
    plain steel + phosphor bronze or plain nylon + silver-wrapped nylon.
    """
    from pyabc2 import Pitch

    if types is None:
        types = {"PB", "PL"}

    data_all = load_data()
    data = data_all.query("group_id in @types")

    # Validate types
    all_types = set(data_all.group_id.cat.categories)
    invalid_passed_types = set(types) - all_types
    if invalid_passed_types:
        raise ValueError(
            f"string type IDs {sorted(invalid_passed_types)} not found in dataset. "
            f"Use one of {sorted(data_all.group_id.cat.categories)}."
        )

    UW = data.uw
    F = Pitch.from_name(pitch).etf
    T_all = UW * (2 * L * F) ** 2 / 386.09

    # Find closest ones
    data_sort = data.iloc[(T_all - T).abs().argsort().iloc[:n]].copy()
    data_sort["T"] = T_all[data_sort.index]
    data_sort["dT"] = data_sort["T"] - T

    b = 1.7  # TODO: allow to set this?
    if (data_sort["dT"] > b).all() or (data_sort["dT"] < -b).all():
        warnings.warn(
            f"You are outside the range of what string type group(s) {types} can provide. "
            "Maybe a different string type can give the tension/pitch/length you desire.",
            stacklevel=2,
        )

    df = data_sort[["id", "T", "dT"]].sort_values(by="dT").reset_index(drop=True)
    desc = {
        "id": "Product ID",
        "T": "Tension",
        "dT": "Tension difference from target tension",
    }
    fancy_col = {
        "id": "ID",
        "T": "T",
        "dT": "ΔT",
    }
    df.attrs.update(col_desc=desc, fancy_col=fancy_col)

    return df
