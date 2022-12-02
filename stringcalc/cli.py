"""
CLI
"""
from __future__ import annotations

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


def error(s: str) -> None:
    """Print error message."""
    console.print(s, style=Style(color="red", bold=True), highlight=False)


def info(s: str) -> None:
    """Print info message."""
    console.print(s, style=Style(color="cyan", bold=True), highlight=False)


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

        raise typer.Exit()


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


@app.command()
def frets(
    N: int = typer.Option(
        ..., "-N", "--number", help="Number of frets, starting from nut (fret 0)."
    ),
    L: float = typer.Option(..., "-L", "--scale-length", help="Scale length."),
    float_format: str = typer.Option("%.3f", help="Format for float-to-string conversion."),
    # TODO: `method`
    # TODO: `format` (rich, CSV, etc.)
):
    """Display fret distance table for `N` frets and scale length `L`."""
    from rich.table import Table

    from .frets import distances

    df = distances(N=N, L=L).reset_index()
    attrs = df.attrs.copy()  # doesn't seem to survive the following
    df_str = df.to_string(float_format=float_format, header=False, index=False)

    if "e" in df_str and console.is_terminal:
        df_str = re.sub(r"\S*e[+-][0-9]*", lambda m: _to_fancy_sci(m.group()), df_str)

    table = Table(title=f"Fret distances for L={L}")
    for col in df.columns:
        table.add_column(
            col if not console.is_terminal else attrs["fancy_col"][col],
            style="green" if col != "n" else None,
        )
    for row in df_str.splitlines():
        table.add_row(*re.split(r"(?<=\S) ", row))
    console.print(table)

    l = max(len(str(c.header)) for c in table.columns)  # noqa: E741
    for k in df.columns:
        k_display = k if not console.is_terminal else attrs["fancy_col"][k]
        v = attrs["col_desc"][k]
        console.print(f"[bold cyan]{k_display:{l+2}}[/]{v}")


_RE_LENGTH_SPEC = re.compile(r"(?P<a>[0-9ns])-(?P<b>[0-9ns])=(?P<d>[0-9e\.\+\-\.]+)")


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
    from frets import length_from_distance

    m = _RE_LENGTH_SPEC.fullmatch(spec)
    if m is None:
        error(f"Input failed to match a-b=d spec format regex {_RE_LENGTH_SPEC.pattern!r}")
        raise typer.Exit(2)

    dct = m.groupdict()
    a = _ab_interp(dct["a"])
    b = _ab_interp(dct["b"])
    d = float(dct["d"])

    res = length_from_distance((a, b), d)

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


@app.command()
def gauge(
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
    verbose: bool = typer.Option(False),
):
    """Compute gauge from string information.

    IMPORTANT: currently must use T in lbf and L in inches,
    returning results in inches.
    """
    from .tension import _STRING_TYPE_ALIAS_TO_VERBOSE, DENSITY_LB_IN, gauge, suggest_gauge

    if suggest:
        if not types:
            if verbose:
                info("No string types specified, defaulting to PB + PL.")
            types = {"PB", "PL"}

        g_df = suggest_gauge(
            T=T, L=L, pitch=P, types=set(types) if types is not None else None, n=nsuggest
        )

        print(g_df)

    else:
        if not types:
            error("Must supply type to use exact gauge calculation.")
            raise typer.Exit(2)

        if len(types) > 1:
            error("Only specify one type for exact gauge calculation. Got {types}.")
            raise typer.Exit(2)

        type_ = types[0]
        allowed_type_keys = sorted(
            list(DENSITY_LB_IN) + list(_STRING_TYPE_ALIAS_TO_VERBOSE), key=lambda s: s.lower()
        )
        if type_ not in allowed_type_keys:
            error(f"Type {type_!r} not allowed. Use one of {allowed_type_keys}.")
            raise typer.Exit(2)

        type_verbose = type_ if type_ in DENSITY_LB_IN else _STRING_TYPE_ALIAS_TO_VERBOSE[type_]
        dens = DENSITY_LB_IN[type_verbose]

        g = gauge(dens, T=T, L=L, pitch=P)

        if verbose:
            console.print(
                f"To get tension of [green]{T} lbf[/] on a [green]type[/] string "
                f'of length [green]{L}"[/] tuned to [cyan]{P}[/], '
                f'gauge [bold cyan underline]{g:.3g}"[/] should be used.',
                highlight=False,
            )
        else:
            console.print(g)


if __name__ == "__main__":
    app()
