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
    # United Rentals invoice billing for TWO units. First unit's ESC is
    # under cap ($60), second unit's ESC is way over cap ($180). If only
    # the first match gets checked, this real overcharge goes undetected.
    make_invoice("united_rentals_multi_unit.pdf", [
        "United Rentals Inc.",
        "Account #: UR-95100 | Invoice #: 0091870001",
        "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #20",
        "Unit 1: Light Tower  Serial: LT-95101",
        "Rental Days Billed: 10 @ Daily Rate $95.00/day = $950.00",
        "Environmental Service Charge: $60.00",
        "Unit 2: Generator Set  Serial: GEN-95102",
        "Rental Days Billed: 10 @ Daily Rate $110.00/day = $1,100.00",
        "Environmental Service Charge: $180.00",
        "AFE: 2026-WH20-951   API#: 42-329-95100",
        "Total Amount Due: $2,290.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
