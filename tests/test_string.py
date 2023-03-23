import itertools

import pytest

from stringcalc.tension import (
    _STRING_TYPE_ALIASES,
    String,
    gauge,
    suggest_gauge,
    tension,
    unit_weight,
)


@pytest.mark.parametrize(
    "g",
    [
        "042",
        ".042",
        "0.042",
        "0.0420",
    ],
)
def test_parse_gauge(g):
    s = String.from_spec(f'22.9" PB {g}')
    assert s.gauge == 0.042


@pytest.mark.parametrize(
    "s",
    [
        '22.9" PB 042',
        '22.9" PB 042w',
        '22.9" PB .042',
    ],
)
def test_str(s):
    s = String.from_spec(s)
    assert str(s) == '22.9" PB .042'


def test_string_ten():
    assert tension(String.from_spec('14" PL .015')) == pytest.approx(19.6, abs=0.01)
    # TODO: confirm the check # somehow

    # http://chordgen.rattree.co.uk/tensiontool.php gives 12.03
    # for 25.6" A4 with .018p N
    assert tension(String.from_spec('25.5906" N .018')) == pytest.approx(12.03, abs=0.01)


def test_suggest_gauge():
    T = 20
    L = 24.75
    pitch = "E4"  # top string in standard guitar tuning

    ret = suggest_gauge(T, L, pitch)
    assert ret.id.tolist() == ["PL011", "PL0115", "PL012"]

    ret = suggest_gauge(T, L, pitch, types={"NYL"})
    assert ret.id.tolist() == ["NYL031", "NYL032", "NYL033"]


def test_suggest_gauge_pb056():
    # GH #7
    T = 23
    L = 25.5
    pitch = "D2"  # dropped D

    ret = suggest_gauge(T, L, pitch, types={"PB"})
    assert ret.id.tolist() == ["PB053", "PB056D", "PB059"]


@pytest.mark.parametrize(
    "pitch",
    ["G1", "G4"],
)
def test_suggest_gauge_bounds_warning(pitch):
    T = 15
    L = 21
    types = {"PB"}

    with pytest.warns(
        UserWarning,
        match=r"You are outside the range of what string type group\(s\) \{'PB'\} can provide\.",
    ):
        suggest_gauge(T=T, L=L, pitch=pitch, types=types)


@pytest.mark.parametrize(
    "T,pitch,expected",
    [
        (19.6, "E4", 0.00002680),  # PL011
        (15.6, "D4", 0.00002680),  # PL011
        (27.1, "D3", 0.00018660),  # PB030
    ],
)
def test_uw_calc(T, pitch, expected):
    # Data from the D'Addario chart
    assert unit_weight(T, 25.5, pitch) == pytest.approx(expected, rel=0.01)


def test_gauge_calc():
    # From Brauchli's Worth tension chart
    rho = 0.06756  # 1.87 g/cm3 -> lb/in3
    ten = 9.3  # lbf
    len_ = 17.01  # 43.2 cm -> in
    d_exp = 0.0291  # 0.074 cm -> in
    assert gauge(rho, ten, len_, "C4") == pytest.approx(d_exp, rel=0.01)


def test_aliases_unique():
    all_aliases = list(
        itertools.chain.from_iterable(aliases for aliases in _STRING_TYPE_ALIASES.values())
    )
    verbose_keys = _STRING_TYPE_ALIASES.keys()
    all_aliases_set = set(all_aliases)
    assert len(all_aliases) == len(all_aliases_set)
    assert len(all_aliases + list(verbose_keys)) == len(all_aliases_set | verbose_keys)
