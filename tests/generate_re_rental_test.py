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
    # GEN-77291 was called off 07/10/2026 per the ledger. This invoice
    # represents a LEGITIMATE new rental of the same unit, starting
    # 07/15/2026 (after the call-off) and billing through 07/25/2026.
    # This should NOT be flagged as a ghost rental.
    make_invoice("united_rentals_re_rental.pdf", [
        "United Rentals Inc.",
        "Account #: UR-88213 | Invoice #: 0091840000",
        "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #4",
        "Unit: Generator Set 500kW  Serial: GEN-77291",
        "Contract Start: 07/15/2026   Billed Through: 07/25/2026",
        "Rental Days Billed: 10 @ Daily Rate $185.00/day = $1,850.00",
        "Environmental Service Charge: $60.00",
        "AFE: 2026-WH4-119   API#: 42-329-11828",
        "Total Amount Due: $1,910.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
