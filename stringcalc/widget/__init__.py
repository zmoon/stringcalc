"""Interactive notebook widgets (via ``anywidget``) sharing the web app UI.

Install the optional extra to use this module::

    pip install stringcalc[widget]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import pandas as pd

try:
    import anywidget
    import traitlets
except ImportError as e:
    raise ImportError(
        "stringcalc.widget requires 'anywidget' and 'traitlets'. "
        "Install them with: pip install stringcalc[widget]"
    ) from e

from .._app import (
    get_catalog,
    load_presets,
    run_exact_gauge,
    run_frets,
    run_scale_length,
    run_suggest_gauge,
)

__all__ = (
    "ExactGaugeWidget",
    "FretsWidget",
    "GaugeSuggestWidget",
    "ScaleLengthWidget",
)

_BUNDLE_PATH = Path(__file__).parent / "_bundle.js"

_DEFAULT_FANNED_IN: dict[str, Any] = {
    "enabled": False,
    "L_bass": 27.0,
    "L_treble": 25.5,
    "nutWidth": 1.89,
    "edgeBass": 0.15625,
    "edgeTreble": 0.125,
}


def _default_fanned(length_unit: str = "in") -> dict[str, Any]:
    factor = 25.4 if length_unit == "mm" else 1.0
    return {
        k: (round(v * factor, 3) if isinstance(v, float) and factor != 1.0 else v)
        for k, v in _DEFAULT_FANNED_IN.items()
    }


def _load_esm() -> str:
    if not _BUNDLE_PATH.exists():
        raise FileNotFoundError(
            f"Widget JS bundle not found at {_BUNDLE_PATH}. "
            "Build it with: npm --prefix frontend run build:widgets"
        )
    return _BUNDLE_PATH.read_text(encoding="utf-8")


def _preset_fields(preset_id: str) -> dict[str, Any]:
    for p in load_presets():
        if p["id"] == preset_id:
            p_L = float(p["L"])
            lu = str(p["lengthUnit"])
            return {
                "preset": preset_id,
                "length_unit": lu,
                "tension_unit": str(p["tensionUnit"]),
                "L": p_L,
                "types": list(p["types"]),
                "strings": [
                    {
                        "pitch": str(s["pitch"]),
                        "T": float(s["T"]),
                        "L": float(s.get("L", p_L)),
                    }
                    for s in p["strings"]
                ],
                "fanned": {**_default_fanned(lu), **(p.get("fanned") or {})},
            }
    valid = [p["id"] for p in load_presets()]
    raise ValueError(f"Unknown preset {preset_id!r}. Valid presets: {valid}")


class _BaseWidget(anywidget.AnyWidget):
    _esm = _BUNDLE_PATH if _BUNDLE_PATH.exists() else ""
    _widget_name = traitlets.Unicode("").tag(sync=True)
    _input_traits: ClassVar[frozenset[str]] = frozenset()

    def __init__(self, **kwargs: Any) -> None:
        if not self._esm and "_esm" not in kwargs:
            kwargs["_esm"] = _load_esm()
        self._recomputing = True
        try:
            super().__init__(**kwargs)
        finally:
            self._recomputing = False
        self._recompute()

    def set_state(self, sync_data: dict[str, Any]) -> None:
        # Batch multi-trait updates coming from the JS frontend into a single recompute.
        self._recomputing = True
        try:
            super().set_state(sync_data)
        finally:
            self._recomputing = False
        if self._input_traits.intersection(sync_data):
            self._recompute()

    @traitlets.observe(traitlets.All)
    def _on_any_change(self, change: Any) -> None:
        if self._recomputing or change["name"] not in self._input_traits:
            return
        self._before_recompute(change["name"])
        self._recompute()

    def _before_recompute(self, _changed_name: str) -> None:
        pass

    def _recompute(self) -> None:
        raise NotImplementedError


class GaugeSuggestWidget(_BaseWidget):
    """Interactive multi-string gauge suggestion widget."""

    _widget_name = traitlets.Unicode("gauge-suggest").tag(sync=True)
    _input_traits = frozenset(
        {"preset", "length_unit", "tension_unit", "n", "L", "types", "strings", "fanned"}
    )

    preset = traitlets.Unicode("guitar-6").tag(sync=True)
    length_unit = traitlets.Unicode("in").tag(sync=True)
    tension_unit = traitlets.Unicode("lbf").tag(sync=True)
    n = traitlets.Int(5).tag(sync=True)
    L = traitlets.Float(25.5).tag(sync=True)
    types = traitlets.List(traitlets.Unicode()).tag(sync=True)
    strings = traitlets.List(traitlets.Dict()).tag(sync=True)
    fanned = traitlets.Dict().tag(sync=True)
    catalog = traitlets.Dict().tag(sync=True)
    results = traitlets.Dict().tag(sync=True)

    def __init__(
        self,
        *,
        preset: str | None = "guitar-6",
        L: float | None = None,
        T: float | None = None,
        strings: list[dict[str, Any]] | None = None,
        types: list[str] | set[str] | None = None,
        n: int = 5,
        length_unit: str | None = None,
        tension_unit: str | None = None,
        fanned: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if preset:
            init_state = _preset_fields(preset)
        else:
            lu = length_unit or "in"
            init_state = {
                "preset": "",
                "length_unit": lu,
                "tension_unit": "lbf",
                "L": 25.5,
                "types": ["DA:PB", "DA:PL"],
                "strings": [{"pitch": "E2", "T": 16.5, "L": 25.5}],
                "fanned": _default_fanned(lu),
            }

        init_state["n"] = n
        init_state["catalog"] = get_catalog()

        if length_unit is not None and length_unit != init_state["length_unit"]:
            init_state["length_unit"] = length_unit
            if fanned is None:
                init_state["fanned"] = _default_fanned(length_unit)
        if tension_unit is not None:
            init_state["tension_unit"] = tension_unit
        if L is not None:
            init_state["L"] = float(L)
            for s in init_state["strings"]:
                s["L"] = float(L)
        if T is not None:
            for s in init_state["strings"]:
                s["T"] = float(T)
        if strings is not None:
            base_L = float(init_state["L"])
            init_state["strings"] = [
                {
                    "pitch": str(s["pitch"]),
                    "T": float(s["T"]),
                    "L": float(s.get("L", base_L)),
                }
                for s in strings
            ]
        if types is not None:
            init_state["types"] = list(types)
        if fanned is not None:
            init_state["fanned"] = {**_default_fanned(init_state["length_unit"]), **fanned}

        init_state.update(kwargs)
        super().__init__(**init_state)

    def _apply_preset_fields(self, preset_id: str) -> None:
        fields = _preset_fields(preset_id)
        self._recomputing = True
        try:
            with self.hold_sync():
                for k, v in fields.items():
                    setattr(self, k, v)
        finally:
            self._recomputing = False

    def apply_preset(self, preset_id: str) -> None:
        """Apply a named instrument preset from ``presets.json``."""
        self._apply_preset_fields(preset_id)
        self._recompute()

    def _before_recompute(self, changed_name: str) -> None:
        if changed_name == "preset" and self.preset:
            self._apply_preset_fields(self.preset)
        elif changed_name == "L":
            # Setting w.L = ... in Python propagates the uniform scale length to all strings.
            self._recomputing = True
            try:
                self.strings = [{**s, "L": self.L} for s in self.strings]
            finally:
                self._recomputing = False

    def _recompute(self) -> None:
        self.results = dict(
            run_suggest_gauge(
                {
                    "lengthUnit": self.length_unit,
                    "tensionUnit": self.tension_unit,
                    "n": self.n,
                    "L": self.L,
                    "types": list(self.types),
                    "strings": list(self.strings),
                    "fanned": dict(self.fanned),
                }
            )
        )

    def to_dataframes(self) -> list[pd.DataFrame]:
        """Return the current per-string suggestions as pandas DataFrames."""
        dfs: list[pd.DataFrame] = []
        lu = self.results.get("lengthUnit", self.length_unit)
        tu = self.results.get("tensionUnit", self.tension_unit)
        for item in self.results.get("strings", []):
            df = pd.DataFrame(
                item.get("suggestions", []),
                columns=["id", "group_id", "gauge_in", "gauge_mm", "T", "dT"],
            )
            df.attrs.update(
                {
                    "pitch": item.get("pitch"),
                    "L": item.get("L"),
                    "T_target": item.get("T_target"),
                    "lengthUnit": lu,
                    "tensionUnit": tu,
                    "warnings": item.get("warnings", []),
                    "error": item.get("error"),
                }
            )
            dfs.append(df)
        return dfs


class ExactGaugeWidget(_BaseWidget):
    """Interactive exact-gauge calculator widget."""

    _widget_name = traitlets.Unicode("exact-gauge").tag(sync=True)
    _input_traits = frozenset(
        {
            "T",
            "tension_unit",
            "L",
            "length_unit",
            "pitch",
            "material",
            "custom_density",
            "density_unit",
        }
    )

    T = traitlets.Float(16.0).tag(sync=True)
    tension_unit = traitlets.Unicode("lbf").tag(sync=True)
    L = traitlets.Float(22.5).tag(sync=True)
    length_unit = traitlets.Unicode("in").tag(sync=True)
    pitch = traitlets.Unicode("E4").tag(sync=True)
    material = traitlets.Unicode("plain steel").tag(sync=True)
    custom_density = traitlets.Float(1.3).tag(sync=True)
    density_unit = traitlets.Unicode("g/cm^3").tag(sync=True)
    catalog = traitlets.Dict().tag(sync=True)
    result = traitlets.Dict().tag(sync=True)

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("catalog", get_catalog())
        super().__init__(**kwargs)

    def _recompute(self) -> None:
        self.result = dict(
            run_exact_gauge(
                {
                    "T": self.T,
                    "tensionUnit": self.tension_unit,
                    "L": self.L,
                    "lengthUnit": self.length_unit,
                    "pitch": self.pitch,
                    "material": self.material,
                    "customDensity": self.custom_density,
                    "densityUnit": self.density_unit,
                }
            )
        )


class FretsWidget(_BaseWidget):
    """Interactive equal-temperament fret positions widget."""

    _widget_name = traitlets.Unicode("frets").tag(sync=True)
    _input_traits = frozenset({"N", "L", "length_unit"})

    N = traitlets.Int(24).tag(sync=True)
    L = traitlets.Float(25.5).tag(sync=True)
    length_unit = traitlets.Unicode("in").tag(sync=True)
    result = traitlets.Dict().tag(sync=True)

    def _recompute(self) -> None:
        self.result = dict(run_frets({"N": self.N, "L": self.L, "lengthUnit": self.length_unit}))

    def to_dataframe(self) -> pd.DataFrame:
        """Return the current fret table as a pandas DataFrame."""
        rows = self.result.get("rows", [])
        if not rows:
            return pd.DataFrame(columns=["d", "dd", "d_inv"])
        return pd.DataFrame(rows).set_index("n")


class ScaleLengthWidget(_BaseWidget):
    """Interactive scale-length-from-fret-distance calculator widget."""

    _widget_name = traitlets.Unicode("scale-length").tag(sync=True)
    _input_traits = frozenset({"a", "b", "d", "length_unit"})

    a = traitlets.Unicode("nut").tag(sync=True)
    b = traitlets.Unicode("1").tag(sync=True)
    d = traitlets.Float(1.4).tag(sync=True)
    length_unit = traitlets.Unicode("in").tag(sync=True)
    result = traitlets.Dict().tag(sync=True)

    def _recompute(self) -> None:
        self.result = dict(
            run_scale_length(
                {"a": self.a, "b": self.b, "d": self.d, "lengthUnit": self.length_unit}
            )
        )
