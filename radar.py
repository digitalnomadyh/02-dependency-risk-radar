#!/usr/bin/env python3
"""
Cross-Team Dependency & Risk Radar
------------------------------------
Reads a task list (CSV) spanning multiple teams, builds a dependency graph,
detects blocked/at-risk tasks, and produces an exec-ready risk report.
Models the kind of quarterly KPI/risk reporting done for a multi-region
program like Global Transaction Management (APAC/EMEA/US) — but automated.

Usage:
    python radar.py --tasks data/tasks.csv --out output/risk_report.md
"""

import argparse
import csv
import os
import sys
from datetime import datetime

import networkx as nx


def load_tasks(path):
    tasks = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            row["depends_on"] = [d for d in row["depends_on"].split(";") if d]
            tasks[row["task_id"]] = row
    return tasks


def build_graph(tasks):
    g = nx.DiGraph()
    for tid, t in tasks.items():
        g.add_node(tid, **t)
    for tid, t in tasks.items():
        for dep in t["depends_on"]:
            if dep in tasks:
                g.add_edge(dep, tid)
    return g


def today():
    return datetime.now().date()


def is_overdue(task):
    if task["status"] == "done":
        return False
    try:
        due = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
    except ValueError:
        return False
    return due < today()


def find_blocked(tasks, g):
    """A task is blocked if any upstream dependency isn't done yet."""
    blocked = []
    for tid, t in tasks.items():
        if t["status"] == "done":
            continue
        unfinished_deps = [d for d in t["depends_on"] if tasks.get(d, {}).get("status") != "done"]
        if unfinished_deps:
            blocked.append((tid, unfinished_deps))
    return blocked


def find_critical_chain(g):
    """Longest dependency chain in the graph — the sequence most likely to
    define the overall program's critical path."""
    try:
        return nx.dag_longest_path(g)
    except Exception:
        return []


def claude_exec_summary(tasks, blocked, overdue, chain):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        blocked_text = "\n".join(
            f"- {tid} ({tasks[tid]['title']}, team {tasks[tid]['team']}) blocked by {deps}"
            for tid, deps in blocked
        )
        overdue_text = "\n".join(
            f"- {tid} ({tasks[tid]['title']}, team {tasks[tid]['team']}), due {tasks[tid]['due_date']}"
            for tid in overdue
        )
        chain_text = " -> ".join(f"{tid} ({tasks[tid]['title']})" for tid in chain)
        prompt = (
            "You are a technical program manager writing a weekly risk update "
            "for executive stakeholders on a multi-team regional infrastructure "
            "launch. Using the data below, write a tight 4-5 sentence status "
            "update: overall health, the single biggest risk, and one "
            "recommended action. Be direct, no filler.\n\n"
            f"Blocked tasks:\n{blocked_text or 'none'}\n\n"
            f"Overdue tasks:\n{overdue_text or 'none'}\n\n"
            f"Critical path:\n{chain_text or 'not determined'}\n"
        )
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        return f"(Claude summary unavailable: {e})"


def write_report(tasks, blocked, overdue, chain, out_path, exec_summary=None):
    lines = []
    lines.append("# Cross-Team Dependency & Risk Radar")
    lines.append(f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append("")
    lines.append(f"Tracking {len(tasks)} tasks across "
                 f"{len(set(t['team'] for t in tasks.values()))} teams.")
    lines.append("")

    if exec_summary:
        lines.append("## Executive Summary (Claude)")
        lines.append(exec_summary.strip())
        lines.append("")

    lines.append("## Blocked Tasks")
    if blocked:
        lines.append("| Task | Team | Blocked By |")
        lines.append("|---|---|---|")
        for tid, deps in blocked:
            t = tasks[tid]
            dep_titles = ", ".join(f"{d} ({tasks[d]['title']})" for d in deps)
            lines.append(f"| {tid}: {t['title']} | {t['team']} | {dep_titles} |")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## Overdue Tasks")
    if overdue:
        lines.append("| Task | Team | Due Date |")
        lines.append("|---|---|---|")
        for tid in overdue:
            t = tasks[tid]
            lines.append(f"| {tid}: {t['title']} | {t['team']} | {t['due_date']} |")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## Critical Path")
    if chain:
        lines.append(" → ".join(f"**{tid}** ({tasks[tid]['title']})" for tid in chain))
    else:
        lines.append("_Not determined (no dependency chain found)._")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Cross-Team Dependency & Risk Radar")
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--out", default="output/risk_report.md")
    args = parser.parse_args()

    tasks = load_tasks(args.tasks)
    g = build_graph(tasks)
    blocked = find_blocked(tasks, g)
    overdue = [tid for tid, t in tasks.items() if is_overdue(t)]
    chain = find_critical_chain(g)
    exec_summary = claude_exec_summary(tasks, blocked, overdue, chain)
    out_path = write_report(tasks, blocked, overdue, chain, args.out, exec_summary)
    print(f"Report written to {out_path}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("(Set ANTHROPIC_API_KEY to also get a Claude-written executive summary.)")


if __name__ == "__main__":
    sys.exit(main())
