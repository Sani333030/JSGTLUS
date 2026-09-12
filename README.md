# Multi-Entity Real Estate Consolidation Toolkit

Automates the core mechanics of consolidating a parent company's books with
the books of several investment vehicles it invests in -- the kind of
structure common at real estate/investment holding companies where a parent
entity holds interests in multiple single-purpose LLCs (one per deal or
property).

All data in this repo is **mock data** (fictional entity names, made-up
balances). This is an educational simulation of consolidation
*methodology* -- real fund/GAAP consolidation involves additional rules
(equity-method adjustments, minority interest, FX translation, etc.) not
modeled here.

## Problem

When a parent company invests in multiple vehicles, closing the books means:
- Making sure each entity's own trial balance actually balances
- Identifying every intercompany account (money owed between the parent and
  each vehicle, and the parent's investment/equity stake in each vehicle)
- Confirming both sides of every intercompany balance agree with each other
- Eliminating those intercompany balances so they don't double-count in the
  consolidated financial statements
- Catching it when they *don't* agree -- which happens often when one
  entity's books are updated before the other's, or when a number comes
  from an external investment partner and needs to be sanity-checked

Doing this by hand across even 3-4 entities means manually cross-referencing
account names and balances across separate trial balance exports -- easy to
miss a discrepancy until much later in the close.

## What it does

`consolidate.py` reads a trial balance CSV per entity and:

1. **Checks each entity balances on its own** (total debits = total credits)
2. **Automatically identifies intercompany accounts** by account name
   pattern (`Due from X`, `Due to X`, `Investment in X`, `Member's Equity - X`)
3. **Pairs up each intercompany relationship** across entities and checks
   whether it nets to zero
4. **Flags any pair that doesn't net to zero**, with the exact variance
   amount, so it can be investigated instead of discovered at audit
5. **Produces a consolidated trial balance** of external (non-intercompany)
   accounts only, by account type

## Time saved

Manually tracing intercompany balances across even a handful of entities
means opening each entity's trial balance separately and cross-referencing
account by account. This does it in one pass and states, in plain language,
exactly which relationship is out of balance and by how much -- turning a
"go hunt for the discrepancy" task into a "here's the discrepancy" report.

## How to run it

```bash
python consolidate.py
```

Reads all `*_trial_balance.csv` files from `sample_data/`, writes two
reports to `sample_output/`, and prints a summary to the console.

## Sample output

```
=== Entity-Level Trial Balance Check ===
Investment Vehicle Alpha LLC     Debits: 2,175,000.00  Credits: 2,175,000.00  [OK]
Investment Vehicle Bravo LLC     Debits: 1,940,000.00  Credits: 1,940,000.00  [OK]
Investment Vehicle Charlie LLC   Debits: 1,000,000.00  Credits: 1,000,000.00  [OK]
TLUS                             Debits: 1,745,000.00  Credits: 1,745,000.00  [OK]

=== Intercompany Elimination Report ===
Investment Vehicle Alpha LLC / TLUS           receivable_payable   Variance:  -5,000.00  [MISMATCH - needs follow-up]
Investment Vehicle Alpha LLC / TLUS           investment_equity    Variance:       0.00  [Eliminates cleanly]
Investment Vehicle Bravo LLC / TLUS           investment_equity    Variance:       0.00  [Eliminates cleanly]
Investment Vehicle Charlie LLC / TLUS         receivable_payable   Variance:       0.00  [Eliminates cleanly]
Investment Vehicle Charlie LLC / TLUS         investment_equity    Variance:       0.00  [Eliminates cleanly]

Total unresolved intercompany variance: -5,000.00
-> Consolidation does NOT fully tie out. See intercompany_elimination_report.csv for details.
```

The Alpha/TLUS receivable-payable pair is intentionally seeded with a
$5,000 mismatch in the sample data, to demonstrate that the tool catches
exactly this kind of discrepancy instead of letting it slide into the
consolidated numbers unnoticed.

## Tech used

Python 3, standard library only (`csv`, `re`, `collections`, `glob`) -- no
external dependencies.

## Possible next steps

- Support equity-method income pickup (parent's share of each vehicle's
  net income) rather than a flat elimination
- Add a `--period` argument to run this against a rolling close calendar

---

# Module 2: Partner-Reported Financials Variance Checker

Investment vehicles are often managed day-to-day by an external investment
partner (a GP/property manager) who periodically sends financial reports
back to the parent company. Before those numbers get booked, someone has to
sanity-check them -- does this quarter's activity look reasonable compared to
last quarter, or does something need to be questioned before it's accepted?

## Problem

Reviewing partner-prepared financials by eye across several entities and
several line items each is slow, and it's easy for a real anomaly to slip
through if nobody happens to eyeball that specific line closely enough.
Meanwhile, drafting the actual "can you explain this" email to the partner
still has to happen for every real variance found.

## What it does

`variance_checker.py` reads `partner_reported_financials.csv` (line items by
entity and period) and, for each entity:

1. Compares the two most recent reporting periods, line item by line item
2. Also computes Net Operating Income (Rental Income minus all expense
   lines) for both periods, since a variance can hide inside NOI even when
   no single line item looks alarming on its own
3. Flags anything that moves by more than **15% and more than $5,000**
   (both conditions, so a tiny account with a big percentage swing on
   trivial dollars doesn't create noise)
4. Drafts the actual clarification question an accountant would send back
   to the investment partner for every flagged item

## Time saved

Turns "manually scan every line of every partner report and do the
percentage math by hand" into a single run that hands back a short, ranked
list of exactly what needs a follow-up email -- with the email already
drafted.

## How to run it

```bash
python variance_checker.py
```

Reads `sample_data/partner_reported_financials.csv`, writes
`sample_output/variance_flags.csv` and `sample_output/clarification_requests.csv`,
and prints a summary to the console.

## Sample output

```
Investment Vehicle Alpha LLC     Repairs & Maintenance                 8,000 ->     28,000 ( 250.0%)  [FLAGGED]
Investment Vehicle Alpha LLC     Net Operating Income (computed)      89,000 ->     70,600 ( -20.7%)  [FLAGGED]
Investment Vehicle Bravo LLC     Rental Income                       140,000 ->     98,000 ( -30.0%)  [FLAGGED]
Investment Vehicle Bravo LLC     Net Operating Income (computed)     104,000 ->     61,600 ( -40.8%)  [FLAGGED]

=== Clarification Requests (4) ===
- [Investment Vehicle Alpha LLC] Can you provide detail on the increase in Repairs & Maintenance for Investment Vehicle Alpha LLC in 2025-Q2 ($8,000 in 2025-Q1 to $28,000 in 2025-Q2, a 250.0% change)?
- [Investment Vehicle Bravo LLC] Can you provide detail on the decrease in Rental Income for Investment Vehicle Bravo LLC in 2025-Q2 ($140,000 in 2025-Q1 to $98,000 in 2025-Q2, a -30.0% change)?
```

The sample data has two anomalies seeded in on purpose (Alpha's repair
costs, Bravo's rental income) -- the tool catches both, and correctly leaves
Charlie's clean quarter unflagged.

## Tech used

Python 3, standard library only (`csv`, `collections`) -- no external
dependencies.

## Possible next steps

- Compare against a budget/pro forma instead of just the prior period
- Feed flagged items into Module 1's consolidation as a "hold for review"
  status before they're booked
- Add a simple email draft export (`.eml` or plain text) per clarification
  request
