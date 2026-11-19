"""
String tension calculations.

For example:

- For specified strings, calculate tensions.
- For specified total or per-string tension, suggest strings.
"""

from __future__ import annotations

import math
import re
import warnings
from functools import lru_cache
from typing import NamedTuple, Protocol, cast

import numpy as np
import pandas as pd
from pint import Quantity

from ._ureg import QLike, _check_positive, _to_magnitude, ureg


def _get_data():
    from importlib.resources import files

    from . import data

    return files(data)


DATA = _get_data()


def _assure_string(s: pd.Series) -> pd.Series[str]:
    """For pandas(-stubs), assure type checker that a Series is of string type.
    Really we know that we have pandas string dtype, but pandas-stubs
    doesn't know/care about this yet(?) in terms of concretizing Series.
    """
    assert s.dtype == "string"
    return cast("pd.Series[str]", s)


@lru_cache(1)
def load_data() -> pd.DataFrame:
    """Load all string data.

    .. note::
       Important columns:

       - ``id``: String (product) ID
         (e.g. "DA:PB053" for the string used for the low E in
         D'Addario phosphor bronze acoustic guitar light set
         `EJ16 <https://www.daddario.com/products/guitar/acoustic-guitar/phosphor-bronze/ej16-phosphor-bronze-acoustic-guitar-strings-light-12-53/>`__).

       - ``group_id``: String group ID (e.g. "DA:PB" for D'Addario phosphor bronze)
         used to identify a group of strings with the same manufacturer, material, etc.

       - ``uw``: String unit weight (mass per unit length) [lbm/in].
         For DA:PB053 this value is 0.000570.

       - ``gauge``: String gauge (diameter) [in].
         For DA:PB053 this value is 0.053.

       The "DA:" prefix in ``id`` and ``group_id``
       indicates the data is from :func:`load_daddario_data`.

    Notes
    -----
    Combines results from the individual ``load_*_data`` functions
    with ``for_combined=True`` applied.

    See Also
    --------
    load_aquila_data
    load_daddario_data
    load_daddario_stp_data
    load_ghs_data
    load_stringjoy_data
    load_worth_data
    """
    df = pd.concat(
        [fn(for_combined=True) for fn in _DATA_LOADERS],
        ignore_index=True,
    )

    for name in ["group", "group_id"]:
        df[name] = df[name].astype("category")

    return df


@lru_cache(2)
def load_daddario_data(*, for_combined: bool = False) -> pd.DataFrame:
    """Load D'Addario data.

    Although outdated in some cases, this data set has the most string types.

    Parameters
    ----------
    for_combined
        Return the frame intended for use in the combined dataset (:func:`load_data`),
        adding appropriate prefixes and dropping extraneous columns.
    """

    df = pd.read_csv(DATA.joinpath("daddario-tension.csv"), header=0).convert_dtypes()

    if for_combined:
        df = df.drop(columns=["notes", "tens"])

        df["group"] = (
            "D'Addario - " + _assure_string(df["category"]) + " - " + _assure_string(df["group"])
        )
        df["group_id"] = "DA:" + _assure_string(df["group_id"])
        df["id"] = "DA:" + _assure_string(df["id"])

        df = df.drop(columns=["category", "id_pref", "id_suff"])

    # Set categorical columns
    for name in ["category", "group", "id_pref", "id_suff", "group_id"]:
        if name in df.columns:
            df[name] = df[name].astype("category")

    return df


@lru_cache(1)
def _get_daddario_group_ids() -> set[str]:
    return set(load_daddario_data(for_combined=False).group_id.cat.categories)


@lru_cache
def _load_aquila_data_cached(
    *, nng_density_lbm_in3: float, for_combined: bool = False
) -> pd.DataFrame:
    df = pd.read_csv(DATA.joinpath("aquila-nng.csv"), header=0).convert_dtypes()

    # Compute UW [lbm / in]
    df["uw"] = nng_density_lbm_in3 * (np.pi * df.gauge**2 / 4)

    # Set group ID (used to select string type)
    df["group"] = "New Nylgut"
    df["group_id"] = "NNG"
    df[["group", "group_id"]] = df[["group", "group_id"]].astype("string")

    gauge_eqv_cols = [col for col in df.columns if col.startswith("gauge_")]
    if for_combined:
        df["group"] = "Aquila " + _assure_string(df["group"])
        df["group_id"] = "A:" + _assure_string(df["group_id"])
        df["id"] = "A:" + _assure_string(df["id"])

        df = df.drop(columns=gauge_eqv_cols)
    else:
        df = df.rename(columns={col: col.replace("gauge_", "gauge_eqv_") for col in gauge_eqv_cols})

    for name in ["group", "group_id"]:
        df[name] = df[name].astype("category")

    return df


def load_aquila_data(
    *, nng_density: float | QLike = 1300, for_combined: bool = False
) -> pd.DataFrame:
    """Load Aquila NNG (New Nylgut) data.

    Parameters
    ----------
    nng_density
        Assumed density of Aquila NNG strings.
        If a plain float is given, it is assumed to be in [kg m-3].
        Can also be a Pint quantity or unit string (e.g. ``'1.3 g/cm^3'``).
        They are supposed to be the same density as gut.
        https://www.cs.helsinki.fi/u/wikla/mus/Calcs/wwwscalc.html says gut is 1276 kg m-3;
        I have seen 1300 elsewhere.
    for_combined
        Return the frame intended for use in the combined dataset (:func:`load_data`),
        adding appropriate prefixes and dropping extraneous columns.
    """
    rho_lbm_in3, _ = _to_magnitude(nng_density, "lbm / inch ** 3", default_unit="kg / m ** 3")
    _check_positive(rho_lbm_in3, "nng_density")

    return _load_aquila_data_cached(nng_density_lbm_in3=rho_lbm_in3, for_combined=for_combined)


@lru_cache(2)
def load_worth_data(*, for_combined: bool = False) -> pd.DataFrame:
    """Load Worth fluorocarbon data.

    Parameters
    ----------
    for_combined
        Return the frame intended for use in the combined dataset (:func:`load_data`),
        adding appropriate prefixes and dropping extraneous columns.
    """

    df = pd.read_csv(DATA.joinpath("worth.csv"), header=0).convert_dtypes()

    # Set group ID (used to select string type)
    df["group"] = "Fluorocarbon"
    df["group_id"] = "FC"
    df[["group", "group_id"]] = df[["group", "group_id"]].astype("string")

    if for_combined:
        df["group"] = "Worth " + _assure_string(df["group"])
        df["group_id"] = "W" + _assure_string(df["group_id"])
        df["id"] = "WFC:" + _assure_string(df["id"])

        df = df.drop(columns="rho")

    for name in ["group", "group_id"]:
        df[name] = df[name].astype("category")

    return df


@lru_cache(2)
def load_stringjoy_data(*, for_combined: bool = False) -> pd.DataFrame:
    """Load Stringjoy data.

    https://tension.stringjoy.com/

    Parameters
    ----------
    for_combined
        Return the frame intended for use in the combined dataset (:func:`load_data`),
        adding appropriate prefixes and dropping extraneous columns.
    """

    df = pd.read_csv(DATA.joinpath("stringjoy.csv"), header=0).convert_dtypes()

    if for_combined:
        df["id"] = "SJ:" + _assure_string(df["id"])
        df["group"] = "Stringjoy " + _assure_string(df["group"])
        df["group_id"] = "SJ:" + _assure_string(df["group_id"])

    for name in ["group", "group_id"]:
        df[name] = df[name].astype("category")

    return df


@lru_cache(2)
def load_ghs_data(*, for_combined: bool = False) -> pd.DataFrame:
    """Load GHS data.

    https://www.ghsstrings.com/pages/tension-calc

    Parameters
    ----------
    for_combined
        Return the frame intended for use in the combined dataset (:func:`load_data`),
        adding appropriate prefixes and dropping extraneous columns.
    """

    df = pd.read_csv(DATA.joinpath("ghs.csv"), header=0).convert_dtypes()

    # Drop ID dupes (e.g. PL which is included for both acoustic and electric)
    df = df.drop_duplicates(subset=["id"], keep="first")

    # Drop where we don't have gauge (bass strings for different scale lengths)
    df = df.dropna(subset=["gauge"])

    if for_combined:
        df["id"] = "GHS:" + _assure_string(df["id"])
        df["group"] = "GHS - " + _assure_string(df["group"])
        df["group_id"] = "GHS:" + _assure_string(df["group_id"])

    for name in ["group", "group_id"]:
        df[name] = df[name].astype("category")

    return df.reset_index(drop=True)


@lru_cache(2)
def load_daddario_stp_data(*, for_combined: bool = False) -> pd.DataFrame:
    """Load D'Addario data derived from the new String Tension Pro (STP).

    https://www.daddario.com/string-tension-pro

    STP is in beta as of June 2024.

    Parameters
    ----------
    for_combined
        Return the frame intended for use in the combined dataset (:func:`load_data`),
        adding appropriate prefixes and dropping extraneous columns.
    """

    df = pd.read_csv(DATA.joinpath("daddario-stp.csv"), header=0).convert_dtypes()

    if for_combined:
        df = df.drop(columns=["instruments"])

        df["id"] = "STP:" + df["id"]
        df["group"] = "D'Addario (STP) - " + df["group"]
        df["group_id"] = "STP:" + df["group_id"]

    for name in ["instruments", "group", "group_id"]:
        if name in df.columns:
            df[name] = df[name].astype("category")

    return df


class _DataLoader(Protocol):
    def __call__(self, *, for_combined: bool = False) -> pd.DataFrame: ...  # noqa: E704


_DATA_LOADERS: list[_DataLoader] = [
    load_daddario_data,
    load_aquila_data,
    load_worth_data,
    load_stringjoy_data,
    load_ghs_data,
    load_daddario_stp_data,
]


_re_string_spec = re.compile(
    r"(?P<L>[\.0-9]+)"
    r" *(?P<Lu>\"|″|in(?:ch(?:es)?)?|[cm]m)"
    r" +(?P<type>[A-Z]+)"
    r" +(?P<gauge>[\.0-9]+)"
    r" *(?P<pw>[pPwW])?"
)


class String(NamedTuple):
    L: float | QLike
    """Scale length (float in inches, or a Pint quantity / string)."""
    type: str
    """String type abbreviation, such as D'Addario "PB", "PL", or "NYL"."""
    gauge: float | QLike
    """String gauge (float in inches, or a Pint quantity / string)."""
    wound: bool
    """Whether the string is wound (as opposed to plain)."""

    # TODO: `wound` isn't really relevant for single string, since `type` tells us whether wound or not
    # i.e., `wound` can be a property (as well as winding and core materials, loop vs ball, ...?)
    # OR: store core and winding material, keeping it more general, instead of using D'Addario IDs

    @classmethod
    def from_spec(cls, s: str):
        """Create a string from spec, e.g. ``'22.9" PB .042w'``."""
        m = _re_string_spec.match(s.strip())
        if m is None:
            raise ValueError(
                f"input {s!r} did not match the spec. "
                "Some valid examples are:\n"
                '  `22.9" PB .042w`'
            )

        d = m.groupdict()

        try:
            L_raw = float(d["L"])
        except Exception as e:
            raise ValueError(
                f"detected string length {d['L']!r} could not be coerced to float"
            ) from e

        L = float(ureg.Quantity(L_raw, d["Lu"]).to("inch").magnitude)

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
        L_in, _ = _to_magnitude(self.L, "inch")
        g_in, _ = _to_magnitude(self.gauge, "inch")

        sgauge = str(g_in)
        if sgauge.startswith("0."):
            sgauge = sgauge[1:]

        return f"{L_in}\" {self.type} {sgauge}{'p' if not self.wound else ''}"

    # TODO: .tune_to() method, returning a TunedString


# TODO: TunedString class with Pitch


def tension(s: String, pitch: str = "A4") -> float | Quantity:
    """Compute tension for :class:`String`.

    Results are for a single type, e.g. plain steel or phosphor bronze.

    Parameters
    ----------
    s
        String of interest.
    pitch
        Pitch name in SPN, e.g. "A4".
    """
    from pyabc2 import Pitch

    t = s.type
    L, u_L = _to_magnitude(s.L, "inch")
    g, u_g = _to_magnitude(s.gauge, "inch")
    _check_positive(L, "L")
    _check_positive(g, "gauge")

    if t in {"PL", "S", "PS"}:  # plain steel
        tda = "DA:PL"
    elif t in {"PB"}:  # phosphor bronze
        tda = "DA:PB"
    elif t in {"NYL", "N"}:  # plain "rectified" nylon
        tda = "DA:NYL"
    elif t in {"NYLW", "NW"}:  # standard silver-wrapped nylon
        tda = "DA:NYLW"
    else:
        raise ValueError(f"string type {t!r} invalid or not supported")

    data = load_data().query(f"group_id == '{tda}'")

    rows = data.loc[data.gauge == g]
    if len(rows) == 0 and u_g is not None:
        rows = data.loc[np.isclose(data.gauge.astype(float), g, atol=1e-6, rtol=0)]

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

    if u_L is not None or u_g is not None:
        return ureg.Quantity(T, "lbf")
    return T


def unit_weight(T: float | QLike, L: float | QLike, pitch: str) -> float | Quantity:
    """From scale length, pitch, and desired tension, compute unit weight
    (mass per unit length) [lbm in-1].

    Parameters
    ----------
    T
        Tension (float in [lbf], or a Pint quantity / string).
        Mass units (e.g. ``'lb'``, ``'kg'``) are converted to force under standard gravity.
    L
        Scale length (float in [in], or a Pint quantity / string).
    pitch
        Pitch name in SPN, e.g. "A4".
    """
    from pyabc2 import Pitch

    T_lbf, u_T = _to_magnitude(T, "lbf", allow_mass_as_force=True)
    L_in, u_L = _to_magnitude(L, "inch")
    _check_positive(T_lbf, "T")
    _check_positive(L_in, "L")

    F = Pitch.from_name(pitch).etf

    UW = (T_lbf * 386.09) / (2 * L_in * F) ** 2

    if u_T is not None or u_L is not None:
        return ureg.Quantity(UW, "lbm / inch")
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


def gauge(
    density: float | QLike, T: float | QLike, L: float | QLike, pitch: str
) -> float | Quantity:
    """From density, scale length, pitch, and desired tension, compute gauge.
    Not nominal gauge, precise diameter.

    Parameters
    ----------
    density
        String material density (float in [lbm in-3], or a Pint quantity / string,
        e.g. ``'1.14 g/cm^3'`` or ``'1300 kg/m^3'``).
    T
        Tension (float in [lbf], or a Pint quantity / string).
        Mass units (e.g. ``'lb'``, ``'kg'``) are converted to force under standard gravity.
    L
        Scale length (float in [in], or a Pint quantity / string).
    pitch
        Pitch name in SPN, e.g. "A4".
    """
    rho_lbm_in3, u_rho = _to_magnitude(density, "lbm / inch ** 3")
    _check_positive(rho_lbm_in3, "density")
    T_lbf, u_T = _to_magnitude(T, "lbf", allow_mass_as_force=True)
    L_in, u_L = _to_magnitude(L, "inch")

    UW = unit_weight(T_lbf, L_in, pitch)
    assert isinstance(UW, float)

    # mu = rho pi r^2
    # => r = sqrt(mu / (rho pi))
    # => d = 2 sqrt(mu / (rho pi))
    d = 2 * math.sqrt(UW / (rho_lbm_in3 * math.pi))

    if u_rho is not None or u_T is not None or u_L is not None:
        return ureg.Quantity(d, "inch")
    return d


def suggest_gauge(
    T: float | QLike, L: float | QLike, pitch: str, *, types: set[str] | None = None, n: int = 3
) -> pd.DataFrame:
    """For target tension, given scale length, and pitch, return suggested gauge(s).

    Two types are commonly used to make string sets, e.g.
    plain steel + phosphor bronze for steel-string acoustic guitar
    or plain nylon + silver-wrapped nylon for classical guitar.

    Parameters
    ----------
    T
        Tension (float in [lbf], or a Pint quantity / string).
        Mass units (e.g. ``'lb'``, ``'kg'``) are converted to force under standard gravity.
        If units are supplied, the returned ``T`` and ``dT`` columns will use those units.
    L
        Scale length (float in [in], or a Pint quantity / string).
    pitch
        Pitch name in ASCII `SPN <https://en.wikipedia.org/wiki/Scientific_pitch_notation>`__,
        e.g. "A4" (A440), which is a fourth above the guitar's high E string.
        Guitar standard tuning: E2 A2 D3 G3 B3 E4.
    types
        String type IDs
        (column ``group_id`` in the :func:`data table <load_data>`)
        to consider.
        If unset, defaults to D'Addario phosphor bronze and plain steel
        (``{'DA:PB', 'DA:PL'}``).
    n
        Number of suggestions to include in the returned frame.
    """
    from pyabc2 import Pitch

    T_lbf, u_T = _to_magnitude(T, "lbf", allow_mass_as_force=True)
    L_in, _ = _to_magnitude(L, "inch")
    _check_positive(T_lbf, "T")
    _check_positive(L_in, "L")

    if types is None:
        types = {"DA:PB", "DA:PL"}

    # Assume D'Addario if match to an original D'Addario group ID (with no `DA:` prefix)
    daddario_group_ids = _get_daddario_group_ids()
    types_in = types
    types = {t if t not in daddario_group_ids else f"DA:{t}" for t in types}
    types_changed = types_in - types
    if types_changed:
        warnings.warn(
            f"string type groups {sorted(types_changed)} assumed to be D'Addario. "
            f"Use group ID prefix 'DA:' to be explicit and avoid this warning.",
            stacklevel=2,
        )

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
    T_all = UW * (2 * L_in * F) ** 2 / 386.09

    # Find closest ones
    data_sort = data.iloc[(T_all - T_lbf).abs().argsort().iloc[:n]].copy()
    data_sort["T"] = T_all[data_sort.index]
    data_sort["dT"] = data_sort["T"] - T_lbf

    b = 1.7  # TODO: allow to set this?
    if (data_sort["dT"] > b).all() or (data_sort["dT"] < -b).all():
        warnings.warn(
            f"(T={T}, L={L}, P={pitch}) "
            f"is outside the range of what string type group(s) {types} can provide. "
            "Maybe a different string type can give the tension/pitch/length you desire.",
            stacklevel=2,
        )

    if u_T is not None:
        conv = float(ureg.Quantity(1.0, "lbf").to(u_T, "gravity").magnitude)
        data_sort["T"] = data_sort["T"] * conv
        data_sort["dT"] = data_sort["dT"] * conv
        u_T_str: str | None = f"{u_T}"
    else:
        u_T_str = None

    df = data_sort[["id", "T", "dT"]].sort_values(by="dT").reset_index(drop=True)
    unit_suffix = f" ({u_T_str})" if u_T_str is not None else ""
    df.attrs.update(
        {
            "units": {"T": u_T_str, "dT": u_T_str} if u_T_str is not None else None,
            "col_desc": {
                "id": "Product ID",
                "T": f"Tension{unit_suffix}",
                "dT": f"Tension difference from target tension{unit_suffix}",
            },
            "fancy_col": {
                "id": "ID",
                "T": "T",
                "dT": "ΔT",
            },
        }
    )

    return df
