from __future__ import annotations

from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import Paragraph, SimpleDocTemplate

from .fonts import register_fonts
from .stylesheet import load_stylesheet


def create_pdf(config, file_path, text):
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
