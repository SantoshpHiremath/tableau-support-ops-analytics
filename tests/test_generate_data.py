import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from generate_data import generate_tickets, CATEGORY_PROFILES


def test_generate_tickets_returns_requested_count():
    rows = generate_tickets(n=500, seed=1)
    assert len(rows) == 500


def test_generate_tickets_only_uses_known_categories():
    rows = generate_tickets(n=500, seed=1)
    categories = {r["category"] for r in rows}
    assert categories <= set(CATEGORY_PROFILES.keys())


def test_generate_tickets_ticket_ids_are_unique():
    rows = generate_tickets(n=1000, seed=2)
    ids = [r["ticket_id"] for r in rows]
    assert len(ids) == len(set(ids))


def test_generate_tickets_resolved_at_after_created_at():
    rows = generate_tickets(n=500, seed=3)
    for r in rows:
        assert r["resolved_at"] > r["created_at"]


def test_generate_tickets_resolution_hours_always_positive():
    rows = generate_tickets(n=500, seed=4)
    assert all(r["resolution_hours"] > 0 for r in rows)


def test_generate_tickets_created_at_only_on_weekdays():
    from datetime import datetime
    rows = generate_tickets(n=500, seed=5)
    for r in rows:
        dt = datetime.fromisoformat(r["created_at"])
        assert dt.weekday() < 5


def test_generate_tickets_same_seed_is_reproducible():
    rows_a = generate_tickets(n=200, seed=42)
    rows_b = generate_tickets(n=200, seed=42)
    assert rows_a == rows_b


def test_generate_tickets_different_seeds_differ():
    rows_a = generate_tickets(n=200, seed=1)
    rows_b = generate_tickets(n=200, seed=2)
    assert rows_a != rows_b


def test_exchange_category_has_higher_mean_resolution_than_user_admin():
    """
    A genuine, checkable claim about the generator's realism: Exchange
    issues are modeled as taking longer to resolve on average than
    user-administration requests, matching real-world IT-support
    intuition (mailbox/permissions issues in a groupware system are
    typically more involved than a password reset or account change).
    """
    rows = generate_tickets(n=3000, seed=0)
    exchange = [r["resolution_hours"] for r in rows if r["category"] == "Exchange-Umfeld"]
    admin = [r["resolution_hours"] for r in rows if r["category"] == "Benutzerverwaltung"]
    assert (sum(exchange) / len(exchange)) > (sum(admin) / len(admin))


def test_automatable_candidate_only_flagged_for_expected_categories():
    rows = generate_tickets(n=1000, seed=6)
    flagged_categories = {r["category"] for r in rows if r["automatable_candidate"]}
    assert flagged_categories <= {"Benutzerverwaltung", "Drucker/Scanner"}
