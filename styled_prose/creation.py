from __future__ import annotations

from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate

from .stylesheet import load_stylesheet


def create_pdf(config, file_path, text):
    document = SimpleDocTemplate(
        file_path,
        leftMargin=0,
        topMargin=0,
        rightMargin=0,
        bottomMargin=0,
        pagesize=letter,
    )

    text = text.replace("\r", "").replace("\n", "<br />")

    ss = load_stylesheet(config)
    document.build([Paragraph(text, ss["default"])])
