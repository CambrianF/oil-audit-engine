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
    # Large negative ESC - if the minus sign is being dropped, this WILL
    # incorrectly show as a Cap Violation since 150 > 99
    make_invoice("united_rentals_large_negative_esc.pdf", [
        "United Rentals Inc.",
        "Account #: UR-40121 | Invoice #: 0091833302",
        "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #12",
        "Unit: Compressor Skid  Serial: CS-19005",
        "Contract Start: 07/01/2026   Billed Through: 07/18/2026",
        "Rental Days Billed: 17 @ Daily Rate $130.00/day = $2,210.00",
        "Environmental Service Charge: -$150.00",
        "AFE: 2026-WH12-088   API#: 42-329-40121",
        "Total Amount Due: $2,060.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
