import os
import json
from datetime import datetime

RATE_HISTORY_PATH = "rate_history.json"


def parse_mmddyyyy(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y")
    except Exception:
        return None


def load_rate_history():
    """Uses utf-8-sig to safely handle a BOM marker, same fix applied
    to the ledger loader - avoids the same silent-empty-file failure."""
    if os.path.exists(RATE_HISTORY_PATH):
        try:
            with open(RATE_HISTORY_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_rate_history(history):
    with open(RATE_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


def check_rate_drift(serial_number, vendor_name, current_rate, invoice_number, invoice_date_str):
    """Compares the current invoice's daily rate for a given unit against
    the most recent PRIOR-DATED rate on file for that same unit. Invoices
    are ordered by their own billing date, not by processing order - an
    invoice that is chronologically OLDER than what's already on file is
    never used to update the comparison point, the same protection
    already applied to the ghost-rental ledger. Without this, reprocessing
    invoices out of order could silently corrupt the comparison baseline
    and produce false or missed drift flags."""
    if not serial_number or serial_number == "N/A" or current_rate is None:
        return None

    current_date = parse_mmddyyyy(invoice_date_str) if invoice_date_str and invoice_date_str != "N/A" else None

    history = load_rate_history()
    key = f"{vendor_name}::{serial_number}"
    previous = history.get(key)

    issue = None

    if previous:
        previous_rate = previous.get("rate")
        previous_invoice = previous.get("invoice_number")
        previous_date_str = previous.get("invoice_date")
        previous_date = parse_mmddyyyy(previous_date_str) if previous_date_str else None

        # If we can't establish reliable dates on both sides, fall back
        # to comparing anyway (better than skipping the check entirely)
        # but never let an older-dated invoice overwrite a newer one.
        is_older = (current_date and previous_date and current_date < previous_date)

        if not is_older and previous_rate is not None and current_rate > previous_rate:
            increase = current_rate - previous_rate
            pct_increase = (increase / previous_rate) * 100
            issue = (
                f"Rate-Card Drift: Unit {serial_number} billed at ${current_rate:,.2f}/day "
                f"on this invoice, up from ${previous_rate:,.2f}/day on a prior invoice "
                f"(#{previous_invoice}) — a ${increase:,.2f}/day ({pct_increase:.1f}%) increase "
                f"with no renegotiation on file"
            )

        if is_older:
            # Older invoice being processed after a newer one is already
            # on file - don't overwrite the comparison point with stale data.
            return None

    history[key] = {"rate": current_rate, "invoice_number": invoice_number, "invoice_date": invoice_date_str}
    save_rate_history(history)

    return issue
