"""
Partner-Reported Financials Variance Checker
----------------------------------------------
Investment vehicles are often managed day-to-day by an external investment
partner (a GP/property manager), who periodically sends financial reports
back to the parent company (TLUS). Before those numbers get booked, someone
has to sanity-check them: does this quarter's activity look reasonable
compared to last quarter, or does something need to be questioned before
it's accepted?

This tool automates that first-pass review: it compares each investment
vehicle's most recent two reporting periods, line item by line item,
flags anything that moved more than a set threshold, and drafts the
clarification question an accountant would send back to the partner.

This is an educational simulation on mock data - it does not replace
judgment about what's actually driving a real variance, but it replaces
the manual "scan every line of every report and do the math by hand" step.

Input:
    sample_data/partner_reported_financials.csv

Output:
    sample_output/variance_flags.csv
    sample_output/clarification_requests.csv

Usage:
    python variance_checker.py
"""

import csv
import os
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sample_output")

# A line item is flagged if it moves by more than this percentage
# AND more than this dollar amount (both have to be true, so a small
# account with a big percentage swing on trivial dollars isn't noise).
PERCENT_THRESHOLD = 15.0
DOLLAR_THRESHOLD = 5000.0

EXPENSE_ACCOUNTS = {
    "Management Fees",
    "Repairs & Maintenance",
    "Insurance",
    "Property Taxes",
    "Utilities",
}
REVENUE_ACCOUNTS = {"Rental Income"}


def load_financials():
    path = os.path.join(DATA_DIR, "partner_reported_financials.csv")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["amount"] = float(row["amount"])
    return rows


def latest_two_periods(rows, entity):
    periods = sorted({r["period"] for r in rows if r["entity"] == entity})
    return periods[-2:] if len(periods) >= 2 else periods


def compute_noi(rows, entity, period):
    revenue = sum(r["amount"] for r in rows if r["entity"] == entity and r["period"] == period and r["account_name"] in REVENUE_ACCOUNTS)
    expenses = sum(r["amount"] for r in rows if r["entity"] == entity and r["period"] == period and r["account_name"] in EXPENSE_ACCOUNTS)
    return revenue - expenses


def build_variance_report(rows):
    entities = sorted({r["entity"] for r in rows})
    by_entity_account = defaultdict(dict)  # (entity, account) -> {period: amount}
    for r in rows:
        by_entity_account[(r["entity"], r["account_name"])][r["period"]] = r["amount"]

    variance_rows = []
    for entity in entities:
        prior_period, current_period = latest_two_periods(rows, entity)
        accounts = sorted({r["account_name"] for r in rows if r["entity"] == entity})

        for account in accounts:
            amounts = by_entity_account[(entity, account)]
            prior = amounts.get(prior_period)
            current = amounts.get(current_period)
            if prior is None or current is None:
                continue

            dollar_variance = current - prior
            percent_variance = (dollar_variance / prior * 100) if prior != 0 else float("inf")
            flagged = abs(percent_variance) > PERCENT_THRESHOLD and abs(dollar_variance) > DOLLAR_THRESHOLD

            variance_rows.append({
                "entity": entity,
                "account_name": account,
                "prior_period": prior_period,
                "prior_amount": prior,
                "current_period": current_period,
                "current_amount": current,
                "dollar_variance": round(dollar_variance, 2),
                "percent_variance": round(percent_variance, 1),
                "flagged": flagged,
            })

        # Also check Net Operating Income as a computed line
        noi_prior = compute_noi(rows, entity, prior_period)
        noi_current = compute_noi(rows, entity, current_period)
        dollar_variance = noi_current - noi_prior
        percent_variance = (dollar_variance / noi_prior * 100) if noi_prior != 0 else float("inf")
        flagged = abs(percent_variance) > PERCENT_THRESHOLD and abs(dollar_variance) > DOLLAR_THRESHOLD
        variance_rows.append({
            "entity": entity,
            "account_name": "Net Operating Income (computed)",
            "prior_period": prior_period,
            "prior_amount": round(noi_prior, 2),
            "current_period": current_period,
            "current_amount": round(noi_current, 2),
            "dollar_variance": round(dollar_variance, 2),
            "percent_variance": round(percent_variance, 1),
            "flagged": flagged,
        })

    return variance_rows


def build_clarification_requests(variance_rows):
    requests = []
    for r in variance_rows:
        if not r["flagged"]:
            continue
        direction = "increase" if r["dollar_variance"] > 0 else "decrease"
        question = (
            f"Can you provide detail on the {direction} in {r['account_name']} for "
            f"{r['entity']} in {r['current_period']} "
            f"(${r['prior_amount']:,.0f} in {r['prior_period']} to ${r['current_amount']:,.0f} "
            f"in {r['current_period']}, a {r['percent_variance']:.1f}% change)?"
        )
        requests.append({
            "entity": r["entity"],
            "account_name": r["account_name"],
            "dollar_variance": r["dollar_variance"],
            "percent_variance": r["percent_variance"],
            "suggested_question": question,
        })
    return requests


def main():
    rows = load_financials()
    variance_rows = build_variance_report(rows)
    clarification_requests = build_clarification_requests(variance_rows)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(os.path.join(OUTPUT_DIR, "variance_flags.csv"), "w", newline="", encoding="utf-8") as f:
        fieldnames = ["entity", "account_name", "prior_period", "prior_amount",
                      "current_period", "current_amount", "dollar_variance",
                      "percent_variance", "flagged"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(variance_rows)

    with open(os.path.join(OUTPUT_DIR, "clarification_requests.csv"), "w", newline="", encoding="utf-8") as f:
        fieldnames = ["entity", "account_name", "dollar_variance", "percent_variance", "suggested_question"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clarification_requests)

    print(f"Threshold: flag if variance exceeds {PERCENT_THRESHOLD}% AND ${DOLLAR_THRESHOLD:,.0f}\n")
    print("=== Variance Review ===")
    for r in variance_rows:
        flag = "FLAGGED" if r["flagged"] else "ok"
        print(f"{r['entity']:<32} {r['account_name']:<32} "
              f"{r['prior_amount']:>10,.0f} -> {r['current_amount']:>10,.0f} "
              f"({r['percent_variance']:>6.1f}%)  [{flag}]")

    print(f"\n=== Clarification Requests ({len(clarification_requests)}) ===")
    for r in clarification_requests:
        print(f"- [{r['entity']}] {r['suggested_question']}")

    if not clarification_requests:
        print("No clarification requests needed - all variances within threshold.")


if __name__ == "__main__":
    main()
