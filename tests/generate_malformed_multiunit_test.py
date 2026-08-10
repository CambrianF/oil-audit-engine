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
    # This unit IS in the ledger as called off - a real ghost rental should
    # be caught here if dates are readable.
    record_call_off("GEN-88800", "07/01/2026", "CALLOFF-88800")

    # Multi-unit invoice: Unit 1 has NO Billed Through date at all (missing
    # field). Unit 2 has a real ghost rental with a malformed date format
    # (dashes instead of slashes). Neither should crash the program - both
    # should be gracefully skipped if unparseable, not silently treated as
    # a false positive OR silently propagate a crash to the whole batch.
    make_invoice("united_rentals_malformed_multiunit.pdf", [
        "United Rentals Inc.",
        "Account #: UR-88800 | Invoice #: 0091890001",
        "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #40",
        "Unit 1: Light Tower  Serial: LT-88700",
        "Rental Days Billed: 10 @ Daily Rate $90.00/day = $900.00",
        "Unit 2: Generator Set  Serial: GEN-88800",
        "Contract Start: 2026-06-01   Billed Through: 2026-07-15",
        "Rental Days Billed: 45 @ Daily Rate $275.00/day = $12,375.00",
        "Environmental Service Charge: $50.00",
        "AFE: 2026-WH40-888   API#: 42-329-88800",
        "Total Amount Due: $13,325.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
