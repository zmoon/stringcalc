---
file_format: mystnb
kernelspec:
  name: python3
---

# Pythagoras ratios

```{code-cell} ipython3
from fractions import Fraction

from stringcalc.frets import distances
```

## Define the ratios

I first saw these in [this StackExchange post](https://music.stackexchange.com/questions/93731/does-guitar-fret-spacing-solely-depend-on-the-length-of-the-string).
The same diagram can be found [here](https://passyworldofmathematics.com/guitar-mathematics/), which seems to be the original source.
I used [this table](https://en.wikipedia.org/wiki/Pythagorean_tuning#Method) to fill in (most of) the gaps (leaving out fret 6 since it is ambiguous).

```{code-cell} ipython3
# This maps the fret number to the relative distance to the saddle.
ratios = {
  1: "243/256",
  2: "8/9",
  3: "27/32",
  4: "64/81",
  5: "3/4",
  7: "2/3",
  8: "81/128",
  9: "16/27",
  10: "9/16",
  11: "128/243",
  12: "1/2",
}
ratios = {k: Fraction(v) for k, v in ratios.items()}
```

## Compare to our equal-temperament calculations

We use {func}`stringcalc.frets.distances`.

```{code-cell} ipython3
df = distances(12, L=1)
df["Pythagoras"] = df.index.map(ratios)
df["Pythagoras float"] = df["Pythagoras"].astype(float)

(
    df
    .assign(**{
        "Δ": df["Pythagoras float"] - df["d_inv"],
        "Equal temperament": df["d_inv"]}
    )
    [["Pythagoras", "Pythagoras float", "Equal temperament", "Δ"]]
    .fillna("")
)
```
