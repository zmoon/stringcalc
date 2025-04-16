---
file_format: mystnb
kernelspec:
  name: python3
---

# Gauge suggest

We can use the {doc}`/api` or the {doc}`/cli` to do this.
For example, consider this Irish tenor banjo situation
(also shown in [the GitHub README](https://github.com/zmoon/stringcalc/blob/main/README.md)):

- target tension: 17 lbf
- scale length: 23"
- tuning: G{sub}`2` D{sub}`3` A{sub}`3` E{sub}`4`
- string types: D'Addario loop-end nickel-wound and plain steel (`DA:LEW` and `DA:LE`)

## API

We use the function {func}`stringcalc.tension.suggest_gauge`.

```{code-cell} ipython3
:tags: [hide-output]

from stringcalc.tension import suggest_gauge
```

```{code-cell} ipython3
T = 17
L = 23
pitches = ["G2", "D3", "A3", "E4"]
types = {"DA:LEW", "DA:LE"}

for pitch in pitches:
    df = suggest_gauge(T, L, pitch, types=types, n=6)
    display(
        df
        .style
        .set_caption(f'{pitch}, target T = {T} lbf')
        .highlight_min(df.dT.abs().argmin())
    )
```

Most players would prefer a wound A string.
The 018w is probably a better choice than the 017p here, tone- and balance-wise,
even though it is farther from the target tension.

## CLI

On the command-line, we can do the same thing
with `stringcalc gauge --suggest`:

```sh
stringcalc gauge --suggest -T 17 -L 23 -P G2 -P D3 -P A3 -P E4 -N 6 --type DA:LEW --type DA:LE --no-column-info
```

```{image} ../cli_gauge-suggest_tb23nw.svg
:alt: CLI gauge suggestion output for 23" TB for D'Addario loop-end nickel-wound strings
:width: 550

```

`--no-column-info` suppresses the descriptions of the columns,
which currently are repeated for each boxed result.
For a single string query, it looks like this:

```sh
stringcalc gauge --suggest -T 17 -L 23 -P D3 --type DA:LEW
```

```{image} ../cli_gauge-suggest_tb23nw_d.svg
:alt: CLI gauge suggestion output for 23" TB D string using D'Addario loop-end nickel-wound strings
:width: 450

```
