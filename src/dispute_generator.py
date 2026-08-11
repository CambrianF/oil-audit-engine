import os
import re
from datetime import date

DISPUTE_OUTPUT_DIR = "disputes"


def extract_dollar_amount(issue_text):
    amounts = re.findall(r'\$([0-9,]+\.\d{2})', issue_text)
    if not amounts:
        return 0.0
    return max(float(a.replace(',', '')) for a in amounts)


def generate_dispute_letter(audit_result):
    """Builds a plain-text dispute letter for one flagged invoice, citing
    each real financial issue with its dollar figure. Returns None if:
    - the invoice failed to process at all (a PDF read error is not a
      disputable charge - it needs human review, not a vendor letter)
    - there are no genuine financial problems (informational credits and
      compliance-only issues don't warrant a dispute - there's nothing
      to ask the vendor to credit back)."""
    if audit_result.get("status") == "Failed":
        return None

    real_issues = [
        i for i in audit_result.get("financial_issues", [])
        if i != "None" and "Credit Noted" not in i
    ]

    if not real_issues:
        return None

    vendor = audit_result.get("vendor_name", "Unknown Vendor")
    invoice_number = audit_result.get("invoice_number", "N/A")
    account_number = audit_result.get("account_number", "N/A")

    total_disputed = sum(extract_dollar_amount(i) for i in real_issues)

    lines = []
    lines.append(f"Date: {date.today().strftime('%B %d, %Y')}")
    lines.append("")
    lines.append(f"To: Accounts Receivable Department, {vendor}")
    lines.append(f"Re: Invoice #{invoice_number} — Request for Credit Memo")
    lines.append("")
    lines.append(f"Account Reference: {account_number}")
    lines.append("")
    lines.append(
        "We are writing to formally dispute the following charge(s) on the "
        "above-referenced invoice and request that a credit memo be issued "
        "for the amount(s) noted below."
    )
    lines.append("")
    lines.append("Disputed Item(s):")
    lines.append("")
    for idx, issue in enumerate(real_issues, 1):
        lines.append(f"{idx}. {issue}")
        lines.append("")
    lines.append(f"Total Amount Disputed: ${total_disputed:,.2f}")
    lines.append("")
    lines.append(
        "Please review the above and issue a corrected invoice or credit "
        "memo at your earliest convenience. Supporting documentation is "
        "available upon request. We appreciate your prompt attention to "
        "this matter."
    )
    lines.append("")
    lines.append("Regards,")
    lines.append("Accounts Payable Department")

    return "\n".join(lines)


def write_dispute_letters(audit_results):
    os.makedirs(DISPUTE_OUTPUT_DIR, exist_ok=True)
    written = []

    for result in audit_results:
        letter = generate_dispute_letter(result)
        if letter is None:
            continue

        invoice_number = result.get("invoice_number", "unknown")
        safe_invoice = re.sub(r'[^A-Za-z0-9\-]', '_', invoice_number)
        vendor_slug = re.sub(r'[^A-Za-z0-9]', '_', result.get("vendor_name", "vendor"))
        filename = f"dispute_{vendor_slug}_{safe_invoice}.txt"
        filepath = os.path.join(DISPUTE_OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(letter)

        written.append(filepath)

    return written
