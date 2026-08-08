import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from src.ledger import record_call_off

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
    # Unit 2 (GEN-99900) was called off 07/01/2026 - this is the unit
    # with the real ghost-rental problem.
    record_call_off("GEN-99900", "07/01/2026", "CALLOFF-99900")

    # Multi-unit invoice: Unit 1 is normal/current at $100/day (no issue).
    # Unit 2 is billed through 07/15/2026 at $300/day - 14 days past its
    # 07/01 call-off. If the ghost-rental math uses the WRONG rate
    # (Unit 1's $100 instead of Unit 2's $300), the calculated overcharge
    # will be wrong by a factor of 3x.
    make_invoice("united_rentals_ghost_multiunit.pdf", [
        "United Rentals Inc.",
        "Account #: UR-99900 | Invoice #: 0091880001",
        "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #30",
        "Unit 1: Light Tower  Serial: LT-99800",
        "Rental Days Billed: 10 @ Daily Rate $100.00/day = $1,000.00",
        "Unit 2: Generator Set  Serial: GEN-99900",
        "Contract Start: 06/01/2026   Billed Through: 07/15/2026",
        "Rental Days Billed: 45 @ Daily Rate $300.00/day = $13,500.00",
        "Environmental Service Charge: $50.00",
        "AFE: 2026-WH30-999   API#: 42-329-99900",
        "Total Amount Due: $14,550.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
