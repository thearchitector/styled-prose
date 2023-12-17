import pytest
import reportlab.lib.enums as RLEnums
from reportlab.lib.colors import Color
from reportlab.lib.styles import ParagraphStyle as RLPStyle

from styled_prose.stylesheet import load_stylesheet

RENDER_DEFAULTS = {
    "leading": 14,
    "wordWrap": "LTR",
    "splitLongWords": False,
    "fontName": "Times",
    "fontSize": 12,
    "bulletFontName": "Times",
    "bulletFontSize": 12,
    "allowWidows": True,
    "allowOrphans": True,
    "firstLineIndent": 0,
    "leftIndent": 0,
    "rightIndent": 0,
    "fontColor": Color(0, 0, 0, 1),
}


@pytest.fixture(autouse=True)
def clear_cache():
    # clear the cache every run since we want to invoke all the logic for every
    # parametrization
    load_stylesheet.cache_clear()


@pytest.mark.parametrize(
    "style,expected",
    (
        # not supplied, uses builtin default
        ({}, RLPStyle("default", **RENDER_DEFAULTS)),
        # simple
        (
            {"name": "default", "font_size": 14, "font_name": "Arial"},
            RLPStyle(
                "default",
                **{
                    **RENDER_DEFAULTS,
                    "fontSize": 14,
                    "fontName": "Arial",
                    "leading": 16,
                    "bulletFontSize": 14,
                    "bulletFontName": "Arial",
                },
            ),
        ),
        # nested
        (
            {
                "name": "default",
                "bullet": {"font_name": "Arial", "font_size": 14, "indent": 8},
                "indent": {"left": 8, "right": 6, "first_line": 14},
            },
            RLPStyle(
                "default",
                **{
                    **RENDER_DEFAULTS,
                    "bulletFontName": "Arial",
                    "bulletFontSize": 14,
                    "bulletIndent": 8,
                    "leftIndent": 8,
                    "rightIndent": 6,
                    "firstLineIndent": 14,
                },
            ),
        ),
        # coerced
        (
            {
                "name": "default",
                "font_color": "#ff00ff",
                "alignment": "justify",
                "word_wrap": "rtl",
                "line_height": 20,
            },
            RLPStyle(
                "default",
                **{
                    **RENDER_DEFAULTS,
                    "fontColor": Color(1, 0, 1, 1),
                    "alignment": RLEnums.TA_JUSTIFY,
                    "wordWrap": "RTL",
                    "leading": 20,
                },
            ),
        ),
    ),
    ids=("builtin-default", "simple", "nested", "coerced"),
)
def test_load_stylesheet(mock_config, style, expected):
    # mock loaded config
    mock_config({"styles": [style] if style else []})

    ss = load_stylesheet("mock.toml")

    assert "default" in ss
    assert ss["default"].__dict__ == expected.__dict__
