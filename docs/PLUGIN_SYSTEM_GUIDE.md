# Plugin System Guide

The ISP Framework introduces an extensible plugin architecture that allows 3rd-party or in-house components to hook into core workflows without modifying the codebase.

## 1. Goals
* Add features (e.g. MikroTik router support, external SMS gateway) on demand.
* Keep the core slim and vendor-agnostic.
* Provide safe enable/disable and versioned migrations.

## 2. Anatomy of a Plugin
```
plugin_package/
├── __init__.py          # must expose `plugin` instance
├── manifest.json        # metadata: name, version, author, hooks
├── models.py            # optional extra tables
├── migrations/          # optional Alembic revisions
└── handlers.py          # hook functions
```

`manifest.json` example:
```json
{
  "name": "mikrotik",
  "version": "1.0.0",
  "description": "MikroTik RouterOS provisioning",
  "hooks": ["service_provision", "device_backup"]
}
```

## 3. Lifecycle
1. **Discovery** – `PluginService` scans `plugins/` directory at startup.
2. **Validation** – Manifest schema & version compatibility checked.
3. **Registration** – Hooks registered in `PluginRegistry` (singleton).
4. **Execution** – Core logic emits events; registry dispatches to hooks.
5. **Disable/Upgrade** – Admin API `/plugins` can deactivate or upgrade.

## 4. Writing a Hook
```python
# handlers.py
from app.plugins import registry

@registry.hook("service_provision")
def provision_mikrotik(service, db):
    # push PPPoE user to RouterOS via API
    ...
```
Hooks receive domain objects and DB session; they can raise `PluginError` to abort the workflow.

## 5. API Endpoints
| Method | Path | Scope | Description |
|--------|------|-------|-------------|
| GET | `/plugins` | `admin` | List installed plugins |
| POST | `/plugins/upload` | `admin` | Upload & install zip |
| PUT | `/plugins/{name}/enable` | `admin` | Enable plugin |
| PUT | `/plugins/{name}/disable` | `admin` | Disable plugin |

## 6. Storage & Security
* Uploaded plugin zips stored in MinIO `plugins/` bucket.
* SHA256 checksum stored for integrity.
* Only admin role with `plugins:manage` permission can install.

## 7. Testing Plugins
* Unit-test hooks with pytest fixtures: `plugin_registry`, `db_session`.
* Integration test via `/plugins/upload` then relevant domain action.

## 8. Future Enhancements
* Semantic-version dependency resolution between plugins.
* Sandboxed execution (Podman) for untrusted plugins.
