# Cross-Team Dependency & Risk Radar

Reads a multi-team task list (CSV), builds a dependency graph, flags blocked
and overdue tasks, and surfaces the critical path in a markdown risk report.
Models the kind of quarterly KPI/risk reporting done for a multi-region
program like Global Transaction Management (APAC/EMEA/US) — but automated.

## What it checks

- **Blocked tasks** — any not-yet-done task whose dependencies aren't done
- **Overdue tasks** — any not-yet-done task past its `due_date`
- **Critical path** — the longest dependency chain in the graph (the
  sequence most likely to define the overall program's timeline)

## Requirements

- Python 3.8+
- [`networkx`](https://pypi.org/project/networkx/)
- (Optional) [`anthropic`](https://pypi.org/project/anthropic/) — only needed
  if you want Claude to write an executive summary on top of the report

```bash
pip install -r requirements.txt
```

## Task CSV format

```
task_id,title,team,status,due_date,depends_on,notes
T-101,Provision compliant data store in new region,Infra,in_progress,2026-09-20,,Waiting on ISO 27001 attestation
T-103,API gateway regional routing config,Platform,not_started,2026-09-25,T-101,
```

- `status` — `not_started`, `in_progress`, or `done`
- `due_date` — `YYYY-MM-DD`
- `depends_on` — semicolon-separated list of `task_id`s this task depends on
  (empty if none)

## Usage

```bash
python radar.py --tasks data/tasks.csv --out output/risk_report.md
```

- `--tasks` — path to the task CSV
- `--out` — path to write the markdown report (default: `output/risk_report.md`)

The tool prints the output path when done:

```
Report written to output/risk_report.md
```

### Optional: Claude executive summary

If `ANTHROPIC_API_KEY` is set in the environment, the report also includes a
short executive summary written by Claude — overall health, the single
biggest risk, and one recommended action — on top of the deterministic
blocked/overdue/critical-path results:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python radar.py --tasks data/tasks.csv --out output/risk_report.md
```

Without the key, the tool still produces the full report using local graph
logic only — the AI layer is additive, not required.

## Example

```bash
python radar.py --tasks data/tasks.csv --out output/risk_report.md
```

Run against the sample [data/tasks.csv](data/tasks.csv) (a 9-task, 8-team
regional launch), the radar finds 5 blocked tasks feeding a critical path
that runs through data store provisioning, gateway routing, security review,
load testing, and go-live readiness — see [output/risk_report.md](output/risk_report.md)
for the full report.
