from src.ledger import record_call_off

if __name__ == "__main__":
    # Unit called off on 07/15/2026 - we'll test an invoice billing
    # THROUGH exactly that date, which should NOT be a ghost rental
    entry = record_call_off(
        serial_number="LT-99500",
        call_off_date_str="07/15/2026",
        confirmation_number="CALLOFF-99500"
    )
    print(f"Recorded call-off: {entry}")
