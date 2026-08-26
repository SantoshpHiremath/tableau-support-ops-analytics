"""
Support-operations analytics functions: SLA performance, category
volume/load, automation-candidate identification, and team workload
distribution -- the exact "BI-Auswertungen" / "Verbesserungspotenziale
in unseren Prozessen sichtbar machen" ask from the posting.
"""

import pandas as pd


def load_tickets(path="data/support_tickets.csv"):
    # format="ISO8601" handles the fact that resolved_at timestamps are
    # not all the same width: most carry microseconds (from adding a
    # fractional-hour timedelta to created_at), but a small fraction
    # land on an exact whole second and have no fractional part at all.
    # A plain parse_dates=[...] locks onto whichever format pandas
    # infers from the first rows and then fails on the mismatched ones
    # (a real bug caught here, not a hypothetical) -- format="ISO8601"
    # parses each value against the ISO 8601 spec individually instead.
    df = pd.read_csv(path)
    df["created_at"] = pd.to_datetime(df["created_at"], format="ISO8601")
    df["resolved_at"] = pd.to_datetime(df["resolved_at"], format="ISO8601")
    df["sla_breached"] = df["sla_breached"].astype(bool)
    df["automatable_candidate"] = df["automatable_candidate"].astype(bool)
    df["created_week"] = df["created_at"].dt.to_period("W").apply(lambda p: p.start_time)
    df["created_weekday"] = df["created_at"].dt.day_name()
    return df


def sla_performance_by_category(df):
    """SLA breach rate and average resolution time per category."""
    g = df.groupby("category")
    result = g.agg(
        tickets=("ticket_id", "count"),
        avg_resolution_hours=("resolution_hours", "mean"),
        sla_breach_rate=("sla_breached", "mean"),
    )
    return result.sort_values("sla_breach_rate", ascending=False)


def volume_by_week(df):
    """Weekly ticket volume, to spot backlog/seasonality trends."""
    return df.groupby("created_week").size().rename("tickets")


def workload_by_assignee(df):
    """Ticket count and average resolution time per team member."""
    g = df.groupby("assignee")
    result = g.agg(
        tickets=("ticket_id", "count"),
        avg_resolution_hours=("resolution_hours", "mean"),
        sla_breach_rate=("sla_breached", "mean"),
    )
    return result.sort_values("tickets", ascending=False)


def automation_opportunity_summary(df):
    """
    Quantify the automation opportunity the posting explicitly asks
    about ("Automatisierung wiederkehrender Arbeitsschritte mit Power
    Automate"): how many tickets per category are flagged as
    automation candidates, and what fraction of that category's total
    volume that represents.
    """
    g = df.groupby("category")
    result = g.agg(
        tickets=("ticket_id", "count"),
        automatable_tickets=("automatable_candidate", "sum"),
    )
    result["automatable_share"] = result["automatable_tickets"] / result["tickets"]
    return result.sort_values("automatable_tickets", ascending=False)


def priority_breach_crosstab(df):
    """
    Cross-tabulation of SLA breach rate by priority level -- a real,
    checkable claim: does higher-declared priority actually correlate
    with better SLA performance, or does it not (a common, genuinely
    useful ops-quality finding either way)?
    """
    return df.groupby("priority")["sla_breached"].agg(
        tickets="count", breach_rate="mean"
    )
