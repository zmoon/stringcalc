"""
CLI
"""
from __future__ import annotations

import functools
import re
from pathlib import Path

try:
    import typer
    from rich.console import Console
    from rich.style import Style
except ImportError as e:
    print("The stringcalc CLI requires typer and rich (included with the 'cli' extra).")
    print(f"Error was: {e!r}")
    raise SystemExit(1)


HERE = Path(__file__).parent
_TRAN_SUPE_DIGIT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

console = Console()

app = typer.Typer(add_completion=False)


def _to_fancy_sci(s: str) -> str:
    a, b0 = s.split("e")
    b = str(int(b0)).replace("-", "⁻").translate(_TRAN_SUPE_DIGIT)

    return f"{a}×10{b}"


def error(s: str, *, rc: int = 1, markup: bool = True) -> None:
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
        import subprocess

        from . import __version__

        v = f"[rgb(184,115,51)]stringcalc[/] [bold blue]{__version__}[/]"
        try:
            cmd = ["git", "-C", HERE.as_posix(), "rev-parse", "--verify", "--short", "HEAD"]
            cp = subprocess.run(cmd, text=True, capture_output=True, check=True)
        except Exception:
            pass
        else:
            v += f" [rgb(100,100,100)]({cp.stdout.strip()})[/]"

        console.print(v, highlight=False)

        raise typer.Exit(0)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version/",
        help="Print version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
):
    ...


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


def pprint_table(df, *, title: str, float_format: str) -> None:
    from rich.table import Table

    attrs = df.attrs.copy()
    df_str = _with_float_nonext_dtypes(df).to_string(
        float_format=float_format, header=False, index=False
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
    for col in df.columns:
        table.add_column(
            maybe_fancy_col_name(col),
            style="green" if col != "n" else None,
        )
    for row in df_str.splitlines():
        table.add_row(*re.split(r"(?<=\S) ", row))
    console.print(table)

    # Column descriptions
    if "col_desc" not in attrs:
        return
    l = max(len(str(c.header)) for c in table.columns)  # noqa: E741
    for col in df.columns:
        v = attrs["col_desc"].get(col)
        if v is None:
            continue
        console.print(f"[bold cyan]{maybe_fancy_col_name(col):{l+2}}[/]{v}")


@app.command()
def frets(
    N: int = typer.Option(
        17, "-N", "--number", help="Number of frets, starting from nut (fret 0)."
    ),
    L: float = typer.Option(..., "-L", "--scale-length", help="Scale length."),
    float_format: str = typer.Option(r"%.3f", help="Format for float-to-string conversion."),
    # TODO: `method`
    # TODO: `format` (rich, CSV, etc.)
):
    """Display fret distance table for `N` frets and scale length `L`."""
    from .frets import distances

    df = distances(N=N, L=L).reset_index()

    pprint_table(df, title=f"Fret distances for L={L}", float_format=float_format)


_RE_LENGTH_SPEC = re.compile(r"(?P<a>[0-9]+|[ns])-(?P<b>[0-9]+|[ns])=(?P<d>[0-9e\.\+\-\.]+)")


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
def length(
    spec: str = typer.Argument(...),
    round_: int = typer.Option(None, "--round", help="Round result to this decimal precision."),
    verbose: bool = typer.Option(False),
):
    """Calculate the scale length implied by spec 'a-b=d'.

    Where `a` and `b` are fret numbers
    (use '0' or 'n' for nut, 's' for saddle)
    and `d` is the corresponding distance.
    """
    from .frets import length_from_distance

    m = _RE_LENGTH_SPEC.fullmatch(spec)
    if m is None:
        error(
            f"Input failed to match a-b=d spec format regex {_RE_LENGTH_SPEC.pattern!r}",
            rc=2,
            markup=False,
        )

    assert m is not None
    dct = m.groupdict()
    try:
        a = _ab_interp(dct["a"])
        b = _ab_interp(dct["b"])
        d = float(dct["d"])
    except ValueError as e:
        error(f"Failed to convert input to frets. Message: {e}", rc=2)

    try:
        res = length_from_distance((a, b), d)
    except ValueError as e:
        error(f"Failed to compute scale length. Message: {e}", rc=2)

    if round_ is not None:
        res = round(float(res), round_)

    if verbose:
        a_name = _ab_name(a)
        b_name = _ab_name(b)
        console.print(
            f"A distance from [green]{a_name}[/] to [red]{b_name}[/] "
            f"of [cyan]{d}[/] implies a scale length of [bold cyan underline]{res}[/].",
            highlight=False,
        )
    else:
        console.print(res)


@app.command(name="gauge")
@pretty_warnings
def gauge_(
    T: float = typer.Option(..., "-T", "--tension", help="Desired tension"),
    L: float = typer.Option(..., "-L", "--length", help="String length (scale length)."),
    P: str = typer.Option(
        ..., "-P", "--pitch", help="Pitch in scientific pitch notation (e.g. 'E4')."
    ),
    suggest: bool = typer.Option(
        False,
        help=("If true, suggest D'Addario gauges. If false, compute exact gauge."),
    ),
    types: list[str] = typer.Option(
        None, "--type", help="String type. Can specify multiple times if using --suggest."
    ),
    nsuggest: int = typer.Option(
        3, "-N", "--nsuggest", help="Number of suggestions. Only relevant if using --suggest."
    ),
    float_format: str = typer.Option(
        r"%.3f", help="Format for float-to-string conversion. Only relevant if using --suggest."
    ),
    verbose: bool = typer.Option(False),
):
    """Compute gauge from string information.

    IMPORTANT: currently must use T in lbf and L in inches,
    returning results in inches.
    """
    from .tension import _STRING_TYPE_ALIAS_TO_VERBOSE, DENSITY_LB_IN, gauge, suggest_gauge

    if suggest:
        types_set: set[str]
        if not types:
            if verbose:
                info("No string types specified, defaulting to PB + PL.")
            types_set = {"PB", "PL"}
        else:
            types_set = set(types)

        g_df = suggest_gauge(T=T, L=L, pitch=P, types=types_set, n=nsuggest)

        if verbose:
            info(f"Searching string types: {types_set}")
        g_df.attrs["col_desc"]["dT"] += f" ({T} lbf)"
        pprint_table(
            g_df,
            title=f"Closest D'Addario gauges\nfor {L}\" @ {P}",
            float_format=float_format,
        )

    else:
        if not types:
            error("Must supply type to use exact gauge calculation.", rc=2)

        if len(types) > 1:
            error("Only specify one type for exact gauge calculation. Got {types}.", rc=2)

        type_ = types[0]
        allowed_type_keys = sorted(
            list(DENSITY_LB_IN) + list(_STRING_TYPE_ALIAS_TO_VERBOSE), key=lambda s: s.lower()
        )
        if type_ not in allowed_type_keys:
            error(f"Type {type_!r} not allowed. Use one of {allowed_type_keys}.", rc=2)

        type_verbose = type_ if type_ in DENSITY_LB_IN else _STRING_TYPE_ALIAS_TO_VERBOSE[type_]
        dens = DENSITY_LB_IN[type_verbose]

        g = gauge(dens, T=T, L=L, pitch=P)

        if verbose:
            console.print(
                f"To get tension of [green]{T} lbf[/] on a [green]{type_verbose}[/] string "
                f'of length [green]{L}"[/] tuned to [cyan]{P}[/], '
                f'gauge [bold cyan underline]{g:.3g}"[/] should be used.',
                highlight=False,
            )
        else:
            console.print(g)


if __name__ == "__main__":
    app()
