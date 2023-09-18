import itertools

import pytest

from stringcalc.tension import (
    _DATA_LOADERS,
    _STRING_TYPE_ALIASES,
    String,
    gauge,
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
    "types",
    [
        {"asdf"},
        {"PB", "asdf"},
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
    dfs = [fn() for fn in _DATA_LOADERS]
    for a, b in itertools.product(
        [set(df.group_id.cat.categories) for df in dfs],
        repeat=2,
    ):
        if a is b:
            continue
        if a & b:
            raise AssertionError(f"Group IDs {a & b} found in multiple datasets.")


def test_load_data_cat_dtypes():
    df = load_data()

    for name in ["category", "group", "id_pref", "id_suff", "group_id"]:
        assert df[name].dtype == "category"


def test_load_data_ids_unique():
    df = load_data()
    id_counts = df["id"].value_counts()
    id_counts_gt1 = id_counts[id_counts > 1]
    assert id_counts_gt1.empty, f"Duplicate IDs found: {sorted(id_counts_gt1.index)}"


def test_stringjoy_data_ids():
    df = load_stringjoy_data()
    assert df.group_id.str.len().isin((3, 4)).all()
    assert df.group_id.str.startswith("SJ").all()
    assert df.id.str.startswith("SJ").all()
    assert (
        ("." + df.apply(lambda row: row.id[len(row.group_id) :], axis=1)).astype(float) == df.gauge
    ).all()


def test_string_suggest_t_consistency():
    s = String.from_spec('25.5" PB .042')
    P = "A2"
    T = tension(s, pitch=P)
    df = suggest_gauge(T, s.L, P, types={"PB"}, n=1)
    assert df["T"].tolist() == [T]
    assert df.dT.tolist() == [0]
