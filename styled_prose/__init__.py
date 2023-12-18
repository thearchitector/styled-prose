""".. include:: ../README.md"""

from .creation import StyledProseGenerator
from .exceptions import BadConfigException, BadFontException, BadStyleException
from .stylesheet import ParagraphStyle

__all__ = [
    "ParagraphStyle",
    "StyledProseGenerator",
    "BadConfigException",
    "BadStyleException",
    "BadFontException",
]
