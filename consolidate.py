"""
Multi-Entity Consolidation Tool
--------------------------------
Consolidates trial balances across a parent company (TLUS) and multiple
investment vehicles it invests in, automatically identifying and
eliminating intercompany balances, and flagging any intercompany pair
that doesn't net to zero (a sign of a data entry error, timing
difference, or a partner-reported number that needs to be questioned).

This models the core mechanics of fund/real-estate consolidation
accounting. It is an educational simulation built on mock data, not a
production consolidation engine -- real fund accounting involves
additional rules (equity-method adjustments, minority interest,
FX translation, etc.) not modeled here.

Input:
    sample_data/tlus_trial_balance.csv
    sample_data/investment_vehicle_alpha_trial_balance.csv
    sample_data/investment_vehicle_bravo_trial_balance.csv
    sample_data/investment_vehicle_charlie_trial_balance.csv

Output:
    sample_output/consolidated_trial_balance.csv
    sample_output/intercompany_elimination_report.csv

Usage:
    python consolidate.py
"""

import csv
import glob
import os
import re
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sample_output")

# Patterns used to recognize intercompany accounts and pull out which
# counterparty entity each line refers to.
INTERCOMPANY_PATTERNS = [
    (re.compile(r"^Due from (.+)$"), "due_from", "receivable_payable"),
    (re.compile(r"^Due to (.+)$"), "due_to", "receivable_payable"),
    (re.compile(r"^Investment in (.+)$"), "investment", "investment_equity"),
    (re.compile(r"^Member's Equity - (.+)$"), "member_equity", "investment_equity"),
]


def load_trial_balances():
    rows = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*_trial_balance.csv"))):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["debit"] = float(row["debit"])
                row["credit"] = float(row["credit"])
                row["net"] = row["debit"] - row["credit"]
                rows.append(row)
    return rows


def check_entity_balances(rows):
    """Each entity's trial balance should have total debits == total credits."""
    totals = defaultdict(lambda: {"debit": 0.0, "credit": 0.0})
    for row in rows:
        totals[row["entity"]]["debit"] += row["debit"]
        totals[row["entity"]]["credit"] += row["credit"]

    results = []
    for entity, t in sorted(totals.items()):
        diff = round(t["debit"] - t["credit"], 2)
        results.append({
            "entity": entity,
            "total_debit": t["debit"],
            "total_credit": t["credit"],
            "in_balance": diff == 0,
            "difference": diff,
        })
    return results


def classify_intercompany(rows):
    """Tag each row as intercompany or not, and extract its counterparty/category."""
    for row in rows:
        row["is_intercompany"] = False
        row["counterparty"] = None
        row["ic_category"] = None
        for pattern, label, category in INTERCOMPANY_PATTERNS:
            m = pattern.match(row["account_name"])
            if m:
                row["is_intercompany"] = True
                row["counterparty"] = m.group(1).strip()
                row["ic_category"] = category
                break
    return rows


def build_elimination_report(rows):
    """
    Group intercompany lines into pairs (e.g. TLUS 'Due from Alpha' <-> Alpha
    'Due to TLUS') and check whether each pair nets to zero. A non-zero net
    means the two entities disagree on the balance and it needs follow-up
    before consolidation can be finalized.
    """
    pairs = defaultdict(list)
    for row in rows:
        if not row["is_intercompany"]:
            continue
        key = (frozenset([row["entity"], row["counterparty"]]), row["ic_category"])
        pairs[key].append(row)

    report = []
    for (entities, category), lines in sorted(pairs.items(), key=lambda x: sorted(x[0][0])):
        net_total = sum(l["net"] for l in lines)
        status = "Eliminates cleanly" if round(net_total, 2) == 0 else "MISMATCH - needs follow-up"
        report.append({
            "entities": " / ".join(sorted(entities)),
            "category": category,
            "line_items": "; ".join(f"{l['entity']}: {l['account_name']} ({l['net']:,.2f})" for l in lines),
            "net_variance": round(net_total, 2),
            "status": status,
        })
    return report


def build_consolidated_trial_balance(rows):
    """Sum all non-intercompany accounts by account_type across every entity."""
    totals = defaultdict(float)
    for row in rows:
        if row["is_intercompany"]:
            continue
        totals[row["account_type"]] += row["net"]

    return [{"account_type": k, "net_balance": round(v, 2)} for k, v in sorted(totals.items())]


def main():
    rows = load_trial_balances()
    rows = classify_intercompany(rows)

    entity_checks = check_entity_balances(rows)
    elimination_report = build_elimination_report(rows)
    consolidated = build_consolidated_trial_balance(rows)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(os.path.join(OUTPUT_DIR, "intercompany_elimination_report.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["entities", "category", "line_items", "net_variance", "status"])
        writer.writeheader()
        writer.writerows(elimination_report)

    with open(os.path.join(OUTPUT_DIR, "consolidated_trial_balance.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["account_type", "net_balance"])
        writer.writeheader()
        writer.writerows(consolidated)

    # Console summary
    print("=== Entity-Level Trial Balance Check ===")
    for r in entity_checks:
        flag = "OK" if r["in_balance"] else f"OUT OF BALANCE by {r['difference']:,.2f}"
        print(f"{r['entity']:<32} Debits: {r['total_debit']:>12,.2f}  Credits: {r['total_credit']:>12,.2f}  [{flag}]")

    print("\n=== Intercompany Elimination Report ===")
    for r in elimination_report:
        print(f"{r['entities']:<45} {r['category']:<20} Variance: {r['net_variance']:>10,.2f}  [{r['status']}]")

    print("\n=== Consolidated Trial Balance (external accounts only) ===")
    for r in consolidated:
        print(f"{r['account_type']:<12} {r['net_balance']:>15,.2f}")

    total_variance = sum(r["net_variance"] for r in elimination_report)
    print(f"\nTotal unresolved intercompany variance: {total_variance:,.2f}")
    if total_variance != 0:
        print("-> Consolidation does NOT fully tie out. See intercompany_elimination_report.csv for details.")
    else:
        print("-> All intercompany balances eliminate cleanly.")


if __name__ == "__main__":
    main()
