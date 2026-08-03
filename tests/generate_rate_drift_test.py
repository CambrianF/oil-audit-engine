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
    # First invoice: baseline rate for a new unit, $150/day
    make_invoice("united_rentals_drift_baseline.pdf", [
        "United Rentals Inc.",
        "Account #: UR-60100 | Invoice #: 0091850001",
        "Bill To: Pioneer Fluid Logistics - Lease: Antelope #9",
        "Unit: Light Tower  Serial: LT-60100",
        "Contract Start: 06/01/2026   Billed Through: 06/10/2026",
        "Rental Days Billed: 9 @ Daily Rate $150.00/day = $1,350.00",
        "Environmental Service Charge: $50.00",
        "AFE: 2026-AT9-600   API#: 42-329-60100",
        "Total Amount Due: $1,400.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])

    # Second invoice, same unit, later - rate quietly bumped to $185/day
    make_invoice("united_rentals_drift_hike.pdf", [
        "United Rentals Inc.",
        "Account #: UR-60100 | Invoice #: 0091850002",
        "Bill To: Pioneer Fluid Logistics - Lease: Antelope #9",
        "Unit: Light Tower  Serial: LT-60100",
        "Contract Start: 07/01/2026   Billed Through: 07/10/2026",
        "Rental Days Billed: 9 @ Daily Rate $185.00/day = $1,665.00",
        "Environmental Service Charge: $50.00",
        "AFE: 2026-AT9-601   API#: 42-329-60101",
        "Total Amount Due: $1,715.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
