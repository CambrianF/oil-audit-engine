from src.ledger import record_call_off

if __name__ == "__main__":
    # Simulate: this unit was officially called off (returned) on July 10, 2026,
    # but we're about to test an invoice that bills through July 22 for it -
    # a classic ghost rental scenario from the founder's notes
    entry = record_call_off(
        serial_number="GEN-77291",
        call_off_date_str="07/10/2026",
        confirmation_number="CALLOFF-88213"
    )
    print(f"Recorded call-off: {entry}")
