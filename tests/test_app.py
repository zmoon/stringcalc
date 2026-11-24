import pytest

from stringcalc._app import (
    get_catalog,
    load_presets,
    run_exact_gauge,
    run_frets,
    run_scale_length,
    run_suggest_gauge,
)
from stringcalc.tension import fanned_scale_lengths, load_data, suggest_gauges


def test_presets_valid_group_ids():
    all_types = set(load_data().group_id.cat.categories)
    presets = load_presets()
    assert len(presets) >= 5
    for p in presets:
        assert p["id"]
        assert p["strings"]
        assert set(p["types"]) <= all_types


def test_get_catalog():
    cat = get_catalog()
    assert cat["version"]
    assert cat["presets"]
    assert len(cat["stringTypes"]) == len(load_data().group_id.cat.categories)
    assert "plain steel" in cat["densities"]


def test_fanned_scale_lengths_and_suggest_gauges():
    Ls = fanned_scale_lengths(27.0, 25.5, 7, nut_width=1.89)
    assert len(Ls) == 7
    assert Ls[0] > Ls[-1]
    assert Ls[0] < 27.0 and Ls[-1] > 25.5

    dfs = suggest_gauges(
        T=17,
        L=23,
        pitch=["G2", "D3", "A3", "E4"],
        types={"DA:LEW", "DA:LE"},
        n=4,
    )
    assert len(dfs) == 4
    assert [df.attrs["pitch"] for df in dfs] == ["G2", "D3", "A3", "E4"]
    assert all(len(df) == 4 for df in dfs)

    dfs_fan = suggest_gauges(
        T="11.5 lbf",
        L=["27 in", "25.5 in"],
        pitch=["B1", "E2", "A2", "D3", "G3", "B3", "E4"],
        types={"DA:NW", "DA:PL"},
        nut_width="1.89 in",
    )
    assert len(dfs_fan) == 7
    assert dfs_fan[0].attrs["L"] > dfs_fan[-1].attrs["L"]

    with pytest.raises(ValueError, match="nut width"):
        suggest_gauges(T=17, L=[27, 25.5], pitch=["E2", "A2"])

    with pytest.raises(ValueError, match="single or same number"):
        suggest_gauges(T=[15, 16], L=25.5, pitch=["E2", "A2", "D3"])


def test_run_suggest_gauge_basic_and_units():
    res = run_suggest_gauge(
        {
            "lengthUnit": "mm",
            "tensionUnit": "kgf",
            "n": 4,
            "types": ["DA:PB", "DA:PL"],
            "strings": [
                {"pitch": "E2", "T": 7.5, "L": 650},
                {"pitch": "E4", "T": 7.5, "L": 650},
            ],
        }
    )
    assert res["error"] is None
    assert res["tensionUnit"] == "kgf"
    assert len(res["strings"]) == 2
    for s in res["strings"]:
        assert s["error"] is None
        assert len(s["suggestions"]) == 4
        assert s["bestIndex"] is not None
        assert s["suggestions"][0]["gauge_in"] is not None
        assert s["suggestions"][0]["gauge_mm"] is not None


def test_run_suggest_gauge_fanned_and_errors():
    res = run_suggest_gauge(
        {
            "lengthUnit": "in",
            "tensionUnit": "lbf",
            "n": 3,
            "types": ["DA:NW", "DA:PL"],
            "fanned": {
                "enabled": True,
                "L_bass": 27.0,
                "L_treble": 25.5,
                "nutWidth": 1.89,
                "edgeBass": 0.15625,
                "edgeTreble": 0.125,
            },
            "strings": [
                {"pitch": "B1", "T": 11.5},
                {"pitch": "E4", "T": 11.5},
            ],
        }
    )
    assert res["error"] is None
    assert res["fannedLengths"] is not None
    assert len(res["fannedLengths"]) == 2
    assert res["fannedLengths"][0] > res["fannedLengths"][1]

    # Invalid pitch on one string does not break the other string
    res_partial = run_suggest_gauge(
        {
            "lengthUnit": "in",
            "tensionUnit": "lbf",
            "n": 3,
            "types": ["DA:PB"],
            "strings": [
                {"pitch": "E2", "T": 16, "L": 25.5},
                {"pitch": "NOTAPITCH", "T": 16, "L": 25.5},
            ],
        }
    )
    assert res_partial["error"] is None
    assert res_partial["strings"][0]["error"] is None
    assert res_partial["strings"][1]["error"] is not None


def test_run_exact_gauge_frets_and_scale_length():
    eg = run_exact_gauge(
        {
            "T": 9.3,
            "tensionUnit": "lbf",
            "L": 432,
            "lengthUnit": "mm",
            "pitch": "C4",
            "material": "custom",
            "customDensity": 1.87,
            "densityUnit": "g/cm^3",
        }
    )
    assert eg["error"] is None
    assert eg["gauge_mm"] == pytest.approx(0.74, rel=0.02)

    fr = run_frets({"N": 12, "L": 25.5, "lengthUnit": "in"})
    assert fr["error"] is None
    assert len(fr["rows"]) == 12
    assert fr["rows"][-1]["d"] == pytest.approx(12.75, rel=1e-4)

    sl = run_scale_length({"a": "nut", "b": "1", "d": 3, "lengthUnit": "cm"})
    assert sl["error"] is None
    assert sl["L_in"] == pytest.approx(21.04, rel=1e-3)

    sl_err = run_scale_length({"a": "5", "b": "5", "d": 1.0, "lengthUnit": "in"})
    assert sl_err["error"] is not None
