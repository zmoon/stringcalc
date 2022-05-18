import numpy as np
import pytest

from stringcalc import frets


@pytest.mark.parametrize(
    "n, expected",
    [
        (12, 0.5),
        (24, 0.75),
        ([12, 24], np.array([0.5, 0.75], dtype=float)),
        (1, 0.05613),
        (5, 0.25085),
    ],
)
def test_d_et_rel(n, expected):
    np.testing.assert_allclose(frets.d_et(n, s=1), expected, rtol=1e-4)


@pytest.mark.parametrize(
    "ab, d, expected",
    [
        ((0, 2), 2, 18.332),
        ((2, None), 16.3316, 18.332),
        ((2, None), 21, 23.572),
        ((0, 1), 1, 17.817),
        ((1, 0), 1, 17.817),
    ],
)
def test_l_from_d(ab, d, expected):
    assert frets.l_from_d(ab, d) == pytest.approx(expected, abs=5e-4)


def test_l_from_d_invalid_ab():
    with pytest.raises(ValueError, match="must be different"):
        frets.l_from_d((0, 0), 10)


def test_l_from_d_invalid_d():
    with pytest.raises(ValueError, match="must be positive"):
        frets.l_from_d((0, 1), -10)
