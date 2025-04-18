"""
Fret distance calculations.

For example:

- compute equal-temperament fret locations for a given scale length
- compute the scale length implied by a given fret-to-fret distance
"""

from __future__ import annotations

from typing import Union

import numpy as np
import numpy.typing as npt  # v1.21 needed
import pandas as pd
from pint import Quantity, UnitRegistry

ureg = UnitRegistry()
# Q_ = ureg.Quantity  # mypy doesn't like this one

QLike = Union[Quantity, str]

# Note also `pint._typing.UnitLike`


def distance_et(n: int | npt.ArrayLike, *, L: float) -> np.float64 | npt.NDArray[np.float64]:
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
        Scale length.
    """
    n = np.floor(n, dtype=np.float64)

    if not np.all(n > 0):
        raise ValueError("input fret numbers should be positive")

    return (L * (1 - 2 ** (-n / 12))).astype(np.float64)


def distances(N: int, *, L: float, method: str = "et") -> pd.DataFrame:
    """Fret distance DataFrame for `N` frets and scale length `L`.

    Parameters
    ----------
    N
        Number of frets (not including nut) to compute.
    L
        Scale length.
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
    n = np.arange(1, N + 1)

    if method in {"et"}:
        d = distance_et(n, L=L)
    else:
        raise ValueError(f"invalid `method` {method!r}")

    dd = np.append(d[0], np.diff(d))  # type: ignore[index]

    # TODO: d to +5 or +7 frets?
    # TODO: comparison to just intonation for specified root

    df = pd.DataFrame({"n": n, "d": d, "dd": dd, "d_inv": L - d}).set_index("n")
    desc = {
        "n": "fret number",
        "d": "distance from nut to fret",
        "dd": "distance from previous fret to current",
        "d_inv": "distance from fret to saddle",
    }
    fancy_col = {
        "n": "n",
        "d": "d",
        "dd": "Δd",
        "d_inv": "L−d",
    }
    df.attrs.update(col_desc=desc, fancy_col=fancy_col)

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
    <Quantity(21.04, 'inch')>
    """
    if isinstance(d, str):
        d = ureg(d)

    if not d > 0:
        raise ValueError("`d` must be positive")

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
    L = 21
    N = 19
    units = "inches"
    float_format = "%.3f"

    df = distances(N, L=L)

    if units.lower() in {"inches", "in", "in.", '"'}:
        su_l = '"'
        su_si = "in"
    elif units.lower() in {"mm"}:
        su_l = su_si = "mm"
    else:
        raise ValueError(f"invalid `units` {units!r}")

    print(f'L = {L}" (scale length)')
    print(df.to_string(float_format=float_format))  # type: ignore[call-overload]
    l = max(len(s) for s in df.attrs["col_desc"])  # noqa: E741
    for k, v in df.attrs["col_desc"].items():
        print(f"{k:{l+2}}{v}{'' if k == 'n' else f' ({su_si})'}")
