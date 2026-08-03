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
    # GEN-77291 was called off 07/10/2026. This invoice represents a
    # same-day re-rental: contract starts 07/10/2026 (same day), bills
    # through 07/18/2026. This should NOT be a ghost rental - it's a
    # legitimate new rental starting the same day the old one ended.
    make_invoice("united_rentals_same_day_rerental.pdf", [
        "United Rentals Inc.",
        "Account #: UR-88213 | Invoice #: 0091841000",
        "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #4",
        "Unit: Generator Set 500kW  Serial: GEN-77291",
        "Contract Start: 07/10/2026   Billed Through: 07/18/2026",
        "Rental Days Billed: 8 @ Daily Rate $185.00/day = $1,480.00",
        "Environmental Service Charge: $50.00",
        "AFE: 2026-WH4-120   API#: 42-329-11829",
        "Total Amount Due: $1,530.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
