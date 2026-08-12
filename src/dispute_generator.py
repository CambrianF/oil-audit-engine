import os
import re
from datetime import date

DISPUTE_OUTPUT_DIR = "disputes"


def extract_disputed_amount(issue_text):
    """Determines the actual dollar amount being disputed for a given
    issue, based on how that issue type states its numbers - NOT just
    the largest dollar figure in the string, which was wrong (e.g. an
    ESC Cap Violation states the full billed amount AND the cap; the
    disputed amount is the difference, not the full billed amount).
    Returns None when the issue type doesn't state a clean, confidently
    calculable dispute amount (e.g. Rate-Roll Failure, which needs a
    weekly/monthly rate not on file to calculate real savings; or a
    Proprietary Benchmarking Alert, which is an informational signal,
    not a firm contractual violation)."""

    if "Cap Violation" in issue_text or "Rate Variance" in issue_text:
        # Format: "... $X exceeds contractual cap of $Y" or "... $X exceeds cap of $Y"
        amounts = re.findall(r'\$([0-9,]+\.\d{2})', issue_text)
        if len(amounts) >= 2:
            billed = float(amounts[0].replace(',', ''))
            cap = float(amounts[1].replace(',', ''))
            return round(billed - cap, 2)
        return None

    if "Unauthorized" in issue_text and "charge of $" in issue_text:
        # Format: "... charge of $X billed despite ..."
        amounts = re.findall(r'charge of \$([0-9,]+\.\d{2})', issue_text)
        if amounts:
            return float(amounts[0].replace(',', ''))
        return None

    if "overcharge at" in issue_text:
        # Format: "... ($X overcharge at $Y/day)" - Ghost Rental Detected
        m = re.search(r'\(\$([0-9,]+\.\d{2}) overcharge', issue_text)
        if m:
            return float(m.group(1).replace(',', ''))
        return None

    if "Rate-Card Drift" in issue_text:
        # Format: "... a $X/day (Y%) increase ..." - this is the per-day
        # increase, not a total dispute amount across the full rental,
        # so it is NOT confidently calculable as a single total either.
        return None

    # Rate-Roll Failure and Proprietary Benchmarking Alert intentionally
    # fall through to here - neither states a clean, confidently
    # calculable dispute total without additional contract data
    # (weekly/monthly rate, or benchmark being advisory rather than
    # contractual).
    return None


def generate_dispute_letter(audit_result):
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

    calculated_total = 0.0
    items_needing_manual_review = 0

    lines = []
    lines.append(f"Date: {date.today().strftime('%B %d, %Y')}")
    lines.append("")
    lines.append(f"To: Accounts Receivable Department, {vendor}")
    lines.append(f"Re: Invoice #{invoice_number} - Request for Credit Memo")
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
        amount = extract_disputed_amount(issue)
        lines.append(f"{idx}. {issue}")
        if amount is not None:
            lines.append(f"   Disputed Amount: ${amount:,.2f}")
            calculated_total += amount
        else:
            lines.append(f"   Disputed Amount: Requires manual calculation (see item detail above)")
            items_needing_manual_review += 1
        lines.append("")

    lines.append(f"Total Calculated Disputed Amount: ${calculated_total:,.2f}")
    if items_needing_manual_review > 0:
        lines.append(
            f"Note: {items_needing_manual_review} item(s) above require manual "
            f"calculation and are NOT included in the total above. Please review "
            f"each item individually."
        )
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

        # utf-8-sig (with BOM) so Windows programs like Notepad correctly
        # detect UTF-8 and render special characters properly - this is
        # a human-facing document, unlike our JSON/CSV data files, which
        # specifically needed NO BOM for Python's own readers.
        with open(filepath, "w", encoding="utf-8-sig") as f:
            f.write(letter)

        written.append(filepath)

    return written
