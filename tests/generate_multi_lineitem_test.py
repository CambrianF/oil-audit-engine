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
    # Apex invoice billing for TWO rigs - first rig is UNDER cap ($20,000,
    # cap is $26,000), second rig is WAY OVER cap ($32,000). If only the
    # first match gets checked, this second, larger overcharge goes
    # completely undetected.
    make_invoice("apex_multi_rig_overcharge.pdf", [
        "Apex Drilling & Rig Services",
        "INVOICE: INV-93001",
        "123 Energy Way, Houston, TX 77002  Date: August 5, 2026",
        "support@oilfieldservices.com  Terms: Net 30",
        "Description Qty Rate Amount",
        "Day Rate - Rig #1 (24 hrs) 1 $20,000.00 $20,000.00",
        "Day Rate - Rig #8 (24 hrs) 1 $32,000.00 $32,000.00",
        "Total Due: $52,000.00",
    ])
