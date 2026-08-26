import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from generate_data import generate_tickets, write_csv
from analysis import load_tickets
from build_hyper_extract import build_extract, verify_extract


@pytest.fixture(scope="module")
def hyper_path(tmp_path_factory):
    tickets = generate_tickets(n=500, seed=7)
    csv_path = tmp_path_factory.mktemp("data") / "tickets.csv"
    write_csv(tickets, str(csv_path))
    df = load_tickets(str(csv_path))

    out_dir = tmp_path_factory.mktemp("output")
    out_path = str(out_dir / "test_extract.hyper")
    build_extract(df, out_path)
    return out_path, len(df)


def test_build_extract_writes_a_real_file(hyper_path):
    path, _ = hyper_path
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0


def test_build_extract_row_count_matches_source_dataframe(hyper_path):
    path, expected_count = hyper_path
    written = None
    # build_extract already returned the count when called in the
    # fixture; re-verify independently here via a fresh connection.
    result = verify_extract(path)
    assert result["total_rows"] == expected_count


def test_verify_extract_reopens_in_a_fresh_process(hyper_path):
    """
    The core claim for this project: the .hyper file is genuinely
    queryable Tableau data, not just serialized bytes. This test opens
    a brand new HyperProcess/Connection (independent of whatever
    process wrote the file) and runs a real SQL aggregate query
    against it.
    """
    path, _ = hyper_path
    result = verify_extract(path)
    assert 0.0 <= result["overall_sla_breach_rate"] <= 1.0
    assert len(result["categories"]) > 0


def test_verify_extract_categories_match_known_set(hyper_path):
    path, _ = hyper_path
    result = verify_extract(path)
    assert set(result["categories"]) <= {
        "Drucker/Scanner", "Benutzerverwaltung", "Interne Fernbetreuung", "Exchange-Umfeld",
    }
