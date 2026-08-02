import os
import json
import pdfplumber
import re
from datetime import datetime

HISTORY_DB_PATH = "vendor_history.json"

EXCLUDE_KEYWORDS = [
    "subtotal", "sub-total", "sub total", "total due", "balance due",
    "prior balance", "previous balance", "tax", "amount due", "grand total"
]


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
            with open(HISTORY_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_vendor_history(history):
    with open(HISTORY_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


def extract_rate_lines(raw_text, include_keywords, exclude_keywords, first_match_only=False):
    """Only pulls dollar amounts from lines that match rate context and
    do NOT match exclusion context (subtotal/tax/balance/etc).
    If first_match_only=True, only takes the first dollar amount on the
    line (the Rate column), ignoring the Amount column that follows it."""
    results = []
    for line in raw_text.split("\n"):
        line_lower = line.lower()
        if any(bad in line_lower for bad in exclude_keywords):
            continue
        if not any(good in line_lower for good in include_keywords):
            continue
        amounts = re.findall(r'[\$]?([0-9,]+\.[0-9]{2})', line)
        if not amounts:
            continue
        if first_match_only:
            results.append(float(amounts[0].replace(',', '')))
        else:
            for amt in amounts:
                results.append(float(amt.replace(',', '')))
    return results


def audit_invoice(file_path):
    issues = []
    raw_text = ""
    vendor_name = "Unknown Vendor"

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
            "issues": [f"PDF Read Error: {str(e)}"],
            "raw_text_snippet": "Could not read file."
        }

    # --- TEMPORARY DEBUG: prints exact extracted text so we can see real line wording ---
    print(f"\n--- RAW TEXT for {file_path} ---\n{raw_text}\n--- END ---\n")

    contracts = load_contracts()
    history = load_vendor_history()
    text_lower = raw_text.lower()

    for known_vendor in contracts.keys():
        keyword = known_vendor.split()[0].lower()
        if keyword in text_lower:
            vendor_name = known_vendor
            break

    if vendor_name in contracts:
        rules = contracts[vendor_name]

        if "Apex" in vendor_name:
            max_rate = rules.get("max_day_rate", 0.0)
            rate_amounts = extract_rate_lines(
                raw_text, ["day rate", "daily rate", "rig rate"], EXCLUDE_KEYWORDS,
                first_match_only=True
            )
            for amt in rate_amounts:
                if amt > max_rate:
                    issues.append(
                        f"Day Rate Variance: Flagged amount ${amt:,.2f} exceeds contractual cap of ${max_rate:,.2f}"
                    )

        elif "Pioneer" in vendor_name:
            max_haul = rules.get("max_haul_rate", 0.0)
            rate_amounts = extract_rate_lines(
                raw_text, ["haul rate", "hauling rate", "transport rate"], EXCLUDE_KEYWORDS,
                first_match_only=True
            )
            for amt in rate_amounts:
                if amt > max_haul:
                    issues.append(
                        f"Hauling Rate Variance: Flagged amount ${amt:,.2f} exceeds cap of ${max_haul:,.2f}"
                    )

        # Regional benchmarking
        regional_benchmarks = {
            "Apex Drilling & Rig Services": 25000.0,
            "Pioneer Fluid Logistics": 1400.0
        }
        benchmark = regional_benchmarks.get(vendor_name, 0.0)
        if benchmark > 0:
            benchmark_amounts = extract_rate_lines(
                raw_text,
                ["day rate", "daily rate", "rig rate", "haul rate", "hauling rate", "transport rate"],
                EXCLUDE_KEYWORDS,
                first_match_only=True
            )
            for amt in benchmark_amounts:
                pct_over = ((amt - benchmark) / benchmark) * 100
                if pct_over >= 2.0:
                    issues.append(
                        f"Proprietary Benchmarking Alert: Spot rate ${amt:,.2f} exceeds regional market index (${benchmark:,.2f}) by {pct_over:.1f}%"
                    )

        # Vendor history / high-risk tracking
        if vendor_name not in history:
            history[vendor_name] = {"invoice_count": 0, "flagged_count": 0, "overcharge_history": []}

        vendor_record = history[vendor_name]
        vendor_record["invoice_count"] += 1

        has_current_overcharge = any("Variance" in i or "Benchmarking" in i for i in issues)
        if has_current_overcharge:
            vendor_record["flagged_count"] += 1

        flag_ratio = vendor_record["flagged_count"] / max(vendor_record["invoice_count"], 1)
        if vendor_record["invoice_count"] >= 2 and flag_ratio >= 0.5:
            issues.append(
                f"High-Risk Vendor Flag: {vendor_name} exhibits systematic overcharging habits "
                f"({flag_ratio*100:.0f}% historical flag rate across {vendor_record['invoice_count']} filings)"
            )

        save_vendor_history(history)

    else:
        issues.append("Unrecognized Vendor / Missing MSA Contract File")

    if "net" not in text_lower:
        issues.append("Missing standard payment terms (Net 30/60)")

    real_issues = [i for i in issues if "Unrecognized Vendor" not in i]

    status = "Passed" if len(real_issues) == 0 else "Flagged"
    if not real_issues and "Unrecognized Vendor" in issues:
        real_issues = ["Unrecognized Vendor (Manual Review Required)"]
        status = "Flagged"

    snippet = raw_text.replace("\n", " ")[:150] + "..." if raw_text else "No text extracted."

    return {
        "file": file_path,
        "status": status,
        "issues": real_issues if real_issues else ["None"],
        "raw_text_snippet": snippet
    }