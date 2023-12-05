from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from .exceptions import BadConfigException

try:
    import tomllib  # pyright: ignore
except ModuleNotFoundError:
    import tomli as tomllib

if TYPE_CHECKING:
    from os import PathLike
    from typing import Any, Dict, List, Union


@lru_cache(maxsize=None)
def load_config(path: Union[str, PathLike[str]]) -> Dict[str, Any]:
    """Load the provided configuration file, caching for subsequent use."""
    try:
        with open(path, "rb") as f:
            config: Dict[str, List[Dict[str, Any]]] = tomllib.load(f)
            return config
    except tomllib.TOMLDecodeError as err:
        raise BadConfigException("Invalid config TOML!") from err
