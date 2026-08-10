import os
import csv
import json
from datetime import datetime

LEDGER_PATH = "open_rental_ledger.json"
CALL_OFF_INTAKE_CSV = "call_off_intake.csv"


def load_ledger():
    """Uses utf-8-sig to safely handle a BOM marker if the file was
    written by PowerShell (Set-Content -Encoding utf8 embeds a BOM)."""
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_ledger(ledger):
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=4)


def parse_mmddyyyy(date_str):
    """Tries several common date formats, not just MM/DD/YYYY, since
    different vendor export systems format dates differently (e.g. ISO
    YYYY-MM-DD). Returns None only if none of the known formats match -
    at that point the caller correctly skips the check rather than
    guessing, but a supported format never silently gets missed just
    because it wasn't the one format originally assumed."""
    if not date_str:
        return None

    date_str = date_str.strip()

    formats_to_try = [
        "%m/%d/%Y",   # 07/15/2026 - original assumed format
        "%Y-%m-%d",   # 2026-07-15 - ISO format
        "%m-%d-%Y",   # 07-15-2026 - dashes instead of slashes
        "%d/%m/%Y",   # 15/07/2026 - day-first (some regions/vendors)
        "%B %d, %Y",  # July 15, 2026 - written out
        "%b %d, %Y",  # Jul 15, 2026 - abbreviated
    ]

    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def record_call_off(serial_number, call_off_date_str, confirmation_number):
    """Marks a unit as officially called off (returned) as of a given date.
    If the unit already has a call-off recorded, the new entry is only
    applied if its date is the same or more recent - an older date is
    rejected rather than silently overwriting good data."""
    ledger = load_ledger()
    new_date = parse_mmddyyyy(call_off_date_str)

    existing = ledger.get(serial_number)
    if existing:
        existing_date = parse_mmddyyyy(existing.get("call_off_date", ""))
        if existing_date and new_date and new_date < existing_date:
            return {
                "status": "Rejected",
                "reason": (
                    f"New call-off date {call_off_date_str} is older than the "
                    f"existing recorded date {existing['call_off_date']} for this unit. "
                    f"Existing entry was kept unchanged."
                ),
                "kept": existing
            }

    ledger[serial_number] = {
        "status": "Called Off",
        "call_off_date": call_off_date_str,
        "confirmation_number": confirmation_number
    }
    save_ledger(ledger)
    return ledger[serial_number]


def get_asset_status(serial_number):
    ledger = load_ledger()
    return ledger.get(serial_number)


def ensure_intake_template_exists():
    if not os.path.exists(CALL_OFF_INTAKE_CSV):
        with open(CALL_OFF_INTAKE_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["serial_number", "call_off_date", "confirmation_number"])
            writer.writerow(["EXAMPLE-UNIT-001", "07/15/2026", "CALLOFF-EXAMPLE"])
        print(f"Created {CALL_OFF_INTAKE_CSV} — open it, replace the example row "
              f"with real call-off confirmations, one per line, then run this "
              f"script again to load them into the ledger.")
        return False
    return True


def import_call_offs_from_csv():
    if not ensure_intake_template_exists():
        return []

    imported = []
    rejected = []
    skipped = []

    with open(CALL_OFF_INTAKE_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            serial = (row.get("serial_number") or "").strip()
            date_str = (row.get("call_off_date") or "").strip()
            conf = (row.get("confirmation_number") or "").strip()

            if serial == "EXAMPLE-UNIT-001":
                continue

            if not serial or not date_str or not conf:
                skipped.append(f"Row {row_num}: missing required field(s), skipped")
                continue

            if not parse_mmddyyyy(date_str):
                skipped.append(f"Row {row_num}: '{date_str}' is not a recognized date format, skipped")
                continue

            result = record_call_off(serial, date_str, conf)

            if result.get("status") == "Rejected":
                rejected.append(f"Row {row_num} ({serial}): {result['reason']}")
            else:
                imported.append(f"{serial} — called off {date_str} (confirmation #{conf})")

    return {"imported": imported, "rejected": rejected, "skipped": skipped}
