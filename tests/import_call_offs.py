from src.ledger import import_call_offs_from_csv

if __name__ == "__main__":
    result = import_call_offs_from_csv()
    if result:
        print(f"\nImported {len(result['imported'])} call-off confirmation(s):")
        for line in result["imported"]:
            print(f"  - {line}")
        if result["skipped"]:
            print(f"\nSkipped {len(result['skipped'])} row(s):")
            for line in result["skipped"]:
                print(f"  - {line}")
