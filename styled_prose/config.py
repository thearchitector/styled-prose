from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from .exceptions import BadConfigException

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Dict


@lru_cache(maxsize=None)
def load_config(path: Path) -> Dict[str, Any]:
    """Load the provided configuration file, caching for subsequent use."""
    try:
        with open(path, "rb") as f:
            config: Dict[str, Any] = tomllib.load(f)
            return config
    except tomllib.TOMLDecodeError as err:
        raise BadConfigException("Invalid config TOML!") from err
