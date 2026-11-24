import pytest

anywidget = pytest.importorskip("anywidget")

from stringcalc.widget import (  # noqa: E402
    _BUNDLE_PATH,
    ExactGaugeWidget,
    FretsWidget,
    GaugeSuggestWidget,
    ScaleLengthWidget,
)


def _bundle_kwargs() -> dict[str, str]:
    """Allow testing widget Python logic even when _bundle.js has not been built."""
    if _BUNDLE_PATH.exists():
        return {}
    return {"_esm": "export default { render() {} }"}


def test_gauge_suggest_widget(monkeypatch):
    w = GaugeSuggestWidget(preset="tenor-banjo-4-irish", **_bundle_kwargs())
    assert w.preset == "tenor-banjo-4-irish"
    assert len(w.strings) == 4
    assert w.results["error"] is None
    dfs = w.to_dataframes()
    assert len(dfs) == 4
    assert [df.attrs["pitch"] for df in dfs] == ["G2", "D3", "A3", "E4"]

    # Mutating w.L propagates to all strings and recomputes
    w.L = 21.0
    assert all(s["L"] == 21.0 for s in w.strings)
    assert all(df.attrs["L"] == 21.0 for df in w.to_dataframes())

    # Mutating a trait recomputes results automatically
    w.n = 2
    assert all(len(df) == 2 for df in w.to_dataframes())

    # Batch frontend sync via set_state triggers exactly one recompute
    calls = 0
    orig_recompute = w._recompute

    def counted_recompute():
        nonlocal calls
        calls += 1
        orig_recompute()

    monkeypatch.setattr(w, "_recompute", counted_recompute)
    w.set_state({"n": 3, "L": 22.0, "tension_unit": "kgf"})
    assert calls == 1

    # Metric preset seeds fanned defaults in mm, not inches
    w.apply_preset("guitar-6-classical")
    assert w.length_unit == "mm"
    assert w.fanned["L_bass"] > 600
    assert len(w.to_dataframes()) == 6

    # Assigning w.preset directly also loads preset fields and recomputes
    w.preset = "guitar-6"
    assert w.length_unit == "in"
    assert w.L == 25.5
    assert [df.attrs["pitch"] for df in w.to_dataframes()] == ["E2", "A2", "D3", "G3", "B3", "E4"]


def test_misc_widgets():
    eg = ExactGaugeWidget(T=16, L=22.5, pitch="D3", **_bundle_kwargs())
    assert eg.result["error"] is None
    assert eg.result["gauge_in"] > 0

    eg.material = "custom"
    eg.custom_density = 1.87
    assert eg.result["error"] is None
    assert eg.result["gauge_mm"] > 0

    fr = FretsWidget(N=12, L=25.5, **_bundle_kwargs())
    assert fr.result["error"] is None
    df = fr.to_dataframe()
    assert len(df) == 12
    assert df.loc[12, "d"] == pytest.approx(12.75, rel=1e-4)

    sl = ScaleLengthWidget(a="nut", b="12", d=12.75, **_bundle_kwargs())
    assert sl.result["error"] is None
    assert sl.result["L_in"] == pytest.approx(25.5, rel=1e-4)

    sl.b = "nut"
    assert sl.result["error"] is not None
