"""
Regenerate the CLI example SVGs used in the README and docs.

    uv run python docs/make_cli_svgs.py
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent

# SVG stem: (terminal width, CLI args)
EXAMPLES = {
    "cli_gauge-suggest_tb23nw": (
        71,
        "gauge --suggest -T 17 -L 23 -P G2 -P D3 -P A3 -P E4 -N 6"
        " --type DA:LEW --type DA:LE --no-column-info",
    ),
    "cli_gauge-suggest_tb23nw_d": (
        54,
        "gauge --suggest -T 17 -L 23 -P D3 --type DA:LEW",
    ),
}

for stem, (width, args) in EXAMPLES.items():
    env = {
        **os.environ,
        "STRINGCALC_RICH_EXPORT": str(HERE / f"{stem}.svg"),
        "STRINGCALC_RICH_EXPORT_EMBED_FONT": "1",
        "COLUMNS": str(width),
        "TTY_COMPATIBLE": "1",  # e.g. fancy column names, even if not run in a terminal
        "PYTHONUTF8": "1",  # avoid cp1252 UnicodeEncodeError on Windows when piped/captured
    }
    subprocess.run([sys.executable, "-m", "stringcalc.cli", *args.split()], env=env, check=True)
