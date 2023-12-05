from __future__ import annotations

from typing import TYPE_CHECKING

from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import Paragraph, SimpleDocTemplate

from .fonts import register_fonts
from .stylesheet import load_stylesheet

if TYPE_CHECKING:
    from pathlib import Path


def create_pdf(config: Path, file_path: Path, text: str) -> None:
    document = SimpleDocTemplate(
        file_path,
        leftMargin=0,
        topMargin=0,
        rightMargin=0,
        bottomMargin=0,
        pagesize=LETTER,
    )

    text = text.replace("\r", "").replace("\n", "<br />")

    register_fonts(config)
    ss = load_stylesheet(config)
    document.build([Paragraph(text, ss["default"])])
