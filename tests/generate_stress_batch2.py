import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def make_invoice(filename, lines, start_y_offset=0):
    os.makedirs("data/sample_invoices", exist_ok=True)
    filepath = os.path.join("data/sample_invoices", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = height - 50 - start_y_offset
    for line in lines:
        c.setFont("Helvetica", 10)
        c.drawString(50, y, line)
        y -= 20
    c.save()
    print(f"Created: {filepath}")

if __name__ == "__main__":
    # 1. Boundary test: exactly 28 days (threshold is > 28, so this should PASS the rate-roll check)
    make_invoice("united_rentals_boundary_28days.pdf", [
        "United Rentals Inc.",
        "Account #: UR-55210 | Invoice #: 0091829555",
        "Bill To: Pioneer Fluid Logistics - Lease: Cactus Draw #5",
        "Unit: Pump Skid  Serial: PS-33110",
        "Contract Start: 07/01/2026   Billed Through: 07/29/2026",
        "Rental Days Billed: 28 @ Daily Rate $95.00/day = $2,660.00",
        "Environmental Service Charge: $80.00",
        "AFE: 2026-CD5-055   API#: 42-329-55210",
        "Total Amount Due: $2,740.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])

    # 2. Leading blank line before letterhead - tests fragility of header_line assumption
    make_invoice("apex_leading_blank_line.pdf", [
        "",
        "Apex Drilling & Rig Services",
        "INVOICE: INV-91002",
        "123 Energy Way, Houston, TX 77002  Date: July 27, 2026",
        "support@oilfieldservices.com  Terms: Net 30",
        "Description Qty Rate Amount",
        "Day Rate - Rig #2 (24 hrs) 1 $19,000.00 $19,000.00",
        "Total Due: $19,000.00",
    ])

    # 3. False-negative risk on "net" substring check - no real payment terms stated,
    # but "internet" appears in the email domain, which would slip past a naive
    # substring check for the word "net"
    make_invoice("apex_no_real_terms.pdf", [
        "Apex Drilling & Rig Services",
        "INVOICE: INV-91003",
        "123 Energy Way, Houston, TX 77002  Date: July 27, 2026",
        "contact@apexinternetservices.com",
        "Description Qty Rate Amount",
        "Day Rate - Rig #9 (24 hrs) 1 $18,500.00 $18,500.00",
        "Total Due: $18,500.00",
        "Payment due immediately upon receipt of goods",
    ])

    # 4. Completely unknown vendor - never tested this path
    make_invoice("unknown_vendor_invoice.pdf", [
        "Lonestar Wireline Services LLC",
        "Invoice #: LWS-4471",
        "456 Rig Road, Midland, TX 79701",
        "Description: Wireline logging services - Well #12",
        "Amount: $8,200.00",
        "Terms: Net 30",
    ])
