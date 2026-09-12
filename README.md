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

- Add a variance-checker module that flags unexpected period-over-period
  swings in each investment vehicle's partner-reported financials
  (mirrors reviewing GP-prepared reports before they're booked)
- Support equity-method income pickup (parent's share of each vehicle's
  net income) rather than a flat elimination
- Add a `--period` argument to run this against a rolling close calendar
