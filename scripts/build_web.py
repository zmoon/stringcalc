"""Build the stringcalc widget ESM bundle, standalone web app, and optional local wheel.

Usage examples:
    uv run python scripts/build_web.py                        # local wheel -> frontend/dist/app
    uv run python scripts/build_web.py --source pypi          # PyPI config -> frontend/dist/app
    uv run python scripts/build_web.py --out docs/_static/app # copy built app for Sphinx docs
    uv run python scripts/build_web.py --wheel-only           # refresh local wheel for `vite dev`
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
WEB_DIR = ROOT / "stringcalc" / "_web"
DIST_APP = FRONTEND / "dist" / "app"


def _run(cmd: list[str], *, cwd: Path = ROOT) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def _npm_bin() -> str:
    return shutil.which("npm") or ("npm.cmd" if sys.platform == "win32" else "npm")


def _write_app_config(target_dir: Path, source: str) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    cfg = {"stringcalcSource": source}
    (target_dir / "app-config.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def _build_local_wheel(target_dir: Path) -> Path:
    wheels_dir = target_dir / "wheels"
    if wheels_dir.exists():
        shutil.rmtree(wheels_dir)
    wheels_dir.mkdir(parents=True, exist_ok=True)

    uv = shutil.which("uv")
    if uv:
        _run([uv, "build", "--wheel", "--out-dir", str(wheels_dir)])
    else:
        _run([sys.executable, "-m", "build", "--wheel", "--outdir", str(wheels_dir)])

    wheels = sorted(wheels_dir.glob("stringcalc-*.whl"))
    if not wheels:
        raise RuntimeError(f"No stringcalc wheel found in {wheels_dir}")
    wheel = wheels[-1]
    (wheels_dir / "manifest.json").write_text(
        json.dumps({"wheel": wheel.name}, indent=2) + "\n", encoding="utf-8"
    )
    return wheel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build stringcalc web apps and widget bundle.")
    parser.add_argument(
        "--source",
        choices=("local", "pypi"),
        default="local",
        help="Package source for the Pyodide worker (default: local).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output directory to copy the built static app into (e.g. docs/_static/app).",
    )
    parser.add_argument(
        "--wheel-only",
        action="store_true",
        help="Only refresh frontend/public/wheels and app-config.json for `vite dev`.",
    )
    parser.add_argument(
        "--skip-widgets",
        action="store_true",
        help="Skip building stringcalc/widget/_bundle.js.",
    )
    args = parser.parse_args(argv)

    npm = _npm_bin()

    if args.wheel_only:
        public_dir = FRONTEND / "public"
        _write_app_config(public_dir, args.source)
        if args.source == "local":
            if not args.skip_widgets:
                _run([npm, "--prefix", str(FRONTEND), "run", "build:widgets"])
            _build_local_wheel(public_dir)
        return 0

    if not args.skip_widgets:
        _run([npm, "--prefix", str(FRONTEND), "run", "build:widgets"])

    _run([npm, "--prefix", str(FRONTEND), "run", "build:app"])

    if DIST_APP.exists():
        shutil.rmtree(DIST_APP)
    shutil.copytree(WEB_DIR, DIST_APP)

    _write_app_config(DIST_APP, args.source)
    if args.source == "local":
        _build_local_wheel(DIST_APP)
    else:
        wheels_dir = DIST_APP / "wheels"
        if wheels_dir.exists():
            shutil.rmtree(wheels_dir)

    if args.out is not None:
        out_dir = (ROOT / args.out).resolve() if not args.out.is_absolute() else args.out
        if out_dir.exists():
            shutil.rmtree(out_dir)
        shutil.copytree(DIST_APP, out_dir)
        print(f"Copied static app to {out_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
