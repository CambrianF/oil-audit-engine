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
    # A NEWER invoice for a brand new unit, at $200/day, dated August (later)
    make_invoice("united_rentals_drift_newer_zz.pdf", [
        "United Rentals Inc.",
        "Account #: UR-70200 | Invoice #: 0091860002",
        "Bill To: Pioneer Fluid Logistics - Lease: Antelope #12",
        "Unit: Light Tower  Serial: LT-70200",
        "Contract Start: 08/01/2026   Billed Through: 08/10/2026",
        "Rental Days Billed: 9 @ Daily Rate $200.00/day = $1,800.00",
        "Environmental Service Charge: $50.00",
        "AFE: 2026-AT12-700   API#: 42-329-70200",
        "Total Amount Due: $1,850.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])

    # An OLDER invoice for the SAME unit, at $150/day, dated July (earlier) -
    # arriving late / being reprocessed AFTER the newer one above. This
    # should NOT overwrite the comparison baseline with the older rate.
    # Note filename starts with a letter that sorts BEFORE "newer_zz" so
    # this actually gets processed first alphabetically - we need to name
    # it so it processes AFTER, to simulate true out-of-order arrival.
    make_invoice("united_rentals_drift_zzz_late_older.pdf", [
        "United Rentals Inc.",
        "Account #: UR-70200 | Invoice #: 0091860001",
        "Bill To: Pioneer Fluid Logistics - Lease: Antelope #12",
        "Unit: Light Tower  Serial: LT-70200",
        "Contract Start: 07/01/2026   Billed Through: 07/10/2026",
        "Rental Days Billed: 9 @ Daily Rate $150.00/day = $1,350.00",
        "Environmental Service Charge: $50.00",
        "AFE: 2026-AT12-699   API#: 42-329-70199",
        "Total Amount Due: $1,400.00",
        "Terms: Net 30 | Please remit within 30 days of receipt",
    ])
