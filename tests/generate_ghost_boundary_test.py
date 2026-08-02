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
    # Legitimate final invoice - bills THROUGH the exact call-off date,
    # not past it. Should NOT trigger a ghost rental flag.
    make_invoice("united_rentals_ghost_boundary.pdf", [
        "United Rentals Inc.",
        "Account #: UR-50500 | Invoice #: 0091834400",
        "Bill To: Pioneer Fluid Logistics - Lease: Antelope #7",
        "Unit: Light Tower  Serial: LT-99500",
        "Contract Start: 07/01/2026   Billed Through: 07/15/2026",
        "Rental Days Billed: 14 @ Daily Rate $95.00/day = $1,330.00",
        "Environmental Service Charge: $60.00",
        "AFE: 2026-AT7-100   API#: 42-329-50500",
        "Total Amount Due: $1,390.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
