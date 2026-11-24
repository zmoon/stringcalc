"""JSON-serializable backend helpers shared by the Pyodide web app and anywidget wrappers."""

from __future__ import annotations

import json
import math
import warnings
from collections.abc import Callable
from functools import lru_cache
from typing import Any, TypedDict

from pint import PintError, Quantity

from . import __version__
from ._ureg import ureg
from .frets import distances, length_from_distance
from .tension import (
    DATA,
    DENSITY_LB_IN,
    fanned_scale_lengths,
    gauge,
    load_data,
    suggest_gauge,
)


class StringTypeInfo(TypedDict):
    id: str
    brand: str
    label: str


class CatalogResponse(TypedDict):
    version: str
    presets: list[dict[str, Any]]
    stringTypes: list[StringTypeInfo]
    densities: dict[str, float]


class SuggestionItem(TypedDict):
    id: str
    group_id: str
    gauge_in: float | None
    gauge_mm: float | None
    T: float
    dT: float


class StringSuggestionResult(TypedDict):
    index: int
    pitch: str
    L: float | None
    T_target: float | None
    bestIndex: int | None
    warnings: list[str]
    error: str | None
    suggestions: list[SuggestionItem]


class SuggestGaugeResponse(TypedDict):
    error: str | None
    lengthUnit: str
    tensionUnit: str
    fannedLengths: list[float] | None
    strings: list[StringSuggestionResult]


class ExactGaugeResponse(TypedDict):
    gauge_in: float | None
    gauge_mm: float | None
    error: str | None


class FretRow(TypedDict):
    n: int
    d: float
    dd: float
    d_inv: float


class FretsResponse(TypedDict):
    rows: list[FretRow]
    lengthUnit: str
    error: str | None


class ScaleLengthResponse(TypedDict):
    L: float | None
    L_in: float | None
    L_mm: float | None
    lengthUnit: str
    error: str | None


_LENGTH_UNITS = {"in", "mm", "cm"}
_TENSION_UNITS = {"lbf", "kgf", "N"}
_DENSITY_UNITS = {"lbm/in^3", "g/cm^3", "kg/m^3"}

_BRAND_RULES: list[tuple[str, str, str]] = [
    ("DA:", "D'Addario (Chart)", "D'Addario - "),
    ("STP:", "D'Addario (STP)", "D'Addario (STP) - "),
    ("SJ:", "Stringjoy", "Stringjoy "),
    ("GHS:", "GHS", "GHS - "),
    ("A:", "Aquila", "Aquila "),
    ("WFC", "Worth", "Worth "),
]


def _brand_and_label(group_id: str, raw_labels: list[str]) -> tuple[str, str]:
    brand = "Other"
    strip_prefix = ""
    for prefix, b, p in _BRAND_RULES:
        if group_id.startswith(prefix):
            brand = b
            strip_prefix = p
            break

    cleaned: list[str] = []
    for lbl in raw_labels:
        s = lbl[len(strip_prefix) :] if strip_prefix and lbl.startswith(strip_prefix) else lbl
        if s not in cleaned:
            cleaned.append(s)

    if len(cleaned) <= 2:
        label = " / ".join(cleaned)
    else:
        label = f"{cleaned[0]} / {cleaned[1]} (+{len(cleaned) - 2} more)"

    return brand, label


@lru_cache(1)
def load_presets() -> list[dict[str, Any]]:
    """Load instrument presets from ``stringcalc/data/presets.json``."""
    raw = DATA.joinpath("presets.json").read_text(encoding="utf-8")
    presets = json.loads(raw)
    assert isinstance(presets, list)
    return presets


@lru_cache(1)
def _string_metadata() -> dict[str, tuple[float, str]]:
    df = load_data()
    return {
        str(sid): (float(g), str(gid)) for sid, g, gid in zip(df["id"], df["gauge"], df["group_id"])
    }


@lru_cache(1)
def _string_types_catalog() -> list[StringTypeInfo]:
    df = load_data()
    grouped: dict[str, list[str]] = {}
    for row in df[["group_id", "group"]].drop_duplicates().itertuples(index=False):
        gid = str(row.group_id)
        grouped.setdefault(gid, []).append(str(row.group))

    items: list[StringTypeInfo] = []
    for gid in sorted(grouped):
        brand, label = _brand_and_label(gid, grouped[gid])
        items.append({"id": gid, "brand": brand, "label": label})
    return items


def get_catalog() -> CatalogResponse:
    """Return version, presets, string types, and material densities for UI initialization."""
    return {
        "version": __version__,
        "presets": load_presets(),
        "stringTypes": _string_types_catalog(),
        "densities": dict(DENSITY_LB_IN),
    }


def _finite_pos_float(val: Any, name: str) -> float:
    try:
        x = float(val)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name} must be a number") from e
    if not (0 < x < math.inf):
        raise ValueError(f"{name} must be positive and finite")
    return x


def _suggest_error(message: str, *, length_unit: str, tension_unit: str) -> SuggestGaugeResponse:
    return {
        "error": message,
        "lengthUnit": length_unit,
        "tensionUnit": tension_unit,
        "fannedLengths": None,
        "strings": [],
    }


def run_suggest_gauge(req: dict[str, Any]) -> SuggestGaugeResponse:
    """Run multi-string gauge suggestions from a JSON-compatible request dict."""
    length_unit = str(req.get("lengthUnit", "in"))
    tension_unit = str(req.get("tensionUnit", "lbf"))
    fanned_lengths: list[float] | None = None

    try:
        if length_unit not in _LENGTH_UNITS:
            raise ValueError(f"Unsupported length unit {length_unit!r}")
        if tension_unit not in _TENSION_UNITS:
            raise ValueError(f"Unsupported tension unit {tension_unit!r}")

        try:
            n = int(req.get("n", 5))
        except (TypeError, ValueError) as e:
            raise ValueError("Number of suggestions must be an integer") from e
        if not (1 <= n <= 20):
            raise ValueError("Number of suggestions must be between 1 and 20")

        types = {str(t) for t in (req.get("types") or []) if str(t).strip()}
        if not types:
            raise ValueError("Select at least one string type.")

        strings_in = req.get("strings") or []
        if not isinstance(strings_in, list) or not strings_in:
            raise ValueError("Add at least one string.")

        fanned = req.get("fanned")
        if isinstance(fanned, dict) and fanned.get("enabled"):
            L_bass = _finite_pos_float(fanned.get("L_bass"), "Bass scale length")
            L_treble = _finite_pos_float(fanned.get("L_treble"), "Treble scale length")
            nut_width = _finite_pos_float(fanned.get("nutWidth"), "Nut width")
            edges = [
                ureg.Quantity(float(v), length_unit)
                for v in (fanned.get("edgeBass"), fanned.get("edgeTreble"))
                if v is not None and v != ""
            ]
            Ls_q = fanned_scale_lengths(
                ureg.Quantity(L_bass, length_unit),
                ureg.Quantity(L_treble, length_unit),
                len(strings_in),
                nut_width=ureg.Quantity(nut_width, length_unit),
                edge_space=edges or None,
            )
            fanned_lengths = [
                round(float(x.magnitude) if isinstance(x, Quantity) else float(x), 4) for x in Ls_q
            ]
    except (ValueError, PintError) as e:
        return _suggest_error(str(e), length_unit=length_unit, tension_unit=tension_unit)

    meta = _string_metadata()
    default_L = req.get("L")
    results: list[StringSuggestionResult] = []

    for idx, s in enumerate(strings_in):
        pitch = str(s.get("pitch", "")).strip()
        L_raw = fanned_lengths[idx] if fanned_lengths is not None else s.get("L", default_L)
        T_raw = s.get("T")
        entry: StringSuggestionResult = {
            "index": idx,
            "pitch": pitch,
            "L": None,
            "T_target": None,
            "bestIndex": None,
            "warnings": [],
            "error": None,
            "suggestions": [],
        }

        try:
            if not pitch:
                raise ValueError("Pitch is required")
            L_val = _finite_pos_float(L_raw, "Scale length")
            T_val = _finite_pos_float(T_raw, "Target tension")
            entry["L"] = L_val
            entry["T_target"] = T_val

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                df = suggest_gauge(
                    T=ureg.Quantity(T_val, tension_unit),
                    L=ureg.Quantity(L_val, length_unit),
                    pitch=pitch,
                    types=types,
                    n=n,
                )

            entry["warnings"] = [str(w.message) for w in caught]
            suggestions: list[SuggestionItem] = []
            for sid_raw, t_raw, dt_raw in zip(df["id"], df["T"], df["dT"]):
                sid = str(sid_raw)
                g_in, gid = meta.get(sid, (math.nan, ""))
                suggestions.append(
                    {
                        "id": sid,
                        "group_id": gid,
                        "gauge_in": round(g_in, 5) if math.isfinite(g_in) else None,
                        "gauge_mm": round(g_in * 25.4, 3) if math.isfinite(g_in) else None,
                        "T": round(float(t_raw), 3),
                        "dT": round(float(dt_raw), 3),
                    }
                )
            entry["suggestions"] = suggestions
            if suggestions:
                entry["bestIndex"] = int(df.dT.abs().argmin())
        except (ValueError, KeyError, PintError) as e:
            entry["error"] = str(e)

        results.append(entry)

    return {
        "error": None,
        "lengthUnit": length_unit,
        "tensionUnit": tension_unit,
        "fannedLengths": fanned_lengths,
        "strings": results,
    }


def run_exact_gauge(req: dict[str, Any]) -> ExactGaugeResponse:
    """Compute exact string diameter from density, tension, scale length, and pitch."""
    length_unit = str(req.get("lengthUnit", "in"))
    tension_unit = str(req.get("tensionUnit", "lbf"))
    density_unit = str(req.get("densityUnit", "g/cm^3"))
    pitch = str(req.get("pitch", "")).strip()
    material = str(req.get("material", "plain steel"))

    try:
        if length_unit not in _LENGTH_UNITS:
            raise ValueError(f"Unsupported length unit {length_unit!r}")
        if tension_unit not in _TENSION_UNITS:
            raise ValueError(f"Unsupported tension unit {tension_unit!r}")
        if not pitch:
            raise ValueError("Pitch is required")

        T_val = _finite_pos_float(req.get("T"), "Tension")
        L_val = _finite_pos_float(req.get("L"), "Scale length")

        if material == "custom":
            if density_unit not in _DENSITY_UNITS:
                raise ValueError(f"Unsupported density unit {density_unit!r}")
            rho_val = _finite_pos_float(req.get("customDensity"), "Density")
            dens: float | Quantity = ureg.Quantity(rho_val, density_unit)
        elif material in DENSITY_LB_IN:
            dens = DENSITY_LB_IN[material]
        else:
            raise ValueError(f"Unknown material {material!r}")

        g = gauge(
            dens,
            T=ureg.Quantity(T_val, tension_unit),
            L=ureg.Quantity(L_val, length_unit),
            pitch=pitch,
        )
        assert isinstance(g, Quantity)
        g_in = float(g.to("inch").magnitude)
        return {
            "gauge_in": round(g_in, 5),
            "gauge_mm": round(g_in * 25.4, 4),
            "error": None,
        }
    except (ValueError, KeyError, PintError) as e:
        return {"gauge_in": None, "gauge_mm": None, "error": str(e)}


def run_frets(req: dict[str, Any]) -> FretsResponse:
    """Compute equal-temperament fret positions table."""
    length_unit = str(req.get("lengthUnit", "in"))
    try:
        if length_unit not in _LENGTH_UNITS:
            raise ValueError(f"Unsupported length unit {length_unit!r}")
        N = int(req.get("N", 24))
        if not (1 <= N <= 48):
            raise ValueError("Number of frets must be between 1 and 48")
        L_val = _finite_pos_float(req.get("L"), "Scale length")

        df = distances(N=N, L=ureg.Quantity(L_val, length_unit)).reset_index()
        rows: list[FretRow] = [
            {
                "n": int(n_v),
                "d": round(float(d_v), 4),
                "dd": round(float(dd_v), 4),
                "d_inv": round(float(d_inv_v), 4),
            }
            for n_v, d_v, dd_v, d_inv_v in zip(df["n"], df["d"], df["dd"], df["d_inv"])
        ]
        return {"rows": rows, "lengthUnit": length_unit, "error": None}
    except (ValueError, PintError) as e:
        return {"rows": [], "lengthUnit": length_unit, "error": str(e)}


def _parse_fret_bound(val: Any) -> int | None:
    if val is None or val == "saddle":
        return None
    if val == "nut":
        return 0
    n = int(val)
    if n < 0:
        raise ValueError("Fret number must be non-negative")
    return n


def run_scale_length(req: dict[str, Any]) -> ScaleLengthResponse:
    """Compute implied scale length from distance between frets a and b."""
    length_unit = str(req.get("lengthUnit", "in"))
    try:
        if length_unit not in _LENGTH_UNITS:
            raise ValueError(f"Unsupported length unit {length_unit!r}")
        a = _parse_fret_bound(req.get("a"))
        b = _parse_fret_bound(req.get("b"))
        d_val = _finite_pos_float(req.get("d"), "Distance")

        L_q = length_from_distance((a, b), ureg.Quantity(d_val, length_unit))
        assert isinstance(L_q, Quantity)
        L_val = float(L_q.magnitude)
        L_in = float(L_q.to("inch").magnitude)
        return {
            "L": round(L_val, 4),
            "L_in": round(L_in, 4),
            "L_mm": round(L_in * 25.4, 3),
            "lengthUnit": length_unit,
            "error": None,
        }
    except (ValueError, PintError) as e:
        return {"L": None, "L_in": None, "L_mm": None, "lengthUnit": length_unit, "error": str(e)}


METHODS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "get_catalog": lambda _req: get_catalog(),
    "run_suggest_gauge": run_suggest_gauge,
    "run_exact_gauge": run_exact_gauge,
    "run_frets": run_frets,
    "run_scale_length": run_scale_length,
}


def dispatch(method: str, payload: dict[str, Any] | None = None) -> Any:
    """Dispatch a JSON-compatible app method call by name."""
    fn = METHODS.get(method)
    if fn is None:
        raise KeyError(f"Unknown method: {method}")
    return fn(payload if payload is not None else {})
