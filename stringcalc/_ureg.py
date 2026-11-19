"""Shared Pint unit registry and input/unit helpers for stringcalc."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Final, Union

from pint import (
    Context,
    DimensionalityError,
    Quantity,
    Unit,
    UnitRegistry,
)

if TYPE_CHECKING:
    from pint.facets.plain import PlainQuantity as _QuantityType
    from pint.facets.plain import PlainUnit as _UnitType
else:
    _QuantityType = Quantity
    _UnitType = Unit


def _preprocess_quotes(s: str) -> str:
    """Replace inch quote symbols with ``inch`` before Pint tokenizes."""
    return s.replace('"', " inch ").replace("″", " inch ")


ureg: Final[UnitRegistry] = UnitRegistry(preprocessors=[_preprocess_quotes])
ureg.define("@alias pound = lbm")


def _mass_to_force(
    ureg: UnitRegistry[Any], value: _QuantityType[Any], **kwargs: Any
) -> _QuantityType[Any]:
    return value * ureg.g0


def _force_to_mass(
    ureg: UnitRegistry[Any], value: _QuantityType[Any], **kwargs: Any
) -> _QuantityType[Any]:
    return value / ureg.g0


_gravity_ctx = Context("gravity")
_gravity_ctx.add_transformation("[mass]", "[force]", _mass_to_force)
_gravity_ctx.add_transformation("[force]", "[mass]", _force_to_mass)
ureg.add_context(_gravity_ctx)
ureg.formatter.default_format = "~P"

QLike = Union[Quantity, str]


_MASS_TO_FORCE_UNIT: dict[_UnitType, str] = {
    ureg.Unit("pound"): "lbf",
    ureg.Unit("kilogram"): "kgf",
    ureg.Unit("gram"): "gf",
    ureg.Unit("ounce"): "ozf",
}


def _to_force_quantity(q: Quantity, *, strict: bool = False) -> Quantity:
    """Convert a mass quantity to its standard-gravity force equivalent."""
    if not q.check("[mass]"):
        return q
    target = _MASS_TO_FORCE_UNIT.get(q.units)
    if target is None:
        if strict:
            raise ValueError(f"Unsupported mass unit for force output: {q.units}")
        target = "lbf"
    return q.to(target, "gravity")


def _check_positive(val: float | Quantity, name: str) -> None:
    """Raise ``ValueError`` unless ``val`` is strictly positive and finite."""
    mag = float(val.magnitude) if isinstance(val, Quantity) else float(val)
    if not (0 < mag < math.inf):
        raise ValueError(f"`{name}` must be positive and finite")


def _normalize_input(
    val: float | QLike,
    dim: str,
    *,
    allow_mass_as_force: bool = False,
) -> float | Quantity:
    """Coerce ``str`` / ``Quantity`` inputs and verify dimensionality.

    Plain numbers are returned as ``float`` (default units assumed).
    """
    if isinstance(val, str):
        q: Quantity = ureg.Quantity(val)
    elif isinstance(val, ureg.Quantity):
        q = val
    elif isinstance(val, Quantity):
        q = ureg.Quantity(val.magnitude, f"{val.units:D}")
    else:
        return float(val)

    if allow_mass_as_force and q.check("[mass]"):
        q = _to_force_quantity(q)

    if not q.check(dim):
        raise DimensionalityError(
            q.units,
            dim,
            str(ureg.get_dimensionality(q.units)),
            str(ureg.get_dimensionality(dim)),
        )

    return q


def _to_magnitude(
    val: float | QLike,
    target_unit: str,
    *,
    default_unit: str | None = None,
    allow_mass_as_force: bool = False,
) -> tuple[float, _UnitType | None]:
    """Convert ``val`` to a magnitude in ``target_unit`` and return its input unit (or ``None``)."""
    if isinstance(val, (str, Quantity)):
        norm = _normalize_input(val, target_unit, allow_mass_as_force=allow_mass_as_force)
        assert isinstance(norm, Quantity)
        return float(norm.to(target_unit, "gravity").magnitude), norm.units
    if default_unit is not None:
        return (
            float(ureg.Quantity(float(val), default_unit).to(target_unit, "gravity").magnitude),
            None,
        )
    return float(val), None
