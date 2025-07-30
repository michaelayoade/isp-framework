# Ansible Automation Integration Plan

Focus: Automatic configuration server for device provisioning (routers, OLTs, CPE) — no ML/predictive analytics scope.

---
## 1. Objectives
- Zero-touch provisioning triggered by lifecycle events in ISP Framework.
- Template-driven, vendor-agnostic configuration management via Ansible playbooks/roles.
- Real-time job visibility and audit trail inside the existing admin portal.

---
## 2. Architecture Overview
```
ISP Framework (FastAPI) ──▶ Automation Module ──▶ ansible-runner ▶ Network Devices
                             │                     (playbooks / roles)
                             │
                             └──▶ Postgres tables: Device, Credential, ProvisioningTask
```
- **ansible-runner** executed locally for Phase-1; pluggable to AWX later.
- Dynamic inventory served by `/automation/inventory` endpoint.
- Job status/events streamed via WebSocket to UI.

---
## 3. Phased Roadmap
| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1. Foundation | 1–2 weeks | • `automation` module scaffold<br>• Alembic migration: `device`, `credential`, `provisioning_task` tables<br>• `ansible/` repo folder with `router_mikrotik` role + `provision_router.yml` playbook<br>• Runner wrapper util + unit smoke test (check_mode)<br>• `POST /automation/jobs`, `GET /automation/jobs/{id}` endpoints |
| 2. Core Automation | 3–4 weeks | • OLT/ONT roles & playbooks (Huawei, ZTE, Nokia)<br>• `/automation/inventory` dynamic endpoint<br>• Event trigger: on `CustomerService` activation enqueue provisioning job<br>• WebSocket/SSE log streaming to admin UI page |
| 3. Scaling & RBAC | 5–6 weeks | • Credential encryption w/ Ansible Vault or HashiCorp Vault<br>• Permission "automation:run" enforcement<br>• Bulk CPE update playbook<br>• Integration tests (FastAPI TestClient + runner) |

---
## 4. Data Model Changes
```text
Device(id, vendor, model, hostname, mgmt_address, site_id, credential_id, created_at)
Credential(id, name, type, encrypted_secret, created_at)
ProvisioningTask(id, playbook, status, started_at, finished_at, log, initiated_by, target_ids[])
```

---
## 5. API Surface
- `POST /automation/jobs` → trigger job template
- `GET  /automation/jobs/{id}` → job metadata
- `GET  /automation/jobs/{id}/log` → stream log (SSE)
- `GET  /automation/inventory` → dynamic inventory JSON

---
## 6. Security & Compliance
- Secrets encrypted at rest; decrypted only during runner execution.
- Audit log entry for every job trigger and completion.
- RBAC permissions mapped to existing role system.

---
## 7. Testing Strategy
- Unit: runner wrapper returns expected rc in `check_mode`.
- Integration: spin up test DB, run FastAPI endpoints, assert playbook execution (dry-run).
- Coverage goal: +5 % overall.

---
## 8. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Long-running playbooks blocking workers | Execute runner in Celery task with timeout |
| Credential leakage | Vault integration + temp file cleanup |
| Vendor command drift | Continuous playbook lint + test lab devices |

---
## 9. Next Immediate Tasks (Sprint-ready)
1. Generate Alembic migration for new tables.
2. Create `automation` package with Pydantic models & SQLAlchemy schemas.
3. Implement runner wrapper and basic smoke test.
4. Commit `router_mikrotik` role + sample playbook.
5. Update Outstanding Tasks doc with new section.

---
## 10. Ownership
- Lead: DevOps / Backend Team
- Support: Network Engineering (device templates), Frontend (UI), QA (tests)

---
*Document generated: 2025-07-29*
