import re


def extract_rate_lines(raw_text, include_keywords, exclude_keywords, first_match_only=False):
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


def find_all_duration_days(raw_text):
    patterns = [
        r'days?\s+billed\s*:?\s*(\d{1,4})',
        r'billed\s+for\s+(\d{1,4})\s*(?:consecutive\s+)?days?',
        r'on\s+rent\s+for\s+(\d{1,4})\s*days?',
        r'(\d{1,4})\s*(?:consecutive\s+)?days?\s+on\s+rent',
    ]
    results = []
    for p in patterns:
        for m in re.finditer(p, raw_text, re.IGNORECASE):
            results.append(int(m.group(1)))
    if results:
        return results
    fallback = re.findall(r'(\d{1,4})\s*(?:consecutive\s+)?days?\b', raw_text, re.IGNORECASE)
    return [int(x) for x in fallback]


def find_all_daily_rates(raw_text):
    patterns = [
        r'daily\s+rate\s*\$?([0-9,]+\.\d{2})',
        r'rate\s+of\s+\$?([0-9,]+\.\d{2})',
        r'\$?([0-9,]+\.\d{2})\s*(?:/\s*day|per\s*day)',
    ]
    results = []
    for p in patterns:
        for m in re.finditer(p, raw_text, re.IGNORECASE):
            results.append(float(m.group(1).replace(',', '')))
    return results


def find_all_signed_amounts(raw_text, label_pattern):
    pattern = label_pattern + r':\s*(-?)\$?([0-9,]+\.\d{2})'
    results = []
    for m in re.finditer(pattern, raw_text, re.IGNORECASE):
        sign = -1 if m.group(1) == '-' else 1
        results.append(sign * float(m.group(2).replace(',', '')))
    return results


EXCLUDE_KEYWORDS = [
    "subtotal", "sub-total", "sub total", "total due", "balance due",
    "prior balance", "previous balance", "tax", "amount due", "grand total"
]


def _unit_prefix(serial_number):
    """Returns 'Unit X: ' if a serial number is known for this block,
    otherwise an empty string - so single-unit invoices (no serial field
    at all) read exactly as before, with no confusing 'Unit None:' text."""
    if serial_number:
        return f"Unit {serial_number}: "
    return ""


def run_rate_cap_rule(raw_text, rule, serial_number=None):
    amounts = extract_rate_lines(raw_text, rule["keywords"], EXCLUDE_KEYWORDS, first_match_only=True)
    issues = []
    prefix = _unit_prefix(serial_number)
    for amt in amounts:
        if amt > rule["max"]:
            issues.append(
                f"{prefix}{rule['label']}: Flagged amount ${amt:,.2f} exceeds contractual cap of ${rule['max']:,.2f}"
            )
    return issues, amounts[0] if amounts else None


def run_rate_roll_rule(raw_text, rule, serial_number=None):
    days_list = find_all_duration_days(raw_text)
    rates_list = find_all_daily_rates(raw_text)
    issues = []
    prefix = _unit_prefix(serial_number)
    for i, days_billed in enumerate(days_list):
        if days_billed > rule["threshold_days"]:
            daily_rate = rates_list[i] if i < len(rates_list) else None
            rate_note = f"${daily_rate:,.2f}/day" if daily_rate is not None else "rate not confidently extracted"
            issues.append(
                f"{prefix}{rule['label']}: Billed {days_billed} days at daily rate ({rate_note}) "
                f"— exceeds {rule['threshold_days']}-day threshold; should have rolled to weekly/monthly tier"
            )
    primary_rate = rates_list[0] if rates_list else None
    return issues, primary_rate


def run_fee_cap_rule(raw_text, rule, serial_number=None):
    amounts = find_all_signed_amounts(raw_text, rule["label_pattern"])
    display = rule.get("display_label", rule["label_pattern"])
    prefix = _unit_prefix(serial_number)
    issues = []
    for amount in amounts:
        if amount > rule["max"]:
            issues.append(
                f"{prefix}{rule['issue_label']}: {display} ${amount:,.2f} exceeds contractual cap of ${rule['max']:,.2f}"
            )
        elif amount < 0:
            issues.append(
                f"{prefix}{rule['credit_label']}: {display} shows a credit of ${abs(amount):,.2f} (informational, not a violation)"
            )
    return issues


def run_unauthorized_fee_rule(raw_text, rule, serial_number=None):
    amounts = find_all_signed_amounts(raw_text, rule["label_pattern"])
    display = rule.get("display_label", rule["label_pattern"])
    prefix = _unit_prefix(serial_number)
    issues = []
    if not rule.get("opted_in", False):
        for amount in amounts:
            if amount > 0:
                issues.append(
                    f"{prefix}{rule['issue_label']}: {display} charge of ${amount:,.2f} billed despite opt-out on file"
                )
            elif amount < 0:
                issues.append(
                    f"{prefix}{rule['credit_label']}: {display} shows a credit of ${abs(amount):,.2f} (informational, not a violation)"
                )
    return issues


RULE_RUNNERS = {
    "rate_cap": run_rate_cap_rule,
    "rate_roll": run_rate_roll_rule,
    "fee_cap": run_fee_cap_rule,
    "unauthorized_fee": run_unauthorized_fee_rule,
}


def run_vendor_rules(raw_text, vendor_config, serial_number=None):
    """Runs every rule defined for a vendor's contract config against the
    given text - which may be the whole invoice (single-unit vendors) or
    a single unit's text block (multi-unit vendors). When serial_number
    is provided, every issue produced is tagged with 'Unit X: ' so a
    multi-unit invoice's dispute letter and audit log can never confuse
    which piece of equipment a fee or violation belongs to."""
    issues = []
    extracted_daily_rate = None

    for rule in vendor_config.get("rules", []):
        rule_type = rule.get("type")
        runner = RULE_RUNNERS.get(rule_type)
        if not runner:
            continue

        if rule_type in ("rate_cap", "rate_roll"):
            rule_issues, rate = runner(raw_text, rule, serial_number=serial_number)
            issues.extend(rule_issues)
            if rate is not None:
                extracted_daily_rate = rate
        else:
            rule_issues = runner(raw_text, rule, serial_number=serial_number)
            issues.extend(rule_issues)

    benchmark = vendor_config.get("benchmark", 0.0)
    if benchmark > 0:
        benchmark_keywords = vendor_config.get("benchmark_keywords", [])
        benchmark_amounts = extract_rate_lines(raw_text, benchmark_keywords, EXCLUDE_KEYWORDS, first_match_only=True)
        prefix = _unit_prefix(serial_number)
        for amt in benchmark_amounts:
            pct_over = ((amt - benchmark) / benchmark) * 100
            if pct_over >= 2.0:
                issues.append(
                    f"{prefix}Proprietary Benchmarking Alert: Spot rate ${amt:,.2f} exceeds regional market index (${benchmark:,.2f}) by {pct_over:.1f}%"
                )

    return issues, extracted_daily_rate
