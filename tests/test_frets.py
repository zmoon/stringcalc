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
    np.testing.assert_allclose(frets.distance_et(n, L=1), expected, rtol=1e-4)


def test_ds_et_rel():
    ret = frets.distances(N=24, L=1)
    assert ret.loc[12].d == 0.5
    assert ret.loc[24].d == 0.75


def test_ds_invalid():
    with pytest.raises(ValueError, match=r"invalid `method` 'asdf'"):
        frets.distances(N=17, L=21, method="asdf")


@pytest.mark.parametrize(
    "n",
    [
        -1,
        -0.1,
        [-2, -1],
        [-1, 0, 1],
    ],
)
def test_d_et_invalid(n):
    with pytest.raises(ValueError, match="input fret numbers should be positive"):
        frets.distance_et(n=n, L=25)


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
    assert frets.length_from_distance(ab, d) == pytest.approx(expected, abs=5e-4)


def test_l_from_d_pint():
    # Seems not to work with `pytest.approx`
    ret = frets.length_from_distance(ab=(1, 0), d="1in")
    expected = 17.817 * frets.ureg["in"]
    delta = 5e-4 * frets.ureg["in"]
    assert expected - delta <= ret <= expected + delta


def test_l_from_d_invalid_ab():
    with pytest.raises(ValueError, match="must be different"):
        frets.length_from_distance((0, 0), 10)


def test_l_from_d_invalid_d():
    with pytest.raises(ValueError, match="must be positive"):
        frets.length_from_distance((0, 1), -10)


def test_main():
    import runpy
    import warnings

    mod_name = "stringcalc.frets"
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=RuntimeWarning,
            message=rf"{mod_name!r} found in sys\.modules after import of package",
        )

        runpy.run_module(mod_name, run_name="__main__")
