# Oil & Gas Invoice Audit Engine

A Python tool that ingests oilfield vendor invoices (PDF), checks them against contract rules, and flags overcharges, unauthorized fees, and ghost rentals — built as a proof-of-concept for an AI-powered AP reconciliation product for mid-market independent oil and gas operators.

**Status: actively developed proof-of-concept.** Tested extensively against synthetic invoices; not yet validated against real vendor documents. See [CASE_STUDY.md](CASE_STUDY.md) for a detailed walkthrough of the testing process and a real bug I found and fixed.

## What it does

- Extracts vendor, invoice, AFE, and API reference numbers from PDF invoices
- Checks day rates, haul rates, and fees against per-vendor contract rules
- Detects "rate-roll failures" — rentals that should have converted to a cheaper weekly/monthly rate but didn't
- Detects unauthorized fees (e.g. a damage waiver charged despite an opt-out on file)
- Cross-references invoices against an open-rental ledger to catch **ghost rentals** — equipment billed after it was officially returned
- Tracks vendor-level risk history separately from invoice-level status
- Outputs a formatted, color-coded Excel report (Executive Summary + Detailed Audit Log)

## Three-tier status system

Every invoice is classified as:
- **Passed** — nothing to see
- **Review** — nothing wrong, but worth a glance (e.g. a legitimate credit)
- **Flagged** — a real problem (overcharge, unauthorized fee, or compliance gap)

This distinction was a deliberate design decision — a credit shouldn't be visually indistinguishable from a real overcharge, but it's also not nothing.

## Architecture

- `main.py` — orchestrates the audit run, builds the Excel workbook
- `src/auditor.py` — extraction and rule-checking logic
- `src/ledger.py` — open-rental ledger for ghost-rental detection, with CSV-based intake (no coding required to use it — AP staff fill in a spreadsheet)
- `contracts.json` — example/synthetic per-vendor contract rules (not real negotiated rates)
- `data/sample_invoices/` — synthetic test invoices used for stress testing

## Vendors currently supported

1. **Apex Drilling & Rig Services** — day rate cap, regional benchmark check
2. **Pioneer Fluid Logistics** — haul rate cap
3. **United Rentals Inc.** — rate-roll threshold, Environmental Service Charge cap, unauthorized RPP fee detection, ghost rental detection

## Extraction approach

Line-item extraction uses proximity-based keyword matching rather than rigid exact-phrase regex, so it can correctly parse the same fact stated in different ways (e.g. "Rental Days Billed: 45 @ Daily Rate $175.00/day" vs. "been on rent for 45 days at a rate of $175.00 per day"). This was a direct fix for a real bug found during testing — see the case study for details.

## Known limitations

- Not yet tested against real vendor invoices — only synthetic data generated for testing
- New vendors currently require hand-written rule logic; no general contract-parsing system yet
- OCR (for scanned/image-based invoices) not yet implemented
- Proximity-based extraction, while more robust than exact-phrase matching, can still be confused by genuinely ambiguous documents (e.g. multiple unrelated day-counts in the same invoice)

## Setup
Drop PDF invoices in `data/sample_invoices/` before running.

## Ghost rental / call-off tracking

To use ghost-rental detection, fill in `call_off_intake.csv` (auto-generated on first run) with unit serial numbers, call-off dates, and confirmation numbers, then run:
