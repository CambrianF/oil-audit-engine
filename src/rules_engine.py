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


def find_duration_days(raw_text):
    patterns = [
        r'days?\s+billed\s*:?\s*(\d{1,4})',
        r'billed\s+for\s+(\d{1,4})\s*(?:consecutive\s+)?days?',
        r'on\s+rent\s+for\s+(\d{1,4})\s*days?',
        r'(\d{1,4})\s*(?:consecutive\s+)?days?\s+on\s+rent',
        r'(\d{1,4})\s*(?:consecutive\s+)?days?\b',
    ]
    for p in patterns:
        m = re.search(p, raw_text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def find_daily_rate(raw_text):
    patterns = [
        r'daily\s+rate\s*\$?([0-9,]+\.\d{2})',
        r'rate\s+of\s+\$?([0-9,]+\.\d{2})',
        r'\$?([0-9,]+\.\d{2})\s*(?:/\s*day|per\s*day)',
    ]
    for p in patterns:
        m = re.search(p, raw_text, re.IGNORECASE)
        if m:
            return float(m.group(1).replace(',', ''))
    return None


def find_signed_amount(raw_text, label_pattern):
    pattern = label_pattern + r':\s*(-?)\$?([0-9,]+\.\d{2})'
    m = re.search(pattern, raw_text, re.IGNORECASE)
    if not m:
        return None
    sign = -1 if m.group(1) == '-' else 1
    amount = float(m.group(2).replace(',', ''))
    return sign * amount


EXCLUDE_KEYWORDS = [
    "subtotal", "sub-total", "sub total", "total due", "balance due",
    "prior balance", "previous balance", "tax", "amount due", "grand total"
]


def run_rate_cap_rule(raw_text, rule):
    amounts = extract_rate_lines(raw_text, rule["keywords"], EXCLUDE_KEYWORDS, first_match_only=True)
    issues = []
    for amt in amounts:
        if amt > rule["max"]:
            issues.append(
                f"{rule['label']}: Flagged amount ${amt:,.2f} exceeds contractual cap of ${rule['max']:,.2f}"
            )
    return issues, amounts[0] if amounts else None


def run_rate_roll_rule(raw_text, rule):
    days_billed = find_duration_days(raw_text)
    daily_rate = find_daily_rate(raw_text)
    issues = []
    if days_billed is not None and days_billed > rule["threshold_days"]:
        rate_note = f"${daily_rate:,.2f}/day" if daily_rate is not None else "rate not confidently extracted"
        issues.append(
            f"{rule['label']}: Billed {days_billed} days at daily rate ({rate_note}) "
            f"— exceeds {rule['threshold_days']}-day threshold; should have rolled to weekly/monthly tier"
        )
    return issues, daily_rate


def run_fee_cap_rule(raw_text, rule):
    """Checks a labeled fee against a cap. Uses 'display_label' (clean
    text) for the user-facing message, and 'label_pattern' (a regex
    fragment) only for matching - keeping these separate avoids leaking
    raw regex syntax like escaped parentheses into displayed messages."""
    amount = find_signed_amount(raw_text, rule["label_pattern"])
    display = rule.get("display_label", rule["label_pattern"])
    issues = []
    if amount is not None:
        if amount > rule["max"]:
            issues.append(
                f"{rule['issue_label']}: {display} ${amount:,.2f} exceeds contractual cap of ${rule['max']:,.2f}"
            )
        elif amount < 0:
            issues.append(
                f"{rule['credit_label']}: {display} shows a credit of ${abs(amount):,.2f} (informational, not a violation)"
            )
    return issues


def run_unauthorized_fee_rule(raw_text, rule):
    """Same display_label / label_pattern separation as run_fee_cap_rule."""
    amount = find_signed_amount(raw_text, rule["label_pattern"])
    display = rule.get("display_label", rule["label_pattern"])
    issues = []
    if amount is not None and not rule.get("opted_in", False):
        if amount > 0:
            issues.append(
                f"{rule['issue_label']}: {display} charge of ${amount:,.2f} billed despite opt-out on file"
            )
        elif amount < 0:
            issues.append(
                f"{rule['credit_label']}: {display} shows a credit of ${abs(amount):,.2f} (informational, not a violation)"
            )
    return issues


RULE_RUNNERS = {
    "rate_cap": run_rate_cap_rule,
    "rate_roll": run_rate_roll_rule,
    "fee_cap": run_fee_cap_rule,
    "unauthorized_fee": run_unauthorized_fee_rule,
}


def run_vendor_rules(raw_text, vendor_config):
    issues = []
    extracted_daily_rate = None

    for rule in vendor_config.get("rules", []):
        rule_type = rule.get("type")
        runner = RULE_RUNNERS.get(rule_type)
        if not runner:
            continue

        if rule_type in ("rate_cap", "rate_roll"):
            rule_issues, rate = runner(raw_text, rule)
            issues.extend(rule_issues)
            if rate is not None:
                extracted_daily_rate = rate
        else:
            rule_issues = runner(raw_text, rule)
            issues.extend(rule_issues)

    benchmark = vendor_config.get("benchmark", 0.0)
    if benchmark > 0:
        benchmark_keywords = vendor_config.get("benchmark_keywords", [])
        benchmark_amounts = extract_rate_lines(raw_text, benchmark_keywords, EXCLUDE_KEYWORDS, first_match_only=True)
        for amt in benchmark_amounts:
            pct_over = ((amt - benchmark) / benchmark) * 100
            if pct_over >= 2.0:
                issues.append(
                    f"Proprietary Benchmarking Alert: Spot rate ${amt:,.2f} exceeds regional market index (${benchmark:,.2f}) by {pct_over:.1f}%"
                )

    return issues, extracted_daily_rate
