"""
CLI
"""

from __future__ import annotations

import functools
import os
import re
import tokenize
from pathlib import Path
from typing import NoReturn

from pint import PintError, Quantity

from ._ureg import _normalize_input, _to_force_quantity, _UnitType, ureg

try:
    import typer
    from rich.console import Console, RenderableType
    from rich.style import Style
except ImportError as e:
    print("The stringcalc CLI requires typer and rich (included with the 'cli' extra).")
    print(f"Error was: {e!r}")
    raise SystemExit(1)

_RICH_EXPORT: str = os.environ.get("STRINGCALC_RICH_EXPORT", "0")
_RICH_EXPORT_EMBED_FONT: str | None = os.environ.get("STRINGCALC_RICH_EXPORT_EMBED_FONT")

HERE = Path(__file__).parent
_TRAN_SUPE_DIGIT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

console = Console(
    record=_RICH_EXPORT != "0",
    # Legacy Windows mode (e.g. when output is piped on Windows) would use "safe" boxes
    # and reduce the width by one, which we don't want for the SVG export
    legacy_windows=False if _RICH_EXPORT != "0" else None,
)

app = typer.Typer(add_completion=False, name="stringcalc")


def _to_fancy_sci(s: str) -> str:
    a, b0 = s.split("e")
    b = str(int(b0)).replace("-", "⁻").translate(_TRAN_SUPE_DIGIT)

    return f"{a}×10{b}"


def _embed_svg_fonts(svg: str) -> str:
    """Replace the SVG's remote ``@font-face`` rules with inline WOFF data URIs,
    subset to the characters used, so that the SVG renders the same everywhere,
    including in ``<img>`` contexts (e.g. GitHub, PyPI) where remote fonts are blocked.

    The font URLs are taken from the ``@font-face`` rules in the SVG (from Rich's template).
    Raises ``ImportError`` if fontTools is not installed.
    """
    import base64
    import html
    import io
    import urllib.request

    from fontTools.subset import Options, Subsetter
    from fontTools.ttLib import TTFont

    text = html.unescape("".join(re.findall(r"<text[^>]*>([^<]*)</text>", svg)))

    def repl(m: re.Match) -> str:
        block = m.group(0)
        family = re.search(r'font-family:\s*"([^"]+)"', block)
        weight = re.search(r"font-weight:\s*(\d+)", block)
        url = re.search(r'url\("(https://[^"]+\.woff)"\)', block)
        if family is None or weight is None or url is None:
            raise ValueError(f"unexpected @font-face rule: {block!r}")

        with urllib.request.urlopen(url.group(1), timeout=10) as r:
            font = TTFont(io.BytesIO(r.read()), recalcTimestamp=False)
        subsetter = Subsetter(Options(flavor="woff"))
        subsetter.populate(text=text)
        subsetter.subset(font)
        buf = io.BytesIO()
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")

        return (
            "@font-face {\n"
            f'        font-family: "{family.group(1)}";\n'
            f'        src: url("data:font/woff;base64,{b64}") format("woff");\n'
            "        font-style: normal;\n"
            f"        font-weight: {weight.group(1)};\n"
            "    }"
        )

    svg, n = re.subn(r"@font-face\s*\{[^}]*\}", repl, svg)
    if n == 0:
        raise ValueError("no @font-face rules found in SVG")
    return svg


def _maybe_export_output(cmd):
    """Export CLI command's Rich output to SVG,
    dependent on the value of the ``STRINGCALC_RICH_EXPORT`` environment variable.

    - ``0`` or unset: Do not export.
    - ``1``: Export to ``stringcalc-rich-export.svg``.
    - Any other value: Export to ``<value>.svg``
      (or just ``value`` if it already ends in ``.svg``).

    By default, if fontTools is installed, the font (subset to the characters used)
    is embedded in the SVG, so that it renders correctly where remote fonts are blocked
    (e.g. GitHub and PyPI READMEs).
    This is controlled by the ``STRINGCALC_RICH_EXPORT_EMBED_FONT`` environment variable.

    - Unset: Embed if fontTools is installed.
    - ``1``: Embed, erroring if not possible.
    - ``0``: Do not embed.
    """

    @functools.wraps(cmd)
    def inner(*args, **kwargs):
        ret = cmd(*args, **kwargs)

        p: Path | None  # type: ignore[annotation-unchecked]
        if _RICH_EXPORT == "1":
            p = Path("stringcalc-rich-export.svg")
        elif _RICH_EXPORT == "0":
            p = None
        else:
            p = Path(_RICH_EXPORT).with_suffix(".svg")

        if p is not None:
            svg = console.export_svg(title="stringcalc")
            if _RICH_EXPORT_EMBED_FONT != "0":
                try:
                    svg = _embed_svg_fonts(svg)
                except ImportError:
                    if _RICH_EXPORT_EMBED_FONT == "1":
                        error("fonttools is required to embed the font in the SVG export.")
                    else:
                        console.print(
                            "Tip: install fonttools to embed the font in the SVG export,"
                            " so that box lines connect when shown on GitHub/PyPI.",
                            style="dim",
                            highlight=False,
                        )
                except Exception as e:
                    if _RICH_EXPORT_EMBED_FONT == "1":
                        error(f"Could not embed font in SVG export ({e!r}).")
                    else:
                        warning(f"Could not embed font in SVG export ({e!r}); saving without it.")
            svg = "\n".join(line.rstrip() for line in svg.rstrip().splitlines()) + "\n"
            p.write_text(svg, encoding="utf-8")

        return ret

    return inner


def error(s: str, *, rc: int = 1, markup: bool = False) -> NoReturn:
    """Print error message."""
    console.print(s, style=Style(color="red", bold=True), highlight=False, markup=markup)
    assert rc != 0
    raise typer.Exit(rc)


def info(s: str) -> None:
    """Print info message."""
    console.print(s, style=Style(color="cyan", bold=True), highlight=False)


def warning(s: str) -> None:
    """Print warning message."""
    console.print(s, style=Style(color="red", bold=False), highlight=False)


def pretty_warnings(f):
    """Decorator to catch warnings and pretty-print them with Rich after running `f`."""
    import warnings

    @functools.wraps(f)
    def inner(*args, **kwargs):
        with warnings.catch_warnings(record=True) as w:
            f(*args, **kwargs)

            for i in range(len(w)):
                warning(f"- {w[i].message}")

    return inner


def _version_callback(show: bool):
    if show:
        from . import __version__

        v = f"[rgb(184,115,51)]stringcalc[/] [bold blue]{__version__}[/]"
        try:
            i = v.index("+")
        except ValueError:
            pass
        else:
            v = v[:i] + "[rgb(100,100,100)]" + v[i:] + "[/]"

        console.print(v, highlight=False)

        raise typer.Exit(0)


@app.callback()
def main(  # noqa: E704
    version: bool = typer.Option(
        False,
        "--version/",
        help="Print version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
): ...


def _with_float_nonext_dtypes(df):
    """Convert float extension dtypes (e.g. 'Float64') to standard NumPy float64."""
    import numpy as np
    import pandas as pd

    df = df.copy()

    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_float_dtype(dtype) and pd.api.types.is_extension_array_dtype(dtype):
            df[col] = df[col].astype(np.float64)

    return df


def _rich_table(
    df,
    *,
    title: str,
    float_format: str,
    panel: bool = False,
    column_info: bool = True,
    ihighlight: int | None = None,
) -> RenderableType:
    import pandas as pd
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    attrs = df.attrs.copy()
    df_str = _with_float_nonext_dtypes(df).to_string(
        float_format=float_format,
        header=False,
        index=False,
    )
    # NOTE: `.to_string` with `float_format` doesn't seem to work for the float extension dtypes

    if "e" in df_str and console.is_terminal:
        df_str = re.sub(r"\S*e[+-][0-9]*", lambda m: _to_fancy_sci(m.group()), df_str)

    def maybe_fancy_col_name(col: str) -> str:
        fancy_col: str | None
        try:
            fancy_col = attrs["fancy_col"][col]
        except KeyError:
            fancy_col = None

        if fancy_col is None or not console.is_terminal:
            return col
        else:
            return fancy_col

    # Table itself
    table = Table(title=title)
    hl_style = "bold"
    if len(df) >= 5:
        hl_style += " underline overline"
    for col in df.columns:
        table.add_column(
            maybe_fancy_col_name(col),
            style="green" if col != "n" else None,
            justify="right" if pd.api.types.is_numeric_dtype(df[col]) else "left",
        )
    for i, row in enumerate(df_str.splitlines()):
        cells = row.split()
        if i == ihighlight:
            table.add_row(*[Text.assemble((c, hl_style)) for c in cells])
        else:
            table.add_row(*cells)

    # Column descriptions
    r: RenderableType
    if "col_desc" not in attrs or not column_info:
        r = table
    else:
        l = max(len(str(c.header)) for c in table.columns)  # noqa: E741
        sub_lines = []
        for col in df.columns:
            v = attrs["col_desc"].get(col)
            if v is None:
                continue
            sub_lines.append(f"[bold cyan]{maybe_fancy_col_name(col):{l+2}}[/]{v}")

        r = Group(table, "\n".join(sub_lines))

    return Panel(r, expand=False) if panel else r


def pprint_table(df, *, title: str, float_format: str, panel=False) -> None:
    """Pretty-print a pandas DataFrame as a Rich table."""
    console.print(_rich_table(df, title=title, float_format=float_format, panel=panel))


def _cli_val(s: str, *, dim: str, allow_mass_as_force: bool = False) -> float | Quantity:
    """Parse a CLI option string as float or validated Quantity, exiting with code 2 on error."""
    s_stripped = s.strip()
    try:
        return float(s_stripped)
    except ValueError:
        pass

    try:
        q: Quantity = ureg.Quantity(s_stripped)
        if q.unitless:
            return float(q.magnitude)

        norm = _normalize_input(q, dim, allow_mass_as_force=allow_mass_as_force)
        assert isinstance(norm, Quantity)
        return norm
    except (PintError, ValueError, ArithmeticError, tokenize.TokenError) as e:
        error(f"Invalid value {s!r}. Message: {e}", rc=2)


def _cli_unit(u: str, *, dim: str, allow_mass_as_force: bool = False) -> _UnitType:
    """Parse a CLI unit string and validate its dimensionality."""
    try:
        unit: _UnitType = ureg.Unit(u)
    except (PintError, ValueError, ArithmeticError, tokenize.TokenError) as e:
        error(f"Invalid unit {u!r}. Message: {e}", rc=2)

    q = ureg.Quantity(1.0, unit)
    if allow_mass_as_force and q.check("[mass]"):
        try:
            q = _to_force_quantity(q, strict=True)
        except ValueError as e:
            error(str(e), rc=2)
        unit = q.units

    if not q.check(dim):
        error(f"Unit {u!r} does not have expected dimensionality {dim}.", rc=2)

    return unit


def _to_cli_unit(val: float | Quantity, target_u: _UnitType, *, default_unit: str) -> Quantity:
    """Convert a float (assumed in ``default_unit``) or Quantity to ``target_u``."""
    q = val if isinstance(val, Quantity) else ureg.Quantity(val, default_unit)
    return q.to(target_u, "gravity")


def _fmt_val(v: float | Quantity, default_unit_suffix: str = "", *, fmt: str = "g") -> str:
    """Format a float or Quantity compactly for CLI titles and messages."""
    if isinstance(v, Quantity):
        mag = format(float(v.magnitude), fmt)
        if v.units == ureg.Unit("inch"):
            return f'{mag}"'
        return f"{mag} {v.units}"
    return f"{format(v, fmt)}{default_unit_suffix}"


@app.command()
@_maybe_export_output
def frets(
    N: int = typer.Option(
        17, "-N", "--number", help="Number of frets, starting from nut (fret 0)."
    ),
    L: str = typer.Option(
        ...,
        "-L",
        "--scale-length",
        help="Scale length (e.g. '25.5', '25.5\"', '650 mm').",
    ),
    units: str | None = typer.Option(
        None,
        "-u",
        "--units",
        help="Output length units (e.g. 'in', 'mm').",
    ),
    float_format: str = typer.Option(r"%.3f", help="Format for float-to-string conversion."),
    # TODO: `method`
    # TODO: `format` (rich, CSV, etc.)
):
    """Display fret distance table for `N` frets and scale length `L`.

    Unitless `L` values default to inches when --units is specified.
    """
    from .frets import distances

    L_val = _cli_val(L, dim="[length]")
    if units is not None:
        target_u = _cli_unit(units, dim="[length]")
        L_val = _to_cli_unit(L_val, target_u, default_unit="inch")

    try:
        df = distances(N=N, L=L_val).reset_index()
    except ValueError as e:
        error(f"Failed to compute fret distances. Message: {e}", rc=2)

    L_title = _fmt_val(L_val)
    pprint_table(df, title=f"Fret distances for L={L_title}", float_format=float_format)


_RE_LENGTH_SPEC = re.compile(r"(?P<a>[0-9]+|[ns])-(?P<b>[0-9]+|[ns])=(?P<d>.+)")


def _ab_interp(s: str) -> int | None:
    if s == "s":
        return None
    elif s == "n":
        return 0
    else:
        return int(s)


def _ab_name(n: int | None) -> str:
    if n == 0:
        return "nut"
    elif n is None:
        return "saddle"
    else:
        return f"fret {n}"


@app.command()
@_maybe_export_output
def length(
    spec: str = typer.Argument(...),
    units: str | None = typer.Option(
        None,
        "-u",
        "--units",
        help="Output length units (e.g. 'in', 'mm').",
    ),
    round_: int | None = typer.Option(
        None, "--round", help="Round result to this decimal precision."
    ),
    verbose: bool = typer.Option(False),
):
    """Calculate the scale length implied by spec 'a-b=d'.

    Where `a` and `b` are fret numbers
    (use '0' or 'n' for nut, 's' for saddle)
    and `d` is the corresponding distance (optionally with units, e.g. '0-1=3 cm').
    Unitless `d` values default to inches when --units is specified.
    """
    from .frets import length_from_distance

    m = _RE_LENGTH_SPEC.fullmatch(spec)
    if m is None:
        error(
            f"Input failed to match a-b=d spec format regex {_RE_LENGTH_SPEC.pattern!r}",
            rc=2,
        )

    dct = m.groupdict()
    try:
        a = _ab_interp(dct["a"])
        b = _ab_interp(dct["b"])
    except ValueError as e:
        error(f"Failed to convert input to frets. Message: {e}", rc=2)

    d = _cli_val(dct["d"], dim="[length]")

    try:
        res = length_from_distance((a, b), d)
    except ValueError as e:
        error(f"Failed to compute scale length. Message: {e}", rc=2)

    if units is not None:
        target_u = _cli_unit(units, dim="[length]")
        res = _to_cli_unit(res, target_u, default_unit="inch")

    if round_ is not None:
        if isinstance(res, Quantity):
            res = ureg.Quantity(round(float(res.magnitude), round_), res.units)
        else:
            res = round(res, round_)

    d_str = _fmt_val(d)
    res_str = _fmt_val(res, fmt="" if (not verbose or round_ is not None) else "g")

    if verbose:
        a_name = _ab_name(a)
        b_name = _ab_name(b)
        console.print(
            f"A distance from [green]{a_name}[/] to [red]{b_name}[/] "
            f"of [cyan]{d_str}[/] implies a scale length of [bold cyan underline]{res_str}[/].",
            highlight=False,
        )
    else:
        console.print(res_str)


def _fanned_lengths(
    L_vals: list[float | Quantity],
    *,
    n_str: int,
    nut_width: str | None,
    edge_space: list[str] | None,
    verbose: bool,
) -> list[float | Quantity]:
    """Compute per-string scale lengths for fanned-fret calculations."""
    from .tension import _fanned_geometry, _from_inch

    if len(L_vals) != 2:
        error(
            "Must supply two scale lengths (bass and treble sides) for fanned calculation. "
            f"Got {len(L_vals)}.",
            rc=2,
        )
    if not nut_width:
        error("Must supply nut width for fanned calculation.", rc=2)

    nw_val = _cli_val(nut_width, dim="[length]")
    es_vals = [_cli_val(e, dim="[length]") for e in edge_space] if edge_space is not None else None

    try:
        geom = _fanned_geometry(
            L_vals[0],
            L_vals[1],
            n_str,
            nut_width=nw_val,
            edge_space=es_vals,
        )
    except ValueError as e:
        error(str(e), rc=2)

    if verbose:
        disp_u = geom.nut_width_unit or ureg.Unit("inch")

        def _fmt_fan(val_in: float) -> str:
            return _fmt_val(ureg.Quantity(_from_inch(val_in, disp_u), disp_u))

        xs_disp = [_from_inch(x, disp_u) for x in geom.positions_in]
        xs_u = f"{disp_u}" if disp_u != ureg.Unit("inch") else '"'
        info(f"Nut width:               {_fmt_fan(geom.nut_width_in)}")
        info(f"Left/bass edge space:    {_fmt_fan(geom.edge_bass_in)}")
        info(f"Right/treble edge space: {_fmt_fan(geom.edge_treble_in)}")
        info(f"Computed string spacing: {_fmt_fan(geom.spacing_in)}")
        info(f"Computed string nut positions ({xs_u}): {xs_disp}")

    return geom.lengths


@app.command(name="gauge")
@pretty_warnings
@_maybe_export_output
def gauge_(
    T: list[str] = typer.Option(
        ...,
        "-T",
        "--tension",
        help="Desired tension (e.g. '17', '17 lbf', '7.5 kg', '75 N').",
    ),
    L: list[str] = typer.Option(
        ...,
        "-L",
        "--length",
        help="String length / scale length (e.g. '25.5', '25.5\"', '650 mm').",
    ),
    P: list[str] = typer.Option(
        ..., "-P", "--pitch", help="Pitch in scientific pitch notation (e.g. 'E4')."
    ),
    suggest: bool = typer.Option(
        False,
        help=("If true, suggest gauges (strings) to use. If false, compute exact gauge."),
    ),
    types: list[str] | None = typer.Option(
        None,
        "--type",
        help=(
            "String type. Can specify multiple times if using --suggest. "
            "For --suggest, defaults to D'Addario phosphor bronze and plain steel ('DA:PB', 'DA:PL'). "
            "If not using --suggest, specify one type or --density."
        ),
    ),
    density: str | None = typer.Option(
        None,
        "-d",
        "--density",
        help=(
            "Material density for exact gauge calculation "
            "(e.g. '1300 kg/m^3', '1.14 g/cm^3', or float in lbm/in^3)."
        ),
    ),
    units: str | None = typer.Option(
        None,
        "-u",
        "--units",
        help="Output units (tension units for --suggest, length units for exact gauge).",
    ),
    nsuggest: int = typer.Option(
        3, "-N", "--nsuggest", help="Number of suggestions. Only relevant if using --suggest."
    ),
    is_fan: bool | None = typer.Option(
        None,
        "--fanned",
        help=(
            "Fanned calculations. Must provide two scale lengths. "
            "Assumed if two scale lengths are provided."
        ),
    ),
    nut_width: str | None = typer.Option(
        None,
        "-w",
        "--nut-width",
        help=(
            "Neck width at (center of?) nut (for fanned calculations, e.g. '1.75', '44.5 mm'). "
            "Required if using --fanned."
        ),
    ),
    edge_space: list[str] | None = typer.Option(
        None,
        "-e",
        "--edge-space",
        help=(
            "Edge space, between the edge of the neck and the center of the first string. "
            "You can specify one (used for both left and right) or two (left, right). "
            'The default is 5/32" on the left and 1/8" on the right. '
            "Only used for fanned calculations."
        ),
    ),
    float_format: str = typer.Option(
        r"%.3f", help="Format for float-to-string conversion. Only relevant if using --suggest."
    ),
    column_info: bool = typer.Option(
        True,
        help="Print column definitions under table. Only relevant if using --suggest.",
    ),
    verbose: bool = typer.Option(False),
):
    """Compute gauge(s) from string information.

    Unitless values for `T`, `L`, `nut_width`, `edge_space`, and `density`
    default to lbf, inches, and lbm/in^3; Pint unit strings (e.g. '650 mm',
    '75 N', '7.5 kg', '1.3 g/cm^3') are also supported.
    """
    from .tension import _STRING_TYPE_ALIAS_TO_VERBOSE, DENSITY_LB_IN, gauge, suggest_gauges

    T_vals: list[float | Quantity] = [
        _cli_val(t, dim="[force]", allow_mass_as_force=True) for t in T
    ]
    L_vals: list[float | Quantity] = [_cli_val(l_, dim="[length]") for l_ in L]

    if suggest:
        from rich.columns import Columns

        if units is not None:
            target_t_u = _cli_unit(units, dim="[force]", allow_mass_as_force=True)
            T_vals = [_to_cli_unit(t, target_t_u, default_unit="lbf") for t in T_vals]

        types_set: set[str]
        if not types:
            if verbose:
                info("No string types specified, defaulting to D'Addario PB + PL.")
            types_set = {"DA:PB", "DA:PL"}
        else:
            types_set = set(types)

        if is_fan is None:
            is_fan = len(L_vals) == 2
        if is_fan:
            L_vals = _fanned_lengths(
                L_vals,
                n_str=max(len(T_vals), len(P)),
                nut_width=nut_width,
                edge_space=edge_space,
                verbose=verbose,
            )

        if verbose:
            info(f"Searching string types: {types_set}")

        try:
            g_dfs = suggest_gauges(
                T=T_vals,
                L=L_vals,
                pitch=P,
                types=types_set,
                n=nsuggest,
                fanned=False,
            )
        except ValueError as e:
            error(f"Failed to compute gauge suggestions. Message: {e}", rc=2)

        n_cases = len(g_dfs)
        tables = []
        for g_df in g_dfs:
            T_ = g_df.attrs["T"]
            L_ = g_df.attrs["L"]
            P_ = g_df.attrs["pitch"]
            g_df.attrs["col_desc"][
                "dT"
            ] = f"Tension difference from target tension ({_fmt_val(T_, ' lbf')})"
            L_title = _fmt_val(L_, '"')
            table = _rich_table(
                g_df,
                title=f"Closest gauges\nfor {L_title} @ {P_}",
                float_format=float_format,
                panel=n_cases > 1,
                column_info=column_info,
                ihighlight=int(g_df.dT.abs().argmin()) if len(g_df) >= 2 else None,
            )
            tables.append(table)

        console.print(Columns(tables))

    else:
        if types and density is not None:
            error("Specify either --type or --density, not both.", rc=2)
        if not types and density is None:
            error(
                "Must supply --type (e.g. 'plain nylon', 'plain steel') or --density "
                "(e.g. '1.3 g/cm^3') to use exact gauge calculation.",
                rc=2,
            )

        try:
            (T_,), (L_,), (P_,) = T_vals, L_vals, P
        except ValueError:
            error(
                f"Only supply one value for each of T, L, P. "
                f"Got {len(T_vals)}, {len(L_vals)}, {len(P)}.",
                rc=2,
            )

        dens: float | Quantity
        type_verbose: str | None = None
        if density is not None:
            dens = _cli_val(density, dim="[mass] / [length] ** 3")
        else:
            assert types is not None
            if len(types) > 1:
                error(f"Only specify one type for exact gauge calculation. Got {types}.", rc=2)

            type_ = types[0]
            allowed_type_keys = sorted(
                list(DENSITY_LB_IN) + list(_STRING_TYPE_ALIAS_TO_VERBOSE), key=lambda s: s.lower()
            )
            if type_ not in allowed_type_keys:
                error(f"Type {type_!r} not allowed. Use one of {allowed_type_keys}.", rc=2)

            type_verbose = type_ if type_ in DENSITY_LB_IN else _STRING_TYPE_ALIAS_TO_VERBOSE[type_]
            dens = DENSITY_LB_IN[type_verbose]

        try:
            g = gauge(dens, T=T_, L=L_, pitch=P_)
        except ValueError as e:
            error(f"Failed to compute gauge. Message: {e}", rc=2)
        if units is not None:
            target_l_u = _cli_unit(units, dim="[length]")
            g = _to_cli_unit(g, target_l_u, default_unit="inch")

        if verbose:
            T_str = _fmt_val(T_, " lbf")
            L_str = _fmt_val(L_, '"')
            g_str = _fmt_val(g, '"', fmt=".3g")
            if type_verbose is not None:
                mat_part = f"a [green]{type_verbose}[/] string"
            else:
                dens_str = _fmt_val(dens, " lbm/in³")
                mat_part = f"a string of density [green]{dens_str}[/]"
            console.print(
                f"To get tension of [green]{T_str}[/] on {mat_part} "
                f"of length [green]{L_str}[/] tuned to [cyan]{P_}[/], "
                f"gauge [bold cyan underline]{g_str}[/] should be used.",
                highlight=False,
            )
        else:
            console.print(_fmt_val(g, fmt="") if isinstance(g, Quantity) else g)


@app.command(name="app")
def run_app(
    host: str = typer.Option("127.0.0.1", help="Host interface to bind."),
    port: int = typer.Option(0, "-p", "--port", help="Port to listen on (0 picks a free port)."),
    open_browser: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open the app in the default web browser.",
    ),
):
    """Launch the interactive web app backed by local Python."""
    from ._server import serve

    try:
        serve(
            host=host,
            port=port,
            open_browser=open_browser,
            on_ready=lambda url: console.print(
                f"Serving stringcalc app at [link={url}]{url}[/link] (Ctrl+C to stop)"
            ),
        )
    except FileNotFoundError as e:
        error(str(e), rc=1)
    except OSError as e:
        error(f"Could not start server on {host}:{port}: {e}", rc=1)


if __name__ == "__main__":
    app()
