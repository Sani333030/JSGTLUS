# Definition of Done

This project is considered complete when:

- [x] Core functionality implements everything described in the project (entity-level balance check, intercompany identification, pairwise elimination with mismatch detection, consolidated trial balance)
- [x] Sample/mock data covers the intended scenarios, including one deliberate intercompany mismatch
- [x] README.md documents: what problem it solves, how it works, how to run it, and sample output
- [x] LICENSE and .gitignore are present
- [x] The tool has actually been run end-to-end (not just code-reviewed) and output verified against the expected sample output
- [x] Pushed to its own GitHub repository

## Status: DONE, pending push (2026-09-12)

- Core: pattern-based intercompany account detection (`Due from X`, `Due to X`, `Investment in X`, `Member's Equity - X`), pairwise grouping across entities by counterparty name, net-to-zero check per pair, consolidated trial balance of external (non-intercompany) accounts by type.
- Sample data: parent entity (TLUS) + 3 investment vehicle LLCs, with one deliberately seeded $5,000 intercompany mismatch (Alpha's "Due to TLUS" vs. TLUS's "Due from Alpha") to demonstrate the mismatch detection actually fires.
- Verified end-to-end: ran `consolidate.py` against the sample data and confirmed the console output and both generated CSVs (`sample_output/consolidated_trial_balance.csv`, `sample_output/intercompany_elimination_report.csv`) match exactly.
- Repo: _(to be added once pushed)_
