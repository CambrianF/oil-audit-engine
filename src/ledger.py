import os
import csv
import json
from datetime import datetime

LEDGER_PATH = "open_rental_ledger.json"
CALL_OFF_INTAKE_CSV = "call_off_intake.csv"


def load_ledger():
    """Uses utf-8-sig to safely handle a BOM marker if the file was
    written by PowerShell (Set-Content -Encoding utf8 embeds a BOM).
    Without this, json.load() silently fails on a BOM-prefixed file,
    the broad except clause swallows the error, and the ledger appears
    empty - which was causing every entry to look "new" and silently
    wiping out anything not touched in that run."""
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
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y")
    except Exception:
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
                skipped.append(f"Row {row_num}: '{date_str}' is not a valid MM/DD/YYYY date, skipped")
                continue

            result = record_call_off(serial, date_str, conf)

            if result.get("status") == "Rejected":
                rejected.append(f"Row {row_num} ({serial}): {result['reason']}")
            else:
                imported.append(f"{serial} — called off {date_str} (confirmation #{conf})")

    return {"imported": imported, "rejected": rejected, "skipped": skipped}
