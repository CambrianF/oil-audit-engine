import os
import json

RATE_HISTORY_PATH = "rate_history.json"


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


def check_rate_drift(serial_number, vendor_name, current_rate, invoice_number):
    """Compares the current invoice's daily rate for a given unit against
    the last recorded rate for that same unit. If the rate increased with
    no renegotiation on file, flags it as rate-card drift. Always updates
    the history with the current rate afterward, regardless of outcome,
    so the next invoice compares against the most recent one."""
    if not serial_number or serial_number == "N/A" or current_rate is None:
        return None

    history = load_rate_history()
    key = f"{vendor_name}::{serial_number}"
    previous = history.get(key)

    issue = None
    if previous:
        previous_rate = previous.get("rate")
        previous_invoice = previous.get("invoice_number")
        if previous_rate is not None and current_rate > previous_rate:
            increase = current_rate - previous_rate
            pct_increase = (increase / previous_rate) * 100
            issue = (
                f"Rate-Card Drift: Unit {serial_number} billed at ${current_rate:,.2f}/day "
                f"on this invoice, up from ${previous_rate:,.2f}/day on a prior invoice "
                f"(#{previous_invoice}) — a ${increase:,.2f}/day ({pct_increase:.1f}%) increase "
                f"with no renegotiation on file"
            )

    history[key] = {"rate": current_rate, "invoice_number": invoice_number}
    save_rate_history(history)

    return issue
