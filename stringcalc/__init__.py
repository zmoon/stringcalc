"""
Instrument string calculations
"""

from ._ureg import ureg

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0"

__all__ = (
    "__version__",
    "ureg",
)
