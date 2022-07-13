import pytest

from stringcalc.tension import String, from_ten, ten


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
    assert ten(String.from_spec('14" PL .015')) == pytest.approx(19.6, abs=0.01)
    # TODO: confirm the check # somehow

    # http://chordgen.rattree.co.uk/tensiontool.php gives 12.03
    # for 25.6" A4 with .018p N
    assert ten(String.from_spec('25.5906" N .018')) == pytest.approx(12.03, abs=0.01)


def test_ten_sugg():
    T = 20
    L = 24.75
    pitch = "E4"  # top string in standard guitar tuning

    ret = from_ten(T, L, pitch)
    assert ret.id.tolist() == ["PL011", "PL0115", "PL012"]

    ret = from_ten(T, L, pitch, type="N")
    assert ret.id.tolist() == ["NYL031", "NYL032", "NYL033"]
