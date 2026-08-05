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
    # Basin Trucking Co. - a brand new vendor added purely via contracts.json,
    # no Python code written. Rate is deliberately over the $185 cap.
    make_invoice("basin_trucking_over_cap.pdf", [
        "Basin Trucking Co.",
        "Invoice #: BT-40021",
        "Account #: BTC-90210",
        "Description: Water Hauling Services - Wildhorse Lease",
        "Hourly Rate: $210.00/hr",
        "Total Hours: 12",
        "Total Amount Due: $2,520.00",
        "Terms: Net 30",
    ])

    # A clean Basin Trucking invoice, under cap - should pass
    make_invoice("basin_trucking_clean.pdf", [
        "Basin Trucking Co.",
        "Invoice #: BT-40022",
        "Account #: BTC-90211",
        "Description: Water Hauling Services - Antelope Lease",
        "Hourly Rate: $165.00/hr",
        "Total Hours: 8",
        "Total Amount Due: $1,320.00",
        "Terms: Net 30",
    ])
