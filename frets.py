"""
Fret distances
"""
from __future__ import annotations

import numpy as np
import numpy.typing as npt  # v1.21 needed
import pandas as pd


def d_et(n: int | npt.ArrayLike, *, s: float) -> np.float_ | npt.NDArray[np.float_]:
    """Exact equal temperament distance from nut for fret(s) `n` for scale length `s`.

    Using the 12th root of 2 method.
    
    Reference: https://www.liutaiomottola.com/formulae/fret.htm

    Parameters
    ----------
    n
        Fret number.
        If floats are passed, they will be floored before computing.
    s
        Scale length.
    """
    n = np.floor(n, dtype=float)

    if not np.all(n > 0):
        raise ValueError("input fret numbers should be positive")

    return s * (1 - 1 / (2**(n / 12)))


def d(N: int, *, L: float, method: str = "et") -> pd.DataFrame:
    """Fret distance DataFrame for `N` frets and scale length `L`."""
    n = np.arange(1, N + 1)

    if method in {"et"}:
        d = d_et(n, s=L)
    else:
        raise ValueError(f"invalid `method` {method!r}")
        
    dd = np.append(d[0], np.diff(d))

    df = pd.DataFrame({"n": n, "d": d, "Δd": dd}).set_index("n")
    desc = {
        "n": "fret number",
        "d": "distance from nut to fret",
        "Δd": "distance from previous fret to current"
    }
    df.attrs.update(col_desc=desc)

    return df


if __name__ == "__main__":
    L = 21
    N = 19
    units = "inches"
    float_format = "%.3f"

    df = d(N, L=L)

    if units.lower() in {"inches", "in", "in.", "\""}:
        su_l = "\""
        su_si = "in"
    elif units.lower() in {"mm"}:
        su_l = su_si = "mm"
    else:
        raise ValueError(f"invalid `units` {units!r}")

    print(f"L = {L}\" (scale length)")
    print(df.to_string(float_format=float_format))
    l = max(len(s) for s in df.attrs["col_desc"])
    for k, v in df.attrs["col_desc"].items():
        print(f"{k:{l+2}}{v}{'' if k == 'n' else f' ({su_si})'}")
