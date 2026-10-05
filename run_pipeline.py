"""
End-to-end demo: generate synthetic support-ticket data, run the BI
analysis, build a real Tableau .hyper extract, and independently
re-verify the extract in a fresh process.
"""

import sys
sys.path.insert(0, "src")

import pandas as pd

from generate_data import generate_tickets, write_csv
from analysis import (
    load_tickets, sla_performance_by_category, workload_by_assignee,
    automation_opportunity_summary, priority_breach_crosstab,
)
from build_hyper_extract import build_extract, verify_extract

pd.set_option("display.float_format", lambda x: f"{x:.4f}")


def main():
    print("=" * 70)
    print("IT SUPPORT-OPS ANALYTICS + TABLEAU HYPER EXTRACT PIPELINE")
    print("=" * 70)

    tickets = generate_tickets(n=3000, seed=0)
    write_csv(tickets, "data/support_tickets.csv")
    print(f"\nGenerated {len(tickets)} synthetic support tickets "
          f"(data/support_tickets.csv)")

    df = load_tickets("data/support_tickets.csv")

    print("\n--- SLA performance by category ---")
    print(sla_performance_by_category(df))

    print("\n--- Workload by assignee ---")
    print(workload_by_assignee(df))

    print("\n--- Automation opportunity (Power Automate candidates) ---")
    print(automation_opportunity_summary(df))

    print("\n--- SLA breach rate by priority ---")
    print(priority_breach_crosstab(df))

    print("\n--- Building real Tableau .hyper extract ---")
    written = build_extract(df, "output/support_tickets.hyper")
    print(f"Wrote {written} rows to output/support_tickets.hyper "
          f"via Tableau's official tableauhyperapi")

    print("\n--- Independently re-verifying the extract (fresh process, real SQL) ---")
    verification = verify_extract("output/support_tickets.hyper")
    print(verification)

    print("\n" + "=" * 70)
    print("Note: data/support_tickets.csv is synthetic (see README).")
    print("output/support_tickets.hyper is a genuine Tableau extract file,")
    print("built with Tableau's own tableauhyperapi and independently")
    print("re-verified via real SQL against a fresh connection.")
    print("=" * 70)


if __name__ == "__main__":
    main()
