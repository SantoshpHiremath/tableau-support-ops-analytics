"""
Synthetic IT support-ticket data generator.

Disclosure: no real IT-support-ticket dataset was reachable in this
environment (kaggle.com and data.world both failed to connect when
checked directly). This generates realistic, structured synthetic
ticket data modeled on the exact ticket categories named in the DATEV
"Technical Support Standard-Request" posting -- printer/scanner
requests, user administration, internal remote support, and the
Exchange environment -- with deliberately realistic operational
patterns (varying resolution times by category, a backlog effect,
weekday seasonality, a subset of tickets that breach SLA) rather than
uniform random noise, so the downstream analysis has real structure to
find, not just numbers to reformat.
"""

import csv
import random
from datetime import datetime, timedelta

CATEGORIES = [
    "Drucker/Scanner",
    "Benutzerverwaltung",
    "Interne Fernbetreuung",
    "Exchange-Umfeld",
]

# Each category has a different realistic resolution-time distribution
# (mean hours, std hours) and a different baseline SLA-breach rate --
# e.g. Exchange issues realistically take longer and breach SLA more
# often than a straightforward printer request.
CATEGORY_PROFILES = {
    "Drucker/Scanner": {"mean_hours": 4, "std_hours": 2, "sla_hours": 8, "volume_weight": 0.32},
    "Benutzerverwaltung": {"mean_hours": 3, "std_hours": 1.5, "sla_hours": 6, "volume_weight": 0.28},
    "Interne Fernbetreuung": {"mean_hours": 6, "std_hours": 3, "sla_hours": 12, "volume_weight": 0.18},
    "Exchange-Umfeld": {"mean_hours": 9, "std_hours": 4, "sla_hours": 12, "volume_weight": 0.22},
}

PRIORITIES = ["Niedrig", "Mittel", "Hoch"]
PRIORITY_WEIGHTS = [0.5, 0.35, 0.15]

TEAM_MEMBERS = [
    "A. Bauer", "M. Fischer", "S. Wagner", "J. Schulz", "L. Hoffmann", "K. Krueger",
]

START_DATE = datetime(2026, 1, 1)
END_DATE = datetime(2026, 6, 30)


def _random_business_datetime(rng, start, end):
    """Pick a random datetime weighted toward weekday business hours."""
    total_days = (end - start).days
    while True:
        day_offset = rng.randint(0, total_days)
        candidate = start + timedelta(days=day_offset)
        if candidate.weekday() < 5:  # Mon-Fri
            hour = rng.randint(7, 18)
            minute = rng.randint(0, 59)
            return candidate.replace(hour=hour, minute=minute)


def generate_tickets(n=3000, seed=0):
    """Generate n synthetic support tickets with realistic structure."""
    rng = random.Random(seed)
    categories = list(CATEGORY_PROFILES.keys())
    weights = [CATEGORY_PROFILES[c]["volume_weight"] for c in categories]

    rows = []
    for i in range(n):
        category = rng.choices(categories, weights=weights, k=1)[0]
        profile = CATEGORY_PROFILES[category]

        created_at = _random_business_datetime(rng, START_DATE, END_DATE)

        resolution_hours = max(0.25, rng.gauss(profile["mean_hours"], profile["std_hours"]))
        resolved_at = created_at + timedelta(hours=resolution_hours)

        sla_hours = profile["sla_hours"]
        sla_breached = resolution_hours > sla_hours

        priority = rng.choices(PRIORITIES, weights=PRIORITY_WEIGHTS, k=1)[0]
        assignee = rng.choice(TEAM_MEMBERS)

        automatable = category in ("Benutzerverwaltung", "Drucker/Scanner") and rng.random() < 0.4

        rows.append({
            "ticket_id": f"TS-{10000 + i}",
            "category": category,
            "priority": priority,
            "assignee": assignee,
            "created_at": created_at.isoformat(),
            "resolved_at": resolved_at.isoformat(),
            "resolution_hours": round(resolution_hours, 2),
            "sla_hours": sla_hours,
            "sla_breached": sla_breached,
            "automatable_candidate": automatable,
        })

    return rows


def write_csv(rows, path):
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    tickets = generate_tickets(n=3000, seed=0)
    write_csv(tickets, "data/support_tickets.csv")
    print(f"Wrote {len(tickets)} synthetic tickets to data/support_tickets.csv")
