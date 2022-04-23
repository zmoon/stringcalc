import pytest

from tension import String


@pytest.mark.parametrize(
    "g",
    [
        "042",
        ".042",
        "0.042",
        "0.0420",
    ]
)
def test_parse_gauge(g):
    s = String.from_spec(f"22.9\" PB {g}")
    assert s.gauge == 0.042


@pytest.mark.parametrize(
    "s",
    [
        "22.9\" PB 042",
        "22.9\" PB 042w",
        "22.9\" PB .042",
    ]
)
def test_str(s):
    s = String.from_spec(s)
    assert str(s) == "22.9\" PB .042"
