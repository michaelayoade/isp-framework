# Networking & IPAM Guide

This guide explains the modular, vendor-agnostic networking subsystem integrated into the ISP Framework as of **July 2025**.

## 1. Core Goals
* Single-source of truth for physical sites, routers, sectors and cabling
* Unified IP address management (IPv4 & IPv6) with allocation + utilisation tracking
* Real-time RADIUS session visibility and accounting
* Vendor independence – MikroTik, Cisco, Ubiquiti, etc. handled via plugin layer

## 2. Key Models
| File | Model | Purpose |
|------|-------|---------|
| `app/models/networking/networks.py` | `NetworkSite` | Logical location such as POP or tower |
|  | `Router`, `RouterSector` | Core routing devices & wireless sectors |
|  | `ManagedDevice` | Generic SNMP-manageable device |
|  | `DeviceConnection` | Physical link/cable/fibre between devices |
|  | `IPv4Network`, `IPv4IP`, `IPv6Network`, `IPv6IP` | IP blocks & addresses with allocation flags |
| `app/models/networking/radius.py` | `RadiusSession`, `RadiusAccounting`, `RadiusInterimUpdate` | Session state and accounting packets |

### Relationship diagram
```
NetworkSite 1--* Router 1--* RouterSector
              |            \
              |             *--* ManagedDevice
              *--* DeviceConnection (self-ref via from_device / to_device)

IPv4Network 1--* IPv4IP  *--1 CustomerService (via ServiceIPAssignment)
RadiusSession *--1 CustomerService
```

## 3. IP Address Allocation Flow
1. `ServiceProvisioning` requests free IP from `ServiceIPAssignmentRepository`.
2. Repository queries `IPv4IP`/`IPv6IP` where `is_allocated = false` and assigns.
3. Allocation recorded; `ip_assignment_id` stored on customer service.
4. RADIUS account created; PPPoE credentials pushed to router plugin.

## 4. RADIUS Integration
* FreeRADIUS container defined in `docker-compose.yml` shares DB connection.
* Foreign keys: `radius_sessions.service_id` → `customer_services.id` (fixed).
* Accounting reports feed `ServiceUsageTracking` for billing.

## 5. Migration Strategy from Legacy Models
* Legacy `network.py` models remain but are **deprecated**.
* Data-migration script `migrate_legacy_network.py` (todo) will map old rows to new tables.
* New endpoints live in `api/v1/endpoints/network.py`.

## 6. API Endpoints (Quick Reference)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/network/sites` | List sites |
| POST | `/network/routers` | Register router |
| GET | `/radius/sessions/online` | Active sessions |

See automatic Swagger docs at `/docs` for the full list.

## 7. Future Work
* IPv6 prefix-delegation helper.
* Netbox exporter.
* LLDP discovery agent.
