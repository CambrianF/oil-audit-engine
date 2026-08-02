import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def make_invoice(filename, pages):
    """pages is a list of lists - one list of lines per page"""
    os.makedirs("data/sample_invoices", exist_ok=True)
    filepath = os.path.join("data/sample_invoices", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    for page_lines in pages:
        y = height - 50
        for line in page_lines:
            c.setFont("Helvetica", 10)
            c.drawString(50, y, line)
            y -= 20
        c.showPage()
    c.save()
    print(f"Created: {filepath}")

if __name__ == "__main__":
    # 1. Multi-page invoice - vendor info on page 1, charges on page 2
    make_invoice("apex_multipage.pdf", [
        [
            "Apex Drilling & Rig Services",
            "INVOICE: INV-92001",
            "123 Energy Way, Houston, TX 77002  Date: July 28, 2026",
            "support@oilfieldservices.com  Terms: Net 30",
            "Page 1 of 2 - Continued on next page",
        ],
        [
            "Description Qty Rate Amount",
            "Day Rate - Rig #3 (24 hrs) 1 $27,500.00 $27,500.00",
            "Total Due: $27,500.00",
        ],
    ])

    # 2. Credit/negative line item - tests if minus sign is handled
    make_invoice("united_rentals_with_credit.pdf", [[
        "United Rentals Inc.",
        "Account #: UR-66120 | Invoice #: 0091830220",
        "Bill To: Pioneer Fluid Logistics - Lease: Antelope #3",
        "Unit: Generator Set 300kW  Serial: GEN-88410",
        "Contract Start: 07/01/2026   Billed Through: 07/20/2026",
        "Rental Days Billed: 19 @ Daily Rate $110.00/day = $2,090.00",
        "Environmental Service Charge: $60.00",
        "Credit Adjustment: -$50.00",
        "AFE: 2026-AT3-091   API#: 42-329-66120",
        "Total Amount Due: $2,100.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ]])

    # 3. Line item with description but no dollar amount at all
    make_invoice("apex_missing_amount.pdf", [[
        "Apex Drilling & Rig Services",
        "INVOICE: INV-92003",
        "123 Energy Way, Houston, TX 77002  Date: July 28, 2026",
        "support@oilfieldservices.com  Terms: Net 30",
        "Description Qty Rate Amount",
        "Day Rate - Rig #5 (24 hrs) 1",
        "Fuel Surcharge - Diesel 1 $2,000.00 $2,000.00",
        "Total Due: $2,000.00",
    ]])

    # 4. United Rentals invoice with different phrasing for rental duration
    make_invoice("united_rentals_alt_phrasing.pdf", [[
        "United Rentals Inc.",
        "Account #: UR-71230 | Invoice #: 0091831110",
        "Bill To: Apex Drilling & Rig Services - Lease: Wildhorse #6",
        "Unit: Light Tower  Serial: LT-22019",
        "This unit has been on rent for 45 days at a rate of $175.00 per day.",
        "Environmental Service Charge: $60.00",
        "AFE: 2026-WH6-140   API#: 42-329-71230",
        "Total Amount Due: $7,935.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ]])

    # 5. Irregular spacing in field labels
    make_invoice("united_rentals_irregular_spacing.pdf", [[
        "United Rentals Inc.",
        "Account   #:  UR-90210   |   Invoice #:  0091832440",
        "Bill To: Pioneer Fluid Logistics - Lease: Cactus Draw #8",
        "Unit: Mud Pump  Serial:  MP-55210",
        "Contract Start: 07/05/2026    Billed Through: 08/10/2026",
        "Rental  Days  Billed:   36  @  Daily  Rate   $195.00/day  =  $7,020.00",
        "Environmental   Service   Charge:   $140.00",
        "AFE:  2026-CD8-201    API#:  42-329-90210",
        "Total Amount Due: $7,160.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ]])

    # 6. Blank page - simulates a scanned image with no text layer
    make_invoice("blank_no_text.pdf", [[]])
