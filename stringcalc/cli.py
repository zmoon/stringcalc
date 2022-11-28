"""
CLI
"""
from __future__ import annotations

import re

import typer
from rich.console import Console

from .frets import distances

console = Console()

console.is_terminal

app = typer.Typer(add_completion=False)


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

    table = Table(title=f"Fret distances for L={L}")
    for col in df.columns:
        table.add_column(col if not console.is_terminal else attrs["fancy_col"][col])
    for row in df_str.splitlines():
        table.add_row(*re.split(r"(?<=\S) ", row))
    console.print(table)

    l = max(len(c.header) for c in table.columns)  # noqa: E741
    for k in df.columns:
        k_display = k if not console.is_terminal else attrs["fancy_col"][k]
        v = attrs["col_desc"][k]
        console.print(f"[bold cyan]{k_display:{l+2}}[/]{v}")


if __name__ == "__main__":
    app()
