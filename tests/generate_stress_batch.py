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
    # 1. Clean United Rentals invoice - should PASS
    make_invoice("united_rentals_clean_01.pdf", [
        "United Rentals Inc.",
        "Account #: UR-77120 | Invoice #: 0091827999",
        "Bill To: Pioneer Fluid Logistics - Lease: Cactus Draw #2",
        "Unit: Light Tower LT-6  Serial: LT-99213",
        "Contract Start: 07/01/2026   Billed Through: 07/15/2026",
        "Rental Days Billed: 14 @ Daily Rate $95.00/day = $1,330.00",
        "Environmental Service Charge: $45.00",
        "Fuel Surcharge: $22.10",
        "AFE: 2026-CD2-042   API#: 42-329-99120",
        "Total Amount Due: $1,397.10",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])

    # 2. Clean Apex invoice - should PASS
    make_invoice("apex_clean_01.pdf", [
        "Apex Drilling & Rig Services",
        "INVOICE: INV-90555",
        "123 Energy Way, Houston, TX 77002  Date: July 26, 2026",
        "support@oilfieldservices.com  Terms: Net 30",
        "Description Qty Rate Amount",
        "Day Rate - Rig #7 (24 hrs) 3 $22,000.00 $66,000.00",
        "Fuel Surcharge - Diesel 1 $3,200.00 $3,200.00",
        "Total Due: $69,200.00",
    ])

    # 3. Adversarial: United Rentals invoice that mentions Apex in the body
    make_invoice("united_rentals_adversarial_01.pdf", [
        "United Rentals Inc.",
        "Account #: UR-33410 | Invoice #: 0091828111",
        "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #9",
        "Note: Previously serviced under Apex Drilling & Rig Services MSA ref #A-2214",
        "Unit: Mud Pump Skid  Serial: MP-44210",
        "Contract Start: 06/10/2026   Billed Through: 08/02/2026",
        "Rental Days Billed: 53 @ Daily Rate $210.00/day = $11,130.00",
        "Environmental Service Charge: $150.00",
        "Damage Waiver (RPP): $120.00",
        "AFE: 2026-WH9-201   API#: 42-329-44210",
        "Total Amount Due: $11,400.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
