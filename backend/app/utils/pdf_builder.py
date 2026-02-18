from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_educational_report(pdf_path: Path, title: str, lines: list[str]) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, title)
    y -= 30

    c.setFont("Helvetica", 11)
    for line in lines:
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 40
        c.drawString(40, y, line)
        y -= 18

    c.showPage()
    c.save()
