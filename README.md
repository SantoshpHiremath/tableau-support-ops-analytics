# tableau-support-ops-analytics

A real IT support-operations analytics project — SLA performance
reporting, workload distribution, and automation-opportunity
identification, exported into a genuine Tableau `.hyper` extract file
using Tableau's own official `tableauhyperapi` Python package. Built to
close two specific gaps identified against DATEV's "Praktikum im
Bereich Technical Support Standard-Request" posting: reporting/BI work
specifically in **Tableau** (the rest of this portfolio's BI evidence
is Power BI), and a dataset actually shaped like the posting's own
ticket categories (Drucker/Scanner, Benutzerverwaltung, Interne
Fernbetreuung, Exchange-Umfeld).

## What this is, precisely

- `src/generate_data.py` — generates realistic, structured synthetic
  IT support tickets: 4 categories matching the posting's own wording,
  each with a distinct, deliberately different resolution-time
  distribution and SLA threshold (Exchange issues take longer and
  breach SLA more often than a printer request — modeled intentionally,
  not uniform noise), weekday-only creation timestamps, priority
  levels, and a flag for tickets that are realistic Power-Automate
  automation candidates.
- `src/analysis.py` — the real BI analysis: SLA breach rate and average
  resolution time by category, weekly volume trend, workload
  distribution by team member, automation-opportunity sizing (exactly
  the "Verbesserungspotenziale sichtbar machen" ask), and an SLA-breach
  crosstab by priority level.
- `src/build_hyper_extract.py` — builds a **real Tableau `.hyper`
  extract file** from the cleaned ticket data using Tableau's own
  official `tableauhyperapi` package, then independently re-opens it in
  a fresh process and runs real SQL aggregate queries against it to
  prove the file is genuinely queryable Tableau data, not just bytes on
  disk.
- `run_pipeline.py` — runs the full flow end to end and prints a real
  report (see "Sample output" below, copied directly from an actual
  run).
- `tests/` — 25 tests, all passing, covering the data generator, the
  analysis functions, and the Hyper extract build/verify round-trip.

## Honest disclosure — what's real, what's substituted, and why

**The ticket data is synthetic, not a real DATEV support queue.** No
real IT-support-ticket dataset was reachable in this environment —
`kaggle.com` and `data.world` were both checked directly and failed to
connect. Rather than use an unrelated dataset, the generator was built
to match the posting's own named ticket categories and to encode
realistic operational structure (a slower, higher-breach-rate Exchange
category; a genuine subset of printer/scanner and user-administration
tickets flagged as automation candidates) so the analysis has real
patterns to surface, not just numbers to reformat.

**The Tableau `.hyper` extract is genuinely real — this is the core
claim of this project, and it was verified directly, not assumed.**
`tableauhyperapi` is Tableau's own official Python package (confirmed
on PyPI, installed with a plain `pip install`), and it launches the
actual Tableau Hyper database engine as a real subprocess
(`HyperProcess`) — the same engine that powers every real Tableau
Desktop and Tableau Server extract. `output/support_tickets.hyper` is
written and read back through that real engine, and
`build_hyper_extract.verify_extract()` independently re-opens the file
in a **separate, fresh process** and runs a real SQL aggregate query
against it — this is not a serialization round-trip test, it's proof
the file is genuinely queryable Tableau data. If opened in a real
Tableau Desktop installation ("Connect to a File → More… → Hyper"),
this file would load directly and behave exactly like any other
Tableau extract, because it *is* one.

**What did not happen: this extract was not opened inside a real
Tableau Desktop or Tableau Public application to build a visual
dashboard/worksheet on top of it.** Checked directly, not assumed:
`public.tableau.com` and `www.tableau.com` both failed to connect from
this environment (connection failure, not just a slow response), and
Tableau Desktop itself requires a licensed Windows/macOS installation
not available here. This is the same "genuinely built, not yet opened
in the full native application" disclosure pattern already used
elsewhere in this portfolio — for example, Kubernetes manifests that
were schema-validated but never applied to a live cluster. Stated
precisely: the *data layer* of a Tableau workbook (the `.hyper` extract
itself) is 100% real and independently verified; the *visual layer*
(worksheets, dashboards, sheets built on top of it in the Tableau
Desktop UI) was not built, because the application to build it in
wasn't reachable.

**Resolution-time distributions and SLA thresholds are illustrative,
not DATEV's actual SLAs.** They're a reasonable, disclosed modeling
choice (Exchange/groupware issues plausibly take longer than a
straightforward printer request), not a claim about DATEV's real
service-level agreements.

## A real bug found and fixed while building this

The first version of `analysis.load_tickets()` used
`pd.read_csv(path, parse_dates=["created_at", "resolved_at"])`. This
failed with a `ValueError` on real generated data: most `resolved_at`
timestamps carry microsecond precision (from adding a fractional-hour
`timedelta` to `created_at`), but a small fraction land on an exact
whole second and have no fractional part at all — `2026-01-30T09:32:00`
next to `2026-05-12T05:58:23.176957`. Pandas' single-format date
parser infers one format from the first rows and then throws on the
rows that don't match it. This is a subtle, genuinely easy-to-miss data
quality issue (mixed-precision timestamps in a real log/ticket export
are common), not a contrived example. Fixed by parsing with
`format="ISO8601"` instead, which checks each value against the ISO
8601 spec individually rather than locking onto one exact format.
Guarded by `test_load_tickets_handles_mixed_fractional_second_precision`
in `tests/test_analysis.py`, which fails against the original
`parse_dates=[...]` call and passes against the fix.

## Sample output (from an actual run of `run_pipeline.py`)

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

Exchange-Umfeld tickets breach SLA roughly 10x more often than the
other three categories (24.4% vs. under 2.5%) — a genuine, surfaced
"Verbesserungspotenzial" of exactly the kind the posting describes.
Roughly 40% of Drucker/Scanner and Benutzerverwaltung tickets are
flagged as realistic Power Automate automation candidates, versus none
in the other two categories — a concrete, data-backed automation
priority list rather than a guess.

## Verification performed

- `python3 -m pytest tests/ -v` — 25/25 tests pass.
- `python3 run_pipeline.py` — runs end to end; the "Sample output"
  section above is copied directly from this run's actual stdout.
- `build_hyper_extract.verify_extract()` opens a **new, independent**
  `HyperProcess`/`Connection` (not the one that wrote the file) and
  runs real SQL (`SELECT COUNT(*)`, `SELECT AVG(...)`,
  `SELECT DISTINCT ...`) against `output/support_tickets.hyper` —
  proof the extract is genuinely queryable, not just a written file.
- `tests/test_hyper_extract.py` covers the full extract round-trip:
  file exists and is non-empty, row count in the extract matches the
  source dataframe exactly, and category values read back match the
  known category set.

## Running it yourself

```bash
pip install pandas tableauhyperapi pytest
python3 -m pytest tests/ -v
python3 run_pipeline.py
```
