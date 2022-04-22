import numpy as np
import pytest

import frets


@pytest.mark.parametrize(
    "n, expected", [
        (12, 0.5),
        (24, 0.75),
        ([12, 24], np.array([0.5, 0.75], dtype=float)),
        (1, 0.05613),
        (5, 0.25085),
    ]
)
def test_d_et_rel(n, expected):
    np.testing.assert_allclose(frets.d_et(n, s=1), expected, rtol=1e-4)
