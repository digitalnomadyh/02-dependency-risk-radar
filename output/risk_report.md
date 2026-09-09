# Cross-Team Dependency & Risk Radar
_Generated 2026-09-09 12:28_

Tracking 9 tasks across 8 teams.

## Blocked Tasks
| Task | Team | Blocked By |
|---|---|---|
| T-103: API gateway regional routing config | Platform | T-101 (Provision compliant data store in new region) |
| T-104: Developer docs update for new region | DevRel | T-103 (API gateway regional routing config) |
| T-105: Security review of regional routing | Security | T-103 (API gateway regional routing config) |
| T-106: Load testing in new region | QA | T-103 (API gateway regional routing config), T-105 (Security review of regional routing) |
| T-107: Go-live readiness review | Program | T-104 (Developer docs update for new region), T-106 (Load testing in new region) |

## Overdue Tasks
_None._

## Critical Path
**T-101** (Provision compliant data store in new region) → **T-103** (API gateway regional routing config) → **T-105** (Security review of regional routing) → **T-106** (Load testing in new region) → **T-107** (Go-live readiness review)