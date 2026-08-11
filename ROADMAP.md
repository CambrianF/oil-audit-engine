# Roadmap — From Prototype to Full Vision

Tracking progress against the original product vision (see founder's notes). Status reflects what's actually built and tested, not what's planned.

## Done
- [x] Rate-cap / rate-roll / fee-cap checking (3+ vendors, config-driven)
- [x] Ghost rental / open-rental ledger detection (ledger with CSV intake, per-unit accurate)
- [x] Rate-card drift detection (flags quiet rate hikes between invoices)
- [x] Vendor risk history tracking (separate from per-invoice status)
- [x] Config-driven vendor onboarding (new vendor = JSON entry, not code)
- [x] Excel report output (Executive Summary + Detailed Audit Log)
- [x] Automated dispute / credit-memo letter generation (one plain-text letter per genuinely flagged invoice, citing exact issues and dollar amounts; correctly skips Failed/informational-only invoices)

## Blocked — needs real-world data
- [ ] Contract parsing (reading real MSAs instead of hand-typed JSON rules)
- [ ] Tax exemption checking (needs real exemption certificate data)
- [ ] AFE-level budget tracking (needs a real AFE document to design against)

## Blocked — needs infrastructure/access
- [ ] ERP integration (Quorum, WolfePak, PakEnergy)
- [ ] Payment splitting / remittance advice automation (touches real payment systems)
- [ ] OCR for scanned/image-based invoices (documented, deferred until a real scanned invoice is available)
- [ ] Monthly automated cadence / unattended scheduling

## Notes
Everything in "Done" has been stress-tested and has real bugs found/fixed documented in CASE_STUDY.md, not just built and assumed working.
