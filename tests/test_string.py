import itertools

import numpy as np
import pint
import pint.testing
import pytest

import stringcalc
from stringcalc.tension import (
    _DATA_LOADERS,
    _STRING_TYPE_ALIASES,
    String,
    gauge,
    load_aquila_data,
    load_daddario_data,
    load_data,
    load_stringjoy_data,
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
    assert ret.id.tolist() == ["DA:PL011", "DA:PL0115", "DA:PL012"]

    ret = suggest_gauge(T, L, pitch, types={"DA:NYL"})
    assert ret.id.tolist() == ["DA:NYL031", "DA:NYL032", "DA:NYL033"]


def test_suggest_gauge_pb056():
    # GH #7
    T = 23
    L = 25.5
    pitch = "D2"  # dropped D

    ret = suggest_gauge(T, L, pitch, types={"DA:PB"})
    assert ret.id.tolist() == ["DA:PB053", "DA:PB056D", "DA:PB059"]


@pytest.mark.parametrize(
    "pitch",
    ["G1", "G4"],
)
def test_suggest_gauge_bounds_warning(pitch):
    T = 15
    L = 21
    types = {"DA:PB"}

    with pytest.warns(
        UserWarning,
        match=(
            rf"\(T=15, L=21, P={pitch}\) "
            r"is outside the range of what string type group\(s\) \{'DA:PB'\} can provide\."
        ),
    ):
        suggest_gauge(T=T, L=L, pitch=pitch, types=types)


@pytest.mark.parametrize(
    "types",
    [
        {"asdf"},
        {"DA:PB", "asdf"},
    ],
    ids=[
        "all invalid",
        "one invalid",
    ],
)
def test_suggest_gauge_invalid_types(types):
    T = 15
    L = 21
    P = "D3"
    with pytest.raises(ValueError, match=r"string type IDs \['asdf'\] not found in dataset."):
        suggest_gauge(T=T, L=L, pitch=P, types=types)


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


def test_load_data_group_ids_unique():
    dfs = [fn(for_combined=True) for fn in _DATA_LOADERS]
    for a, b in itertools.product(
        [set(df.group_id.cat.categories) for df in dfs],
        repeat=2,
    ):
        if a is b:
            continue
        if a & b:
            raise AssertionError(f"Group IDs {a & b} found in multiple datasets.")


def test_load_data_cat_dtypes():
    df = load_daddario_data(for_combined=False)
    for name in ["category", "group", "id_pref", "id_suff", "group_id"]:
        assert df[name].dtype == "category"

    df = load_data()
    for name in ["group", "group_id"]:
        assert df[name].dtype == "category"


def test_load_data_ids_unique():
    df = load_data()
    id_counts = df["id"].value_counts()
    id_counts_gt1 = id_counts[id_counts > 1]
    assert id_counts_gt1.empty, f"Duplicate IDs found: {sorted(id_counts_gt1.index)}"


def test_stringjoy_data_ids():
    df = load_stringjoy_data(for_combined=True)
    assert df.group_id.str.len().isin((4, 5)).all()
    assert df.group_id.str.startswith("SJ").all()
    assert df.id.str.startswith("SJ").all()
    assert (
        ("." + df.apply(lambda row: row.id[len(row.group_id) :], axis=1)).astype(float) == df.gauge
    ).all()


def test_string_suggest_t_consistency():
    s = String.from_spec('25.5" PB .042')
    P = "A2"
    T = tension(s, pitch=P)
    df = suggest_gauge(T, s.L, P, types={"DA:PB"}, n=1)
    assert df["T"].tolist() == [T]
    assert df.dT.tolist() == [0]


def test_string_suggest_da_conv_warning():
    with pytest.warns(
        UserWarning, match=r"string type groups \['PB', 'PL'\] assumed to be D'Addario"
    ):
        suggest_gauge(20, 25.5, "G3", types={"PB", "PL"})


def test_ureg_setup():
    ureg = stringcalc.ureg
    assert pint.get_application_registry().get() is not ureg
    assert ureg("0.285 lbm / in**3").check("[mass] / [length] ** 3")
    assert f"{ureg('1.3 g/cm^3')}" == "1.3 g/cm³"
    assert f"{ureg('25.5 in')}" == "25.5 in"
    pint.testing.assert_equal(ureg('25.5"'), ureg("25.5 in"))
    pint.testing.assert_equal(ureg("25.5″"), ureg("25.5 in"))
    pint.testing.assert_allclose(ureg("10 lb").to("lbf", "gravity"), ureg("10 lbf"))
    pint.testing.assert_allclose(ureg("10 kg").to("kgf", "gravity"), ureg("10 kgf"))

    other_ureg = pint.UnitRegistry()
    pint.testing.assert_allclose(
        unit_weight(pint.Quantity("19.6 lb"), other_ureg("25.5 in"), "E4"),
        unit_weight("19.6 lbf", '25.5"', "E4"),
    )
    pint.testing.assert_allclose(
        gauge(other_ureg("1.87 g/cm^3"), pint.Quantity("9.3 lbf"), other_ureg("43.2 cm"), "C4"),
        gauge("1.87 g/cm^3", "9.3 lbf", "43.2 cm", "C4"),
    )

    latex_ureg = pint.UnitRegistry()
    latex_ureg.formatter.default_format = "L"
    pint.testing.assert_allclose(
        gauge(latex_ureg("1.87 g/cm^3"), pint.Quantity("9.3 lbf"), latex_ureg("43.2 cm"), "C4"),
        gauge("1.87 g/cm^3", "9.3 lbf", "43.2 cm", "C4"),
    )


def test_ureg_quotes_and_gravity():
    ureg = stringcalc.ureg
    assert ureg.Unit('"') == ureg.Unit("inch")
    assert ureg.Unit("″") == ureg.Unit("inch")
    pint.testing.assert_equal(ureg('0.285 lbm / "^3'), ureg("0.285 lbm / in**3"))

    # Bidirectional gravity context
    pint.testing.assert_allclose(ureg("10 lbf").to("lb", "gravity"), ureg("10 lb"))
    pint.testing.assert_allclose(ureg("10 kgf").to("kg", "gravity"), ureg("10 kg"))
    pint.testing.assert_allclose((ureg("1 kg") * ureg.g0).to("kg", "gravity"), ureg("1 kg"))


def test_ureg_helpers():
    from stringcalc._ureg import _normalize_input, _to_force_quantity, _to_magnitude, ureg

    # _to_force_quantity
    q_n = ureg("10 N")
    assert _to_force_quantity(q_n) is q_n
    pint.testing.assert_allclose(_to_force_quantity(ureg("10 lb")), ureg("10 lbf"))
    pint.testing.assert_allclose(_to_force_quantity(ureg("10 lbm")), ureg("10 lbf"))
    pint.testing.assert_allclose(_to_force_quantity(ureg("8 kg")), ureg("8 kgf"))
    pint.testing.assert_allclose(_to_force_quantity(ureg("500 g")), ureg("500 gf"))
    q_oz = _to_force_quantity(ureg("16 oz"))
    assert q_oz.units == ureg.Unit("ozf")
    pint.testing.assert_allclose(q_oz, ureg("16 ozf"))
    assert _to_force_quantity(ureg("1000 mg")).units == ureg.Unit("lbf")
    with pytest.raises(ValueError, match="Unsupported mass unit"):
        _to_force_quantity(ureg("1000 mg"), strict=True)

    # _normalize_input
    res_num = _normalize_input(25, "[length]")
    assert res_num == 25.0 and isinstance(res_num, float)
    with pytest.raises(pint.DimensionalityError):
        _normalize_input("10 lb", "[force]", allow_mass_as_force=False)
    pint.testing.assert_allclose(
        _normalize_input("10 lb", "[force]", allow_mass_as_force=True),
        ureg("10 lbf"),
    )

    # _to_magnitude
    assert _to_magnitude(12, "inch") == (12.0, None)
    mag_rho, unit_rho = _to_magnitude(1300, "lbm / inch ** 3", default_unit="kg / m ** 3")
    assert unit_rho is None
    assert mag_rho == pytest.approx(ureg("1300 kg/m^3").to("lbm / inch ** 3").magnitude)

    mag_f, unit_f = _to_magnitude("8 kg", "lbf", allow_mass_as_force=True)
    assert unit_f == ureg.Unit("kgf")
    assert mag_f == pytest.approx(ureg("8 kgf").to("lbf").magnitude)


def test_load_aquila_data_pint():
    df_float = load_aquila_data(nng_density=1300)
    df_str = load_aquila_data(nng_density="1.3 g/cm^3")
    df_q = load_aquila_data(nng_density=stringcalc.ureg.Quantity(1300, "kg / m**3"))
    np.testing.assert_allclose(df_str["uw"], df_float["uw"], rtol=1e-12)
    np.testing.assert_allclose(df_q["uw"], df_float["uw"], rtol=1e-12)

    with pytest.raises(pint.DimensionalityError):
        load_aquila_data(nng_density="1.3 g/cm^2")


def test_string_from_spec_metric():
    s_mm = String.from_spec("647.7mm PB .042w")
    s_cm = String.from_spec("64.77 cm PB .042w")
    assert s_mm.L == pytest.approx(25.5)
    assert s_cm.L == pytest.approx(25.5)


def test_tension_pint():
    ureg = stringcalc.ureg
    s_float = String.from_spec('25.5" PB .042')
    s_q = String(L=ureg('25.5"'), type="PB", gauge=ureg("0.042 in"), wound=True)
    s_mm = String(L="647.7 mm", type="PB", gauge="1.0668 mm", wound=True)

    expected = tension(s_float, pitch="A2") * ureg("lbf")
    pint.testing.assert_allclose(tension(s_q, pitch="A2"), expected)
    pint.testing.assert_allclose(tension(s_mm, pitch="A2"), expected)


def test_unit_weight_pint():
    ureg = stringcalc.ureg
    expected = 0.00002680 * ureg("lbm / in")
    pint.testing.assert_allclose(unit_weight("19.6 lbf", '25.5"', "E4"), expected, rtol=0.01)
    pint.testing.assert_allclose(unit_weight("19.6 lb", "647.7 mm", "E4"), expected, rtol=0.01)

    with pytest.raises(pint.DimensionalityError):
        unit_weight("19.6 m", 25.5, "E4")


def test_gauge_pint():
    ureg = stringcalc.ureg
    # Brauchli's Worth tension chart in native metric units
    g = gauge("1.87 g/cm^3", "9.3 lbf", "43.2 cm", "C4")
    pint.testing.assert_allclose(g.to("cm"), 0.074 * ureg("cm"), rtol=0.01)

    g_mass_t = gauge("1.87 g/cm^3", "9.3 lb", "43.2 cm", "C4")
    pint.testing.assert_allclose(g_mass_t, g)

    with pytest.raises(pint.DimensionalityError):
        gauge("1.87 g/cm^2", 9.3, 17.01, "C4")


def test_suggest_gauge_pint():
    df_lbf = suggest_gauge("17 lbf", '23"', "G2", types={"DA:LEW", "DA:LE"})
    assert df_lbf.attrs["units"] == {"T": "lbf", "dT": "lbf"}
    assert "(lbf)" in df_lbf.attrs["col_desc"]["T"]

    df_kg = suggest_gauge("8 kg", "650 mm", "E4")
    assert df_kg.attrs["units"] == {"T": "kgf", "dT": "kgf"}
    assert "(kgf)" in df_kg.attrs["col_desc"]["T"]

    df_kgf = suggest_gauge("8 kgf", "650 mm", "E4")
    np.testing.assert_allclose(df_kg["T"], df_kgf["T"])
    np.testing.assert_allclose(df_kg["dT"], df_kgf["dT"])


def test_cli_pint():
    from typer.testing import CliRunner

    from stringcalc.cli import app

    runner = CliRunner()

    # frets
    res = runner.invoke(app, ["frets", "-L", "25.5 in", "-u", "mm", "-N", "3"])
    assert res.exit_code == 0, res.output
    assert "647.7 mm" in res.output
    assert "(mm)" in res.output

    res_bare = runner.invoke(app, ["frets", "-L", "25.5", "-u", "mm", "-N", "3"])
    assert res_bare.exit_code == 0, res_bare.output
    assert "647.7 mm" in res_bare.output
    assert "(mm)" in res_bare.output

    res_bad = runner.invoke(app, ["frets", "-L", "5 kg"])
    assert res_bad.exit_code == 2
    assert "[mass]" in res_bad.output
    assert "[length]" in res_bad.output

    res_bad_u = runner.invoke(app, ["frets", "-L", "25.5", "-u", "kg"])
    assert res_bad_u.exit_code == 2
    assert "[length]" in res_bad_u.output

    # length
    res = runner.invoke(app, ["length", "0-1=3 cm", "-u", "in", "--round", "2"])
    assert res.exit_code == 0, res.output
    assert res.output.strip() == '21.04"'

    res_full = runner.invoke(app, ["length", "0-1=3 cm", "-u", "in"])
    assert res_full.exit_code == 0, res_full.output
    assert res_full.output.strip().startswith("21.043882")
    assert res_full.output.strip().endswith('"')

    res_bare_full = runner.invoke(app, ["length", "0-1=1.4"])
    assert res_bare_full.exit_code == 0, res_bare_full.output
    assert res_bare_full.output.strip().startswith("24.94401524")

    res_bare_verbose = runner.invoke(app, ["length", "0-1=1.4", "--verbose"])
    assert res_bare_verbose.exit_code == 0, res_bare_verbose.output
    assert "24.944." in res_bare_verbose.output

    res_bad = runner.invoke(app, ["length", "0-1=5 kg"])
    assert res_bad.exit_code == 2

    # gauge --suggest
    res = runner.invoke(app, ["gauge", "--suggest", "-T", "7.5 kg", "-L", "650 mm", "-P", "E4"])
    assert res.exit_code == 0, res.output
    assert "650 mm" in res.output
    assert "kgf" in res.output

    # gauge --suggest fanned with units
    res = runner.invoke(
        app,
        [
            "gauge",
            "--suggest",
            "-T",
            "17",
            "-L",
            "25.5 in",
            "-L",
            "24.75 in",
            "-w",
            "44 mm",
            "-e",
            "3 mm",
            "-P",
            "E2",
            "-P",
            "A2",
        ],
    )
    assert res.exit_code == 0, res.output
    assert "Closest gauges" in res.output

    # gauge exact with --density and --units
    res = runner.invoke(
        app,
        [
            "gauge",
            "-T",
            "9.3 lb",
            "-L",
            "43.2 cm",
            "-P",
            "C4",
            "-d",
            "1.87 g/cm^3",
            "-u",
            "mm",
        ],
    )
    assert res.exit_code == 0, res.output
    assert "0.74" in res.output
    assert "mm" in res.output

    # gauge exact error when both --type and --density provided
    res_bad = runner.invoke(
        app,
        [
            "gauge",
            "-T",
            "15",
            "-L",
            "25.5",
            "-P",
            "E4",
            "--type",
            "PL",
            "-d",
            "0.285",
        ],
    )
    assert res_bad.exit_code == 2

    # gauge --suggest fanned with mixed units and --verbose
    res_fan = runner.invoke(
        app,
        [
            "gauge",
            "--suggest",
            "-T",
            "17",
            "-L",
            "25.5",
            "-L",
            "628 mm",
            "-w",
            "44 mm",
            "-e",
            "3 mm",
            "-P",
            "E2",
            "-P",
            "A2",
            "--verbose",
        ],
    )
    assert res_fan.exit_code == 0, res_fan.output
    assert "44 mm" in res_fan.output
    assert "3 mm" in res_fan.output
    assert "38 mm" in res_fan.output
    assert "mm @ E2" in res_fan.output
    assert "Closest gauges" in res_fan.output

    # CLI rejects non-positive, non-finite, unmapped mass units, and malformed math cleanly
    for args in [
        ["frets", "-L", "inf in"],
        ["frets", "-L", "1/0 in"],
        ["frets", "-L", "(25.5 in"],
        ["frets", "-L", "25.5 ** 10000 in"],
        ["frets", "-L", "25.5", "-u", "1/0 in"],
        ["gauge", "-T", "-5", "-L", "25.5", "-P", "E4", "--type", "PL"],
        ["gauge", "-T", "15", "-L", "0", "-P", "E4", "--type", "PL"],
        ["gauge", "-T", "15", "-L", "25.5", "-P", "E4", "-d", "0"],
        ["gauge", "--suggest", "-T", "17", "-L", "25.5", "-P", "E4", "-u", "mg"],
    ]:
        res_err = runner.invoke(app, args)
        assert res_err.exit_code == 2
        assert isinstance(res_err.exception, SystemExit)

    # Additional CLI unit/output paths: -u oz, -u N, bare length -u, exact --verbose
    res_oz = runner.invoke(
        app, ["gauge", "--suggest", "-T", "17", "-L", "25.5", "-P", "E4", "-u", "oz"]
    )
    assert res_oz.exit_code == 0, res_oz.output
    assert "ozf" in res_oz.output

    res_n = runner.invoke(
        app, ["gauge", "--suggest", "-T", "17", "-L", "25.5", "-P", "E4", "-u", "N"]
    )
    assert res_n.exit_code == 0, res_n.output
    assert "(N)" in res_n.output

    res_len_mm = runner.invoke(app, ["length", "0-1=1.4", "-u", "mm", "--round", "2"])
    assert res_len_mm.exit_code == 0, res_len_mm.output
    assert res_len_mm.output.strip() == "633.58 mm"

    res_exact_type_v = runner.invoke(
        app, ["gauge", "-T", "15", "-L", "25.5", "-P", "E4", "--type", "PL", "--verbose"]
    )
    assert res_exact_type_v.exit_code == 0, res_exact_type_v.output
    assert "plain steel" in res_exact_type_v.output
    assert "15 lbf" in res_exact_type_v.output

    res_exact_dens_v = runner.invoke(
        app,
        [
            "gauge",
            "-T",
            "15",
            "-L",
            "25.5",
            "-P",
            "E4",
            "-d",
            "1.3 g/cm^3",
            "-u",
            "mm",
            "--verbose",
        ],
    )
    assert res_exact_dens_v.exit_code == 0, res_exact_dens_v.output
    assert "1.3 g/cm³" in res_exact_dens_v.output
    assert "mm" in res_exact_dens_v.output


def test_embed_svg_fonts():
    import base64
    import html
    import io
    import re
    import urllib.error

    pytest.importorskip("fontTools")
    from fontTools.ttLib import TTFont
    from rich.console import Console
    from rich.panel import Panel

    from stringcalc.cli import _embed_svg_fonts

    console = Console(record=True, width=40, file=io.StringIO(), legacy_windows=False)
    console.print(Panel("[bold]Δ hi[/] ┃ 0.5 & <x>", title="test"))
    svg = console.export_svg()
    assert svg.count("@font-face") == 2

    try:
        svg_emb = _embed_svg_fonts(svg)
    except urllib.error.URLError as e:
        pytest.skip(f"network unavailable: {e}")

    assert "cdnjs.cloudflare.com" in svg
    assert "cdnjs.cloudflare.com" not in svg_emb
    b64s = re.findall(r'data:font/woff;base64,([^"]+)"', svg_emb)
    assert len(b64s) == 2
    assert "font-weight: 400" in svg_emb and "font-weight: 700" in svg_emb

    chars = set(html.unescape("".join(re.findall(r"<text[^>]*>([^<]*)</text>", svg)))) - {"\n"}
    assert {"╭", "─", "Δ", "&", "<", "\xa0"} <= chars
    for b64 in b64s:
        cmap = TTFont(io.BytesIO(base64.b64decode(b64))).getBestCmap()
        missing = {c for c in chars if ord(c) not in cmap}
        assert not missing


def test_cli_svg_export_no_embed(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    import stringcalc.cli as cli

    p = tmp_path / "out.svg"
    monkeypatch.setattr(cli, "_RICH_EXPORT", str(p))
    monkeypatch.setattr(cli, "_RICH_EXPORT_EMBED_FONT", "0")
    monkeypatch.setattr(cli.console, "record", True)

    res = CliRunner().invoke(cli.app, ["gauge", "--suggest", "-T", "17", "-L", "23", "-P", "D3"])
    assert res.exit_code == 0, res.output
    svg = p.read_text(encoding="utf-8")
    assert "cdnjs.cloudflare.com" in svg
    assert "data:font" not in svg
    assert all(line == line.rstrip() for line in svg.splitlines())
    assert svg.endswith("\n") and not svg.endswith("\n\n")
    cli.console.export_text(clear=True)


def test_cli_svg_export_embed_modes(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    import stringcalc.cli as cli

    p = tmp_path / "out.svg"
    runner = CliRunner()
    args = ["length", "0-1=1.4", "--round", "2"]
    orig_embed = cli._embed_svg_fonts
    monkeypatch.setattr(cli, "_RICH_EXPORT", str(p))
    monkeypatch.setattr(cli.console, "record", True)

    def raise_err(exc):
        def _fail(_svg):
            raise exc

        return _fail

    try:
        # 1. Default (unset): embeds via _embed_svg_fonts
        cli.console.export_text(clear=True)
        monkeypatch.setattr(cli, "_RICH_EXPORT_EMBED_FONT", None)
        monkeypatch.setattr(cli, "_embed_svg_fonts", lambda _svg: "<svg>embedded</svg>")
        res = runner.invoke(cli.app, args)
        assert res.exit_code == 0, res.output
        assert p.read_text(encoding="utf-8") == "<svg>embedded</svg>\n"

        # 2. Default (unset) + ImportError: dim tip and saves fallback SVG cleanly
        cli.console.export_text(clear=True)
        monkeypatch.setattr(cli, "_embed_svg_fonts", raise_err(ImportError("no fonttools")))
        res = runner.invoke(cli.app, args)
        assert res.exit_code == 0, res.output
        assert "Tip: install fonttools" in res.output
        svg = p.read_text(encoding="utf-8")
        assert "cdnjs.cloudflare.com" in svg
        assert "Tip:" not in svg

        # 3. Required (=1) + ImportError: exits 1 without overwriting file
        cli.console.export_text(clear=True)
        p.write_text("keep", encoding="utf-8")
        monkeypatch.setattr(cli, "_RICH_EXPORT_EMBED_FONT", "1")
        res = runner.invoke(cli.app, args)
        assert res.exit_code == 1
        assert "fonttools is required" in res.output
        assert p.read_text(encoding="utf-8") == "keep"

        # 4. Default (unset) + runtime error: warning and saves fallback SVG cleanly
        cli.console.export_text(clear=True)
        monkeypatch.setattr(cli, "_RICH_EXPORT_EMBED_FONT", None)
        monkeypatch.setattr(cli, "_embed_svg_fonts", raise_err(RuntimeError("boom")))
        res = runner.invoke(cli.app, args)
        assert res.exit_code == 0, res.output
        assert "Could not embed font" in res.output
        svg = p.read_text(encoding="utf-8")
        assert "cdnjs.cloudflare.com" in svg
        assert "Could not embed" not in svg

        # 5. Required (=1) + runtime error: exits 1 without overwriting file
        cli.console.export_text(clear=True)
        p.write_text("keep", encoding="utf-8")
        monkeypatch.setattr(cli, "_RICH_EXPORT_EMBED_FONT", "1")
        res = runner.invoke(cli.app, args)
        assert res.exit_code == 1
        assert "Could not embed font" in res.output
        assert p.read_text(encoding="utf-8") == "keep"

        # 6. Zero @font-face rules in SVG raises ValueError
        pytest.importorskip("fontTools")
        with pytest.raises(ValueError, match="no @font-face"):
            orig_embed("<svg><text>hi</text></svg>")
    finally:
        cli.console.export_text(clear=True)


def test_rich_table_alignment_and_highlight():
    import io

    import pandas as pd
    from rich.console import Console

    from stringcalc.cli import _rich_table

    df = suggest_gauge(17, 23, "A3", types={"DA:LEW", "DA:LE"}, n=6)
    c = Console(record=True, width=50, file=io.StringIO(), legacy_windows=False)
    c.print(_rich_table(df, title="test", float_format="%.3f", ihighlight=3))
    assert "│ DA:LE017  │" in c.export_text(clear=False)
    assert ">DA:LE017</text>" in c.export_svg()

    # Right-aligned numeric cells on a highlighted row also keep underline off padding
    df_pos = pd.DataFrame(
        {
            "id": ["A", "B", "C", "D", "E"],
            "T": [15.0, 16.0, 17.018, 18.0, 19.0],
            "dT": [-2.0, -1.0, 0.018, 1.0, 2.0],
        }
    )
    c2 = Console(record=True, width=50, file=io.StringIO(), legacy_windows=False)
    c2.print(_rich_table(df_pos, title="test", float_format="%.3f", ihighlight=2))
    assert ">0.018</text>" in c2.export_svg()


def test_tension_non_positive():
    with pytest.raises(ValueError, match="must be positive"):
        load_aquila_data(nng_density=0)
    with pytest.raises(ValueError, match="must be positive"):
        tension(String(L=-25.5, type="PB", gauge=0.042, wound=True))
    with pytest.raises(ValueError, match="must be positive"):
        tension(String(L=25.5, type="PB", gauge=0, wound=True))
    with pytest.raises(ValueError, match="must be positive"):
        unit_weight(-10, 25.5, "E4")
    with pytest.raises(ValueError, match="must be positive"):
        unit_weight(float("inf"), 25.5, "E4")
    with pytest.raises(ValueError, match="must be positive"):
        unit_weight(10, 0, "E4")
    with pytest.raises(ValueError, match="must be positive"):
        gauge("0 g/cm^3", 10, 25.5, "E4")
    with pytest.raises(ValueError, match="must be positive"):
        gauge("inf g/cm^3", 10, 25.5, "E4")
    with pytest.raises(ValueError, match="must be positive"):
        suggest_gauge(-10, 25.5, "E4")
    with pytest.raises(ValueError, match="must be positive"):
        suggest_gauge(10, 0, "E4")
