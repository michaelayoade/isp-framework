# Database Migration Policy

_Last updated: 26 July 2025_

This document defines the mandatory rules for Alembic migrations in the ISP Framework.

## 1. One Linear Chain
* The project **must** have a single migration head at any time (`alembic heads` returns exactly one revision).
* Branches are disallowed. If multiple heads appear, they must be resolved **before** merging.

## 2. File Naming
* Use the template: `<timestamp>_<concise_description>.py` where timestamp is UTC `YYYYMMDD_HHMM`.
* Keep names short and descriptive (`20250726_add_radius_clients.py`).

## 3. Content Guidelines
* Prefer **explicit** migrations; avoid auto-generated dumps over 200 lines.
* Include seeding data only if absolutely required for foreign-key integrity.
* Wrap constraint changes in safe `if not inspector.has…` checks.

## 4. Consolidation Workflow
1. Run `make migration` for new feature branches.
2. Before merging to `main`, run `python scripts/consolidate_migrations.py --dry-run`.
3. Resolve any orphaned or duplicate revisions; rerun with `--apply`.
4. Confirm `alembic upgrade head` on a clean DB succeeds.

## 5. Review Checklist
- [ ] One head only
- [ ] Well-named file
- [ ] < 200 lines (else rationale provided)
- [ ] `downgrade()` implemented or explicitly justified
- [ ] Passes on PostgreSQL 13 & 15

## 6. Emergency Fixes
If a bad migration hits production:
* Create a **targeted** hotfix migration; never edit historical files in `main`.
* Document reason in commit message and in the file docstring.

## 7. Useful Commands
```bash
alembic current            # Show current revision
alembic history --verbose  # Full chain
alembic heads              # Detect branches
```

Following this policy ensures reliable, repeatable schema evolution across all environments.
