"""
Fret distances
"""
from __future__ import annotations

import numpy as np
import numpy.typing as npt  # v1.21 needed


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
