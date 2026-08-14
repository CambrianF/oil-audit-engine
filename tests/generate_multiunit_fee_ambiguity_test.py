import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def make_invoice(filename, lines):
    os.makedirs("data/sample_invoices", exist_ok=True)
    filepath = os.path.join("data/sample_invoices", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = height - 50
    for line in lines:
        c.setFont("Helvetica", 10)
        c.drawString(50, y, line)
        y -= 20
    c.save()
    print(f"Created: {filepath}")

if __name__ == "__main__":
    # Two units, BOTH with ESC cap violations at different amounts.
    # If the issue text doesn't cite which unit each belongs to, a
    # vendor reading the dispute letter cannot tell them apart.
    make_invoice("united_rentals_ambiguous_fee_units.pdf", [
        "United Rentals Inc.",
        "Account #: UR-77700 | Invoice #: 0091900001",
        "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #50",
        "Unit 1: Light Tower  Serial: LT-77701",
        "Rental Days Billed: 10 @ Daily Rate $95.00/day = $950.00",
        "Environmental Service Charge: $250.00",
        "Unit 2: Generator Set  Serial: GEN-77702",
        "Rental Days Billed: 10 @ Daily Rate $110.00/day = $1,100.00",
        "Environmental Service Charge: $180.00",
        "AFE: 2026-WH50-777   API#: 42-329-77700",
        "Total Amount Due: $2,480.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
