from __future__ import annotations

import string
from typing import TYPE_CHECKING, Literal, Optional

import reportlab.lib.enums as RLEnums
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle as RLPStyle
from reportlab.lib.styles import StyleSheet1 as StyleSheet

from .exceptions import BadStyleException

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Dict

from functools import lru_cache

from . import config as spconfig
from .util import to_camel_case


class Indent(BaseModel):
    left: Optional[int] = 0
    right: Optional[int] = 0
    first_line: Optional[int] = 0


class Bullet(BaseModel):
    font_name: Optional[str] = None
    font_size: Optional[int] = None
    indent: int = 0
    anchor: Literal["start", "middle", "end"] = "start"


class ParagraphStyle(BaseModel):
    name: str

    # global font properties
    font_name: str = "Times"
    font_size: int = 12
    font_color: str = "#000000"

    # spacing properties
    line_height: Optional[int] = None
    space_before: int = 0
    space_after: int = 0
    indent: Indent = Indent()
    alignment: Literal["left", "center", "right", "justify"] = "left"

    # viewport properties (wrapping)
    word_wrap: Optional[Literal["cjk", "ltr", "rtl"]] = "ltr"
    split_long_words: bool = False
    ## https://en.wikipedia.org/wiki/Widows_and_orphans
    allow_widows: bool = True
    allow_orphans: bool = True

    # list style
    bullet: Bullet = Bullet()

    model_config = ConfigDict(extra="forbid")

    @field_validator("font_color")
    @classmethod
    def check_is_color(cls, value: str) -> str:
        if value[0] != "#" or any(c not in string.hexdigits for c in value[1:]):
            raise ValueError(
                "Colors must begin with '#' and be a valid 6-character hex string!"
            )

        return value

    def to_reportlab(self) -> RLPStyle:
        """
        Convert this configured paragraph style into one supported by ReportLab. We
        have to manually convert some properties that are exposed differently for
        clarity / ease of use.
        """
        properties: Dict[str, Any] = {}
        for field, value in self.__dict__.items():
            # if a nested property, handle separately
            if isinstance(value, BaseModel):
                for f, val in vars(value).items():
                    if field == "bullet" and not val:
                        if f == "font_name":
                            val = self.font_name
                        elif f == "font_size":
                            val = self.font_size

                    properties[to_camel_case(f, field, swap=(field == "indent"))] = val
                continue
            # if a color, convert to a HexColor object
            elif "color" in field:
                value = HexColor(value)
            # if an alignment, convert to the proper integer literal
            elif field == "alignment":
                value = getattr(RLEnums, f"TA_{value.upper()}")
            elif field == "word_wrap" and value:
                value = value.upper()
            elif field == "line_height":
                field = "leading"
                if not value:
                    # default single spaced
                    value = round(self.font_size * 1.15)

            properties[to_camel_case(field)] = value

        return RLPStyle(**properties)


@lru_cache(maxsize=None)
def load_stylesheet(path: Path) -> StyleSheet:
    """
    Given a path to a TOML stylesheet definition, load the paragraph
    styles and construct a RL stylesheet to use when generating styled prose.
    """
    config: Dict[str, Any] = spconfig.load_config(path)
    stylesheet: StyleSheet = StyleSheet()

    for style in config.get("styles", []):
        # check to ensure the name of the style is unique
        name = style.pop("name")
        if name in stylesheet:
            raise BadStyleException(
                f"All styles must be unique, but {name} was listed at least twice!"
            )

        # try to coerce the style to the proper format, adding it if successful
        try:
            ps: ParagraphStyle = ParagraphStyle(name=name, **style)
            stylesheet.add(ps.to_reportlab())
        except ValidationError as err:
            raise BadStyleException(
                f"Invalid paragraph style {name}! Misconfigurations are listed below:\n"
                f"\n{err}"
            ) from None

    # add the default style is not overridden
    if "default" not in stylesheet:
        stylesheet.add(ParagraphStyle(name="default").to_reportlab())

    return stylesheet
