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
    # Brand new unit, never seen before - called off 07/12, this invoice
    # bills through 07/20, 8 days past return
    make_invoice("united_rentals_ghost_e2e_test.pdf", [
        "United Rentals Inc.",
        "Account #: UR-77000 | Invoice #: 0091835500",
        "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #15",
        "Unit: Compressor Skid  Serial: CS-77000",
        "Contract Start: 07/01/2026   Billed Through: 07/20/2026",
        "Rental Days Billed: 19 @ Daily Rate $140.00/day = $2,660.00",
        "Environmental Service Charge: $70.00",
        "AFE: 2026-WH15-500   API#: 42-329-77000",
        "Total Amount Due: $2,730.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
