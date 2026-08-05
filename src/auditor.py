import os
import json
import pdfplumber
import re
from src.ledger import get_asset_status, parse_mmddyyyy
from src.rate_tracker import check_rate_drift
from src.rules_engine import run_vendor_rules

HISTORY_DB_PATH = "vendor_history.json"


def load_contracts():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    contract_path = os.path.join(base_dir, "contracts.json")
    if os.path.exists(contract_path):
        with open(contract_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}


def load_vendor_history():
    if os.path.exists(HISTORY_DB_PATH):
        try:
            with open(HISTORY_DB_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_vendor_history(history):
    with open(HISTORY_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


def get_vendor_risk_level(vendor_record):
    invoice_count = vendor_record["invoice_count"]
    flagged_count = vendor_record["flagged_count"]

    if invoice_count < 2:
        return "Insufficient History"

    flag_ratio = flagged_count / invoice_count

    if flag_ratio >= 0.5:
        return f"High Risk ({flag_ratio*100:.0f}% flag rate across {invoice_count} filings)"
    elif flag_ratio >= 0.25:
        return f"Moderate Risk ({flag_ratio*100:.0f}% flag rate across {invoice_count} filings)"
    else:
        return f"Low Risk ({flag_ratio*100:.0f}% flag rate across {invoice_count} filings)"


def extract_reference_fields(raw_text):
    def find(pattern):
        match = re.search(pattern, raw_text, re.IGNORECASE)
        return match.group(1).strip() if match else "N/A"

    return {
        "account_number": find(r'Account\s*#?\s*:\s*([A-Za-z0-9\-]+)'),
        "invoice_number": find(r'Invoice\s*#?\s*:\s*([A-Za-z0-9\-]+)'),
        "afe_number": find(r'AFE\s*:\s*([A-Za-z0-9\-]+)'),
        "api_number": find(r'API\s*#?\s*:\s*([A-Za-z0-9\-]+)'),
        "serial_number": find(r'Serial\s*:\s*([A-Za-z0-9\-]+)'),
        "billed_through": find(r'Billed\s+Through\s*:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})'),
        "contract_start": find(r'Contract\s+Start\s*:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})'),
    }


def has_valid_payment_terms(raw_text):
    return re.search(r'\bnet\s*\d{1,3}\b', raw_text, re.IGNORECASE) is not None


def check_ghost_rental(serial_number, billed_through_str, contract_start_str, daily_rate):
    if not serial_number or serial_number == "N/A":
        return None
    if not billed_through_str or billed_through_str == "N/A":
        return None

    asset = get_asset_status(serial_number)
    if not asset or asset.get("status") != "Called Off":
        return None

    call_off_date = parse_mmddyyyy(asset["call_off_date"])
    billed_through_date = parse_mmddyyyy(billed_through_str)
    contract_start_date = parse_mmddyyyy(contract_start_str) if contract_start_str and contract_start_str != "N/A" else None

    if not call_off_date or not billed_through_date:
        return None

    if contract_start_date and contract_start_date >= call_off_date:
        return None

    if billed_through_date > call_off_date:
        overbilled_days = (billed_through_date - call_off_date).days
        overcharge_note = ""
        if daily_rate is not None:
            overcharge_amount = overbilled_days * daily_rate
            overcharge_note = f" (${overcharge_amount:,.2f} overcharge at ${daily_rate:,.2f}/day)"
        return (
            f"Ghost Rental Detected: Unit {serial_number} was officially called off on "
            f"{asset['call_off_date']} (confirmation #{asset['confirmation_number']}), but this "
            f"invoice bills through {billed_through_str} — {overbilled_days} days past return{overcharge_note}"
        )
    return None


def audit_invoice(file_path):
    financial_issues = []
    compliance_issues = []
    raw_text = ""
    vendor_name = "Unknown Vendor"
    vendor_risk_level = "N/A"

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    raw_text += text + "\n"
    except Exception as e:
        return {
            "file": file_path,
            "status": "Failed",
            "vendor_name": "Unknown Vendor",
            "account_number": "N/A",
            "invoice_number": "N/A",
            "afe_number": "N/A",
            "api_number": "N/A",
            "financial_issues": [f"PDF Read Error: {str(e)}"],
            "compliance_issues": [],
            "vendor_risk_level": "N/A",
            "raw_text_snippet": "Could not read file."
        }

    contracts = load_contracts()
    history = load_vendor_history()
    text_lower = raw_text.lower()

    ref_fields = extract_reference_fields(raw_text)

    lines = raw_text.split("\n")
    header_line = lines[0].lower() if lines else ""
    for known_vendor in contracts.keys():
        keyword = known_vendor.split()[0].lower()
        if keyword in header_line:
            vendor_name = known_vendor
            break

    unrecognized_vendor = False

    if vendor_name in contracts:
        vendor_config = contracts[vendor_name]

        rule_issues, extracted_daily_rate = run_vendor_rules(raw_text, vendor_config)
        financial_issues.extend(rule_issues)

        features = vendor_config.get("features", [])

        if "ghost_rental" in features:
            ghost_rental_issue = check_ghost_rental(
                ref_fields["serial_number"], ref_fields["billed_through"],
                ref_fields["contract_start"], extracted_daily_rate
            )
            if ghost_rental_issue:
                financial_issues.append(ghost_rental_issue)

        if "rate_drift" in features:
            drift_issue = check_rate_drift(
                ref_fields["serial_number"], vendor_name, extracted_daily_rate,
                ref_fields["invoice_number"], ref_fields["contract_start"]
            )
            if drift_issue:
                financial_issues.append(drift_issue)

        if vendor_name not in history:
            history[vendor_name] = {"invoice_count": 0, "flagged_count": 0, "overcharge_history": []}

        vendor_record = history[vendor_name]
        vendor_record["invoice_count"] += 1

        has_real_overcharge = any(("Credit Noted" not in i) for i in financial_issues) if financial_issues else False
        if has_real_overcharge:
            vendor_record["flagged_count"] += 1

        vendor_risk_level = get_vendor_risk_level(vendor_record)

        save_vendor_history(history)

    else:
        unrecognized_vendor = True
        compliance_issues.append("Unrecognized Vendor / Missing MSA Contract File")

    if not has_valid_payment_terms(raw_text):
        compliance_issues.append("Missing standard payment terms (Net 30/60)")

    real_financial_problems = [i for i in financial_issues if "Credit Noted" not in i]
    informational_only = [i for i in financial_issues if "Credit Noted" in i]

    if unrecognized_vendor and not real_financial_problems:
        status = "Flagged"
    elif real_financial_problems or compliance_issues:
        status = "Flagged"
    elif informational_only:
        status = "Review"
    else:
        status = "Passed"

    snippet = raw_text.replace("\n", " ")[:150] + "..." if raw_text else "No text extracted."

    return {
        "file": file_path,
        "status": status,
        "vendor_name": vendor_name,
        "account_number": ref_fields["account_number"],
        "invoice_number": ref_fields["invoice_number"],
        "afe_number": ref_fields["afe_number"],
        "api_number": ref_fields["api_number"],
        "financial_issues": financial_issues if financial_issues else ["None"],
        "compliance_issues": compliance_issues if compliance_issues else ["None"],
        "vendor_risk_level": vendor_risk_level,
        "raw_text_snippet": snippet
    }
