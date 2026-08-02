import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_messy_rental_invoice():
    os.makedirs("data/sample_invoices", exist_ok=True)
    filepath = os.path.join("data/sample_invoices", "united_rentals_messy_01.pdf")

    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "United Rentals Inc.")
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 65, "Account #: UR-88213  |  Invoice #: 0091827364")
    c.drawString(50, height - 78, "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #4")

    c.setFont("Helvetica", 9)
    c.drawString(50, height - 110, "Unit: Generator Set 500kW  Serial: GEN-77291")
    c.drawString(50, height - 123, "Contract Start: 06/02/2026   Billed Through: 07/22/2026")
    c.drawString(50, height - 136, "Rental Days Billed: 50 @ Daily Rate $185.00/day = $9,250.00")
    c.drawString(50, height - 149, "Environmental Service Charge: $210.00")
    c.drawString(50, height - 162, "Fuel Surcharge: $88.40")
    c.drawString(50, height - 175, "Damage Waiver (RPP): $95.00")
    c.drawString(50, height - 195, "AFE: 2026-WH4-118   API#: 42-329-11827")
    c.drawString(50, height - 215, "Total Amount Due: $9,643.40")
    c.drawString(50, height - 235, "Terms: Net 30 | Please remit within 30 days of receipt")

    c.save()
    print(f"Created: {filepath}")

if __name__ == "__main__":
    create_messy_rental_invoice()
