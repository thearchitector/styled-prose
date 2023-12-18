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
    """
    Every property within this class changes the formatting and subsequent rendering
    of any prose using the style.

    For example, the following changes the default font size to 14 and the font
    family to "EB Garamond". To register custom fonts, like "EB Garamond", see
    `FontFamily`.

    ```toml
    [[styles]]
    name = "default"
    font_size = 14
    font_name = "EB Garamond"
    ```
    Multiple styles are supported through multiple `[[styles]]` definitions.
    """

    name: str
    """
    The name of the style. It must be unique, and can be referenced from
    `StyledProseGenerator.create_jpg`.
    """

    # global font properties
    font_name: str = "Times"
    """
    The font family this style should use to render prose. "Times" (the default),
    "Helvetica" / "Arial", and "Courier" are bundeled and available. You can supply
    your own fonts via the `[[fonts]]` section of your stylesheet; see `FontFamily`.
    """
    font_size: int = 12
    """ The font size. It is 12pt by default."""
    font_color: str = "#000000"
    """
    The color of your prose in hexademical format ("#RRGGBB"). By default, this is
    black ("#000000").
    """

    # spacing properties
    line_height: Optional[int] = None
    """
    The desired line height. This value should be provided in absolute font size
    points; by default, it will be 115% of the provided font size (single spaced).
    """
    space_before: int = 0
    space_after: int = 0
    indent: Indent = Indent()
    alignment: Literal["left", "center", "right", "justify"] = "left"
    """
    The justification of rendered prose. By default, all text will be left-justified. It
    can be any one of "left", "center", "right", or "justify".
    """

    # viewport properties (wrapping)
    text_direction: Optional[Literal["cjk", "ltr", "rtl"]] = "ltr"
    """
    Controls the text direction. By default it is "ltr" (left to right), but can
    also be "rtl" (right to left) and "cjk" (Chinese, Japanese, or Korean).
    """
    split_long_words: bool = False
    """
    Dictates if long words can be split in order to more compactly wrap text. By
    default, long words will begin a new line instead of being split.
    """

    ## https://en.wikipedia.org/wiki/Widows_and_orphans
    allow_widows: bool = True
    """
    Determines if widows are allowed; a widow is a line of text carried over to a new
    page because it doesn't fit on the previous.

    <https://en.wikipedia.org/wiki/Widows_and_orphans>
    """
    allow_orphans: bool = True
    """
    Determines if orphans are allowed; an orphan is the last word of a sentence that is
    too long to fit on the same line. If this docstring were to extend the entire width of this paragraph, the last word would be an<br />orphan.

    <https://en.wikipedia.org/wiki/Widows_and_orphans>
    """

    # list style
    bullet: Bullet = Bullet()

    model_config = ConfigDict(extra="forbid")

    @field_validator("font_color")
    @classmethod
    def _check_is_color(cls, value: str) -> str:
        if value[0] != "#" or any(c not in string.hexdigits for c in value[1:]):
            raise ValueError(
                "Colors must begin with '#' and be a valid 6-character hex string!"
            )

        return value

    def _to_reportlab(self) -> RLPStyle:
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
            elif field == "text_direction" and value:
                field = "word_wrap"
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
            stylesheet.add(ps._to_reportlab())
        except ValidationError as err:
            raise BadStyleException(
                f"Invalid paragraph style {name}! Misconfigurations are listed below:\n"
                f"\n{err}"
            ) from None

    # add the default style is not overridden
    if "default" not in stylesheet:
        stylesheet.add(ParagraphStyle(name="default")._to_reportlab())

    return stylesheet
