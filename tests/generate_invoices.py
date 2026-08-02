import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_sample_invoice(filename, vendor, inv_num, items, total):
    os.makedirs("data/sample_invoices", exist_ok=True)
    filepath = os.path.join("data/sample_invoices", filename)

    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, vendor)

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, "123 Energy Way, Houston, TX 77002")
    c.drawString(50, height - 85, "support@oilfieldservices.com")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, height - 50, f"INVOICE: {inv_num}")
    c.setFont("Helvetica", 10)
    c.drawString(400, height - 68, "Date: July 25, 2026")
    c.drawString(400, height - 85, "Terms: Net 30")

    c.line(50, height - 110, width - 50, height - 110)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 125, "Description")
    c.drawString(300, height - 125, "Qty")
    c.drawString(360, height - 125, "Rate")
    c.drawString(450, height - 125, "Amount")
    c.line(50, height - 135, width - 50, height - 135)

    y = height - 155
    c.setFont("Helvetica", 10)
    for desc, qty, rate, amt in items:
        c.drawString(50, y, desc)
        c.drawString(300, y, str(qty))
        c.drawString(360, y, f"${rate:,.2f}")
        c.drawString(450, y, f"${amt:,.2f}")
        y -= 25

    c.line(350, y - 10, width - 50, y - 10)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, y - 30, "Total Due:")
    c.drawString(450, y - 30, f"${total:,.2f}")

    c.save()
    print(f"Created: {filepath}")

if __name__ == "__main__":
    create_sample_invoice(
        "invoice_apex_rig_01.pdf",
        "Apex Drilling & Rig Services",
        "INV-90421",
        [
            ("Day Rate - Rig #4 (24 hrs)", 2, 28500.00, 57000.00),
            ("Fuel Surcharge - Diesel", 1, 4500.00, 4500.00),
            ("BHA Rental & Maintenance", 1, 12000.00, 12000.00)
        ],
        73500.00
    )

    create_sample_invoice(
        "invoice_pioneer_fluids.pdf",
        "Pioneer Fluid Logistics",
        "PF-8832",
        [
            ("Water Hauling - Frac Tank Support", 18, 350.00, 6300.00),
            ("Flowback Disposal Fee", 5, 800.00, 4000.00)
        ],
        10300.00
    )
