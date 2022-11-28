"""
CLI
"""
from __future__ import annotations

import re

import typer
from rich.console import Console
from rich.style import Style

from .frets import distances, length_from_distance

_TRAN_SUPE_DIGIT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

console = Console()

console.is_terminal

app = typer.Typer(add_completion=False)


def _to_fancy_sci(s: str) -> str:
    a, b0 = s.split("e")
    b = str(int(b0)).replace("-", "⁻").translate(_TRAN_SUPE_DIGIT)

    return f"{a}×10{b}"


def error(s: str) -> None:
    """Print error message."""
    console.print(s, style=Style(color="red", bold=True), highlight=False)


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

    df = distances(N=N, L=L).reset_index()
    attrs = df.attrs.copy()  # doesn't seem to survive the following
    df_str = df.to_string(float_format=float_format, header=False, index=False)

    if "e" in df_str and console.is_terminal:
        df_str = re.sub(r"\S*e[+-][0-9]*", lambda m: _to_fancy_sci(m.group()), df_str)

    table = Table(title=f"Fret distances for L={L}")
    for col in df.columns:
        table.add_column(col if not console.is_terminal else attrs["fancy_col"][col])
    for row in df_str.splitlines():
        table.add_row(*re.split(r"(?<=\S) ", row))
    console.print(table)

    l = max(len(str(c.header)) for c in table.columns)  # noqa: E741
    for k in df.columns:
        k_display = k if not console.is_terminal else attrs["fancy_col"][k]
        v = attrs["col_desc"][k]
        console.print(f"[bold cyan]{k_display:{l+2}}[/]{v}")


_RE_LENGTH_SPEC = re.compile(r"(?P<a>[0-9ns])->(?P<b>[0-9ns])=(?P<d>[0-9e\.\+\-\.]+)")


def _ab_interp(s: str) -> int | None:
    if s == "s":
        return None
    elif s == "n":
        return 0
    else:
        return int(s)


@app.command()
def length(
    spec: str = typer.Argument(
        ...,
    ),
):
    """Calculate the scale length implied by spec 'a->b=d'.

    Where `a` and `b` are fret numbers
    (use '0' or 'n' for nut, 's' for saddle)
    and `d` is the corresponding distance.
    """

    m = _RE_LENGTH_SPEC.fullmatch(spec)
    if m is None:
        error(f"Input failed to match a->b=d spec format regex {_RE_LENGTH_SPEC.pattern!r}")
        raise typer.Exit(2)

    dct = m.groupdict()
    a = _ab_interp(dct["a"])
    b = _ab_interp(dct["b"])
    d = float(dct["d"])

    res = length_from_distance((a, b), d)

    console.print(res)


if __name__ == "__main__":
    app()
