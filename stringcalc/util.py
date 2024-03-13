from __future__ import annotations


def get_version(*, git: bool = True) -> str:
    """
    Parameters
    ----------
    git
        Include the short version of the Git hash in the returned version string.
    """
    from . import __version__

    ver = __version__
    if git:
        import subprocess
        import warnings
        from pathlib import Path

        repo = Path(__file__).parent.parent

        try:
            cmd = ["git", "-C", repo.as_posix(), "rev-parse", "--verify", "--short", "HEAD"]
            cp = subprocess.run(cmd, text=True, capture_output=True, check=True)
        except Exception:
            warnings.warn(f"Could not get Git hash using command `{' '.join(cmd)}`.")
            hsh = ""
        else:
            hsh = f" ({cp.stdout.strip()})"

        return f"{ver}{hsh}"
    else:
        return ver
