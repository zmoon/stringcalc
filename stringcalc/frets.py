"""
Fret distance calculations.

For example:

- compute equal-temperament fret locations for a given scale length
- compute the scale length implied by a given fret-to-fret distance
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt  # v1.21 needed
import pandas as pd
from pint import Quantity

from ._ureg import QLike, _check_positive, _normalize_input, ureg

# Note also `pint._typing.UnitLike`


def distance_et(
    n: int | npt.ArrayLike, *, L: float | QLike
) -> np.float64 | npt.NDArray[np.float64] | Quantity:
    r"""Exact equal-temperament distance from nut for fret(s) `n` for scale length `L`.

    Using the 12th-root-of-2 method.

    .. math::

       d_n = L \left( 1 - 2^{-n/12} \right)

    Reference: https://www.liutaiomottola.com/formulae/fret.htm

    Parameters
    ----------
    n
        Fret number (or array-like of them).
        If floats are passed, they will be floored before computing.
    L
        Scale length. Can be a float or a Pint quantity / string (e.g. ``'25.5"'``, ``'650 mm'``).
    """
    L_norm = _normalize_input(L, "[length]")
    _check_positive(L_norm, "L")

    n = np.floor(n, dtype=np.float64)

    if not np.all(n > 0):
        raise ValueError("input fret numbers should be positive")

    factor = (1 - 2 ** (-n / 12)).astype(np.float64)
    if isinstance(L_norm, Quantity):
        return ureg.Quantity(L_norm.magnitude * factor, L_norm.units)
    return (L_norm * factor).astype(np.float64)


def distances(N: int, *, L: float | QLike, method: str = "et") -> pd.DataFrame:
    """Fret distance DataFrame for `N` frets and scale length `L`.

    Parameters
    ----------
    N
        Number of frets (not including nut) to compute.
    L
        Scale length. Can be a float or a Pint quantity / string (e.g. ``'25.5"'``, ``'650 mm'``).
    method
        Method to use for computing fret distances.

        - ``'et'``: equal temperament (:func:`distance_et`)


    .. note::
       Columns:

       - ``n``: fret number (index)
       - ``d``: distance from nut to fret
       - ``dd``: distance from previous fret to current
       - ``d_inv``: distance from fret to saddle
    """
    assert N >= 1  # guarantees `d` is array with at least one value
    L_norm = _normalize_input(L, "[length]")
    _check_positive(L_norm, "L")

    if isinstance(L_norm, Quantity):
        L_mag = float(L_norm.magnitude)
        L_unit_str: str | None = f"{L_norm.units}"
    else:
        L_mag = float(L_norm)
        L_unit_str = None

    n = np.arange(1, N + 1)

    if method in {"et"}:
        d = distance_et(n, L=L_mag)
    else:
        raise ValueError(f"invalid `method` {method!r}")

    assert not isinstance(d, Quantity)
    dd = np.append(d[0], np.diff(d))  # type: ignore[index,call-overload]

    # TODO: d to +5 or +7 frets?
    # TODO: comparison to just intonation for specified root

    df = pd.DataFrame({"n": n, "d": d, "dd": dd, "d_inv": L_mag - d}).set_index("n")
    unit_suffix = f" ({L_unit_str})" if L_unit_str is not None else ""
    df.attrs.update(
        {
            "units": L_unit_str,
            "col_desc": {
                "n": "fret number",
                "d": f"distance from nut to fret{unit_suffix}",
                "dd": f"distance from previous fret to current{unit_suffix}",
                "d_inv": f"distance from fret to saddle{unit_suffix}",
            },
            "fancy_col": {
                "n": "n",
                "d": "d",
                "dd": "Δd",
                "d_inv": "L−d",
            },
        }
    )

    return df


def length_from_distance(ab: tuple[int | None, int | None], d: float | QLike) -> float | Quantity:
    """Calculate the scale length implied by a->b distance `d`.

    Parameters
    ----------
    ab
        `ab` is a 2-tuple ``(a, b)`` specifying the bounds of the input distance `d` in terms of fret number.
        Use ``None`` to indicate the bridge/saddle end of the fretboard
        (and ``0`` to indicate the nut end).
    d
        Distance between ``a`` and ``b``.

        .. note::
           Can use a quantity string that Pint will recognize, e.g. ``'25.5 in'``.
           Then, the output will be a :class:`pint.Quantity` with the same units.

    Examples
    --------

    >>> from stringcalc.frets import length_from_distance
    >>> round(length_from_distance((0, 1), 1.4), 2)
    24.94
    >>> round(length_from_distance((0, 1), "3 cm").to("inch"), 2)
    Quantity(21.04, "inch")
    """
    d = _normalize_input(d, "[length]")
    _check_positive(d, "d")

    a, b = ab

    def c(n):
        if n in {None, np.inf}:
            return 1
        elif n == 0:
            return 0
        else:
            return 1 - 1 / (2 ** (n / 12))

    c_a = c(a)
    c_b = c(b)

    if c_a == c_b:
        raise ValueError("`a` and `b` must be different frets in order to compute L")

    return d / abs(c_b - c_a)


if __name__ == "__main__":
    L = ureg.Quantity(21, "inch")
    N = 19
    float_format = "%.3f"

    df = distances(N, L=L)

    print(f"L = {L} (scale length)")
    print(df.to_string(float_format=float_format))  # type: ignore[call-overload]
    l = max(len(s) for s in df.attrs["col_desc"])  # noqa: E741
    for k, v in df.attrs["col_desc"].items():
        print(f"{k:{l+2}}{v}")
