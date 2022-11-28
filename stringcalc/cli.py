"""
CLI
"""
from __future__ import annotations

import re

import typer
from rich.console import Console

from .frets import distances

_TRAN_SUPE_DIGIT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

console = Console()

console.is_terminal

app = typer.Typer(add_completion=False)


def _to_fancy_sci(s: str) -> str:
    a, b0 = s.split("e")
    b = str(int(b0)).replace("-", "⁻").translate(_TRAN_SUPE_DIGIT)

    return f"{a}×10{b}"


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


if __name__ == "__main__":
    app()
