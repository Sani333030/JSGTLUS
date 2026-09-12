# Definition of Done

This project is considered complete when:

- [x] Core functionality implements everything described in the project for both modules (Module 1: entity-level balance check, intercompany identification, pairwise elimination with mismatch detection, consolidated trial balance; Module 2: period-over-period variance detection with a dollar-and-percent threshold, computed NOI check, and drafted clarification questions)
- [x] Sample/mock data covers the intended scenarios, including one deliberate intercompany mismatch (Module 1) and two deliberate variance anomalies (Module 2)
- [x] README.md documents, for each module: what problem it solves, how it works, how to run it, and sample output
- [x] LICENSE and .gitignore are present
- [x] Both tools have actually been run end-to-end (not just code-reviewed) and output verified against the expected sample output
- [x] Pushed to its own GitHub repository

## Status: DONE (2026-09-12)

- Module 1 (`consolidate.py`): pattern-based intercompany account detection (`Due from X`, `Due to X`, `Investment in X`, `Member's Equity - X`), pairwise grouping across entities by counterparty name, net-to-zero check per pair, consolidated trial balance of external (non-intercompany) accounts by type. Sample data: parent entity (TLUS) + 3 investment vehicle LLCs, with one deliberately seeded $5,000 intercompany mismatch to demonstrate the mismatch detection actually fires.
- Module 2 (`variance_checker.py`): period-over-period line-item comparison per entity (including a computed Net Operating Income line), flagged only when a change exceeds both a percent AND a dollar threshold, with a drafted clarification question per flagged item. Sample data: 3 entities x 2 quarters, with two deliberately seeded anomalies (Alpha's repair costs, Bravo's rental income) and one entity (Charlie) left clean to confirm the tool doesn't flag a normal quarter.
- Verified end-to-end: ran both `consolidate.py` and `variance_checker.py` against the sample data and confirmed console output and all four generated CSVs match exactly what was provided.
- Repo: https://github.com/Sani333030/JSGTLUS
