import os
import csv
import json
from datetime import datetime

LEDGER_PATH = "open_rental_ledger.json"
CALL_OFF_INTAKE_CSV = "call_off_intake.csv"


def load_ledger():
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_ledger(ledger):
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=4)


def record_call_off(serial_number, call_off_date_str, confirmation_number):
    """Marks a unit as officially called off (returned) as of a given date."""
    ledger = load_ledger()
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


def parse_mmddyyyy(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y")
    except Exception:
        return None


def ensure_intake_template_exists():
    """Creates a starter CSV file for AP staff to fill in, if one doesn't
    already exist. This is the actual intake mechanism - no Python
    knowledge required, just editing a spreadsheet."""
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
    """Reads call_off_intake.csv and records every row into the ledger.
    Skips the example row and any row missing required fields. Uses
    utf-8-sig to safely handle a BOM marker if one is present (common
    when the CSV was saved by PowerShell, Excel, or Notepad on Windows) -
    without this, the first column header can silently fail to match."""
    if not ensure_intake_template_exists():
        return []

    imported = []
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

            record_call_off(serial, date_str, conf)
            imported.append(f"{serial} — called off {date_str} (confirmation #{conf})")

    return {"imported": imported, "skipped": skipped}
