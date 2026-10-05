# tableau-support-ops-analytics

An IT support-operations analytics project covering SLA performance reporting, workload distribution, and automation-opportunity identification, exported into a genuine Tableau `.hyper` extract file using Tableau's own official `tableauhyperapi` Python package. It focuses on reporting/BI work in **Tableau**, with a dataset shaped like real support-ticket categories (Drucker/Scanner, Benutzerverwaltung, Interne Fernbetreuung, Exchange-Umfeld).

## What it does

- `src/generate_data.py` generates structured synthetic IT support tickets: 4 categories, each with a distinct, deliberately different resolution-time distribution and SLA threshold (Exchange issues take longer and breach SLA more often than a printer request, modeled intentionally rather than as uniform noise), weekday-only creation timestamps, priority levels, and a flag for tickets that are Power Automate automation candidates.
- `src/analysis.py` runs the BI analysis: SLA breach rate and average resolution time by category, weekly volume trend, workload distribution by team member, automation-opportunity sizing ("Verbesserungspotenziale sichtbar machen"), and an SLA-breach crosstab by priority level.
- `src/build_hyper_extract.py` builds a **Tableau `.hyper` extract file** from the cleaned ticket data using Tableau's official `tableauhyperapi` package, then independently re-opens it in a fresh process and runs real SQL aggregate queries against it to show the file is queryable Tableau data, not just bytes on disk.
- `run_pipeline.py` runs the full flow end to end and prints a report (see "Results" below, copied directly from an actual run).
- `tests/` has 25 tests, all passing, covering the data generator, the analysis functions, and the Hyper extract build/verify round-trip.

## Data

The ticket data is synthetic. The generator was built to match typical support-ticket categories and to encode realistic operational structure (a slower, higher-breach-rate Exchange category; a subset of printer/scanner and user-administration tickets flagged as automation candidates) so the analysis has real patterns to surface. Resolution-time distributions and SLA thresholds are illustrative modeling choices (Exchange/groupware issues plausibly take longer than a straightforward printer request); the generator is built so real ticket exports can replace it.

## Scope

`tableauhyperapi` is Tableau's official Python package, installed with a plain `pip install`, and it launches the actual Tableau Hyper database engine as a subprocess (`HyperProcess`), the same engine that powers Tableau Desktop and Tableau Server extracts. `output/support_tickets.hyper` is written and read back through that engine, and `build_hyper_extract.verify_extract()` re-opens the file in a **separate, fresh process** and runs a real SQL aggregate query against it. Opened in Tableau Desktop ("Connect to a File > More... > Hyper"), the file loads directly and behaves like any other Tableau extract. This project covers the data layer of a Tableau workbook (the `.hyper` extract); worksheets and dashboards are authored on top of it in Tableau Desktop.

## Results

Sample output from an actual run of `run_pipeline.py`:

```
--- SLA performance by category ---
                       tickets  avg_resolution_hours  sla_breach_rate
category
Exchange-Umfeld            614                9.2651           0.2443
Benutzerverwaltung         842                2.9896           0.0238
Drucker/Scanner            969                4.0869           0.0227
Interne Fernbetreuung      575                6.0954           0.0139

--- Automation opportunity (Power Automate candidates) ---
                       tickets  automatable_tickets  automatable_share
category
Drucker/Scanner            969                  390             0.4025
Benutzerverwaltung         842                  336             0.3990
Exchange-Umfeld            614                    0             0.0000
Interne Fernbetreuung      575                    0             0.0000

--- Building real Tableau .hyper extract ---
Wrote 3000 rows to output/support_tickets.hyper via Tableau's official tableauhyperapi

--- Independently re-verifying the extract (fresh process, real SQL) ---
{'total_rows': 3000, 'overall_sla_breach_rate': 0.066667,
 'categories': ['Benutzerverwaltung', 'Drucker/Scanner', 'Exchange-Umfeld', 'Interne Fernbetreuung']}
```

Exchange-Umfeld tickets breach SLA roughly 10x more often than the other three categories (24.4% vs. under 2.5%), a clear "Verbesserungspotenzial" surfaced by the analysis. Roughly 40% of Drucker/Scanner and Benutzerverwaltung tickets are flagged as Power Automate automation candidates, versus none in the other two categories, giving a data-backed automation priority list.

## Tests

- `python3 -m pytest tests/ -v`: 25/25 tests pass.
- `python3 run_pipeline.py` runs end to end; the sample output above is copied from this run's stdout.
- `build_hyper_extract.verify_extract()` opens a **new, independent** `HyperProcess`/`Connection` (not the one that wrote the file) and runs real SQL (`SELECT COUNT(*)`, `SELECT AVG(...)`, `SELECT DISTINCT ...`) against `output/support_tickets.hyper`.
- `tests/test_hyper_extract.py` covers the full extract round-trip: the file exists and is non-empty, the row count in the extract matches the source dataframe exactly, and category values read back match the known category set.

## Project structure

```
run_pipeline.py                  end-to-end runner
src/generate_data.py             synthetic ticket generator
src/analysis.py                  SLA, workload and automation analysis
src/build_hyper_extract.py       Tableau .hyper build and verification
data/support_tickets.csv         generated tickets
output/support_tickets.hyper     Tableau extract
tests/                           pytest suite
```

## Running it

```bash
pip install pandas tableauhyperapi pytest
python3 -m pytest tests/ -v
python3 run_pipeline.py
```

## Notes

The first version of `analysis.load_tickets()` used `pd.read_csv(path, parse_dates=["created_at", "resolved_at"])`, which failed with a `ValueError` on the generated data: most `resolved_at` timestamps carry microsecond precision (from adding a fractional-hour `timedelta` to `created_at`), but a small fraction land on an exact whole second and have no fractional part, e.g. `2026-01-30T09:32:00` next to `2026-05-12T05:58:23.176957`. Pandas' single-format date parser infers one format from the first rows and throws on the rows that do not match. Mixed-precision timestamps are common in real log and ticket exports. I fixed it by parsing with `format="ISO8601"`, which checks each value against the ISO 8601 spec individually. `test_load_tickets_handles_mixed_fractional_second_precision` in `tests/test_analysis.py` fails against the original `parse_dates=[...]` call and passes against the fix.

## Possible extensions

- Build Tableau worksheets and a dashboard on top of the `.hyper` extract.
- Load a real ticket export in place of the synthetic data.
- Implement the Power Automate flows for the flagged automation candidates.
