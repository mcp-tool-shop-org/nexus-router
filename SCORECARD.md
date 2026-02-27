# Scorecard

> Score a repo before remediation. Fill this out first, then use SHIP_GATE.md to fix.

**Repo:** nexus-router
**Date:** 2026-02-27
**Type tags:** [pypi]

## Pre-Remediation Assessment

| Category | Score | Notes |
|----------|-------|-------|
| A. Security | 8/10 | SECURITY.md exists but wrong email, outdated version table |
| B. Error Handling | 10/10 | NexusOperationalError with code + details, schema validation |
| C. Operator Docs | 9/10 | README, CHANGELOG (stale), ARCHITECTURE, ADAPTER_SPEC |
| D. Shipping Hygiene | 7/10 | CI good (lint + test + build-check) but no coverage, no dep-audit, no verify |
| E. Identity (soft) | 10/10 | Logo, translations, landing page |
| **Overall** | **44/50** | |

## Key Gaps

1. SECURITY.md has wrong email and outdated version table (0.1.x)
2. No Codecov coverage upload in CI
3. No dependency audit job
4. No verify script (Makefile)
5. CHANGELOG missing v1.0.0 and v1.1.0 entries

## Remediation Priority

| Priority | Item | Estimated effort |
|----------|------|-----------------|
| 1 | Update SECURITY.md | 3 min |
| 2 | Add coverage + dep-audit to CI | 3 min |
| 3 | Add Makefile, update CHANGELOG | 5 min |

## Post-Remediation

| Category | Before | After |
|----------|--------|-------|
| A. Security | 8/10 | 10/10 |
| B. Error Handling | 10/10 | 10/10 |
| C. Operator Docs | 9/10 | 10/10 |
| D. Shipping Hygiene | 7/10 | 10/10 |
| E. Identity (soft) | 10/10 | 10/10 |
| **Overall** | 44/50 | 50/50 |
