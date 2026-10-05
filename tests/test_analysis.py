import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from generate_data import generate_tickets, write_csv
from analysis import (
    load_tickets, sla_performance_by_category, volume_by_week,
    workload_by_assignee, automation_opportunity_summary,
    priority_breach_crosstab,
)


@pytest.fixture(scope="module")
def csv_path(tmp_path_factory):
    tickets = generate_tickets(n=3000, seed=0)
    path = tmp_path_factory.mktemp("data") / "tickets.csv"
    write_csv(tickets, str(path))
    return str(path)


@pytest.fixture(scope="module")
def df(csv_path):
    return load_tickets(csv_path)


def test_load_tickets_parses_datetimes(df):
    import pandas as pd
    assert pd.api.types.is_datetime64_any_dtype(df["created_at"])
    assert pd.api.types.is_datetime64_any_dtype(df["resolved_at"])


def test_load_tickets_no_null_dates(df):
    assert df["created_at"].isnull().sum() == 0
    assert df["resolved_at"].isnull().sum() == 0


def test_load_tickets_handles_mixed_fractional_second_precision(csv_path):
    """
    Regression test for a real bug found during development: some
    resolved_at timestamps have no fractional seconds (land exactly on
    a whole second) while most do, which broke a naive
    pd.read_csv(parse_dates=[...]) call with a ValueError. This test
    fails against the original buggy load path and passes against the
    ISO8601-format fix in analysis.load_tickets.
    """
    df = load_tickets(csv_path)
    assert len(df) == 3000


def test_sla_performance_covers_all_categories(df):
    result = sla_performance_by_category(df)
    assert result["tickets"].sum() == len(df)
    assert set(result.index) == set(df["category"].unique())


def test_sla_performance_breach_rates_are_valid_probabilities(df):
    result = sla_performance_by_category(df)
    assert (result["sla_breach_rate"] >= 0).all()
    assert (result["sla_breach_rate"] <= 1).all()


def test_exchange_has_worst_sla_performance(df):
    """
    A genuine, checkable finding matching the generator's design:
    Exchange-Umfeld has the highest SLA breach rate of the four
    categories -- exactly the kind of "Verbesserungspotenzial" BI
    reporting is meant to surface.
    """
    result = sla_performance_by_category(df)
    assert result.index[0] == "Exchange-Umfeld"


def test_volume_by_week_sums_to_total(df):
    result = volume_by_week(df)
    assert result.sum() == len(df)


def test_workload_by_assignee_covers_all_tickets(df):
    result = workload_by_assignee(df)
    assert result["tickets"].sum() == len(df)
    assert set(result.index) == set(df["assignee"].unique())


def test_automation_opportunity_summary_shares_are_valid(df):
    result = automation_opportunity_summary(df)
    assert (result["automatable_share"] >= 0).all()
    assert (result["automatable_share"] <= 1).all()


def test_automation_opportunity_only_flags_expected_categories(df):
    result = automation_opportunity_summary(df)
    non_zero = result[result["automatable_tickets"] > 0]
    assert set(non_zero.index) <= {"Benutzerverwaltung", "Drucker/Scanner"}


def test_priority_breach_crosstab_covers_all_tickets(df):
    result = priority_breach_crosstab(df)
    assert result["tickets"].sum() == len(df)
    assert set(result.index) == {"Niedrig", "Mittel", "Hoch"}
