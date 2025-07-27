# Service Management Guide

This guide details how the ISP Framework provisions, tracks, and manages customer services (Internet, Voice, Bundles, Recurring).

## 1. Core Concepts
* **ServiceTemplate** – what *can* be sold (speed, price, availability)
* **CustomerService** – what *is* sold to a customer (life-cycle)
* **ProvisioningWorkflow** – automation steps to activate / suspend / terminate
* **ServiceIPAssignment** – IP allocation and DHCP/PPPoE bindings
* **ServiceUsageTracking** – bandwidth & quota measurement
* **ServiceAlert** – real-time alerts and SLA breaches

All objects live under `app/models/services/` and have matching repositories & schemas.

## 2. Life-Cycle
```
ServiceTemplate → CustomerService (status = PENDING)
           ↓ create ProvisioningWorkflow
ProvisioningWorkflow runs (router config, RADIUS user, IP assign)
          ↓ success
CustomerService status = ACTIVE → billing kicks in
          ↓ suspension trigger (non-payment)
CustomerService status = SUSPENDED → automated shaping
          ↓ termination
CustomerService status = TERMINATED → IP released, RADIUS disabled
```

## 3. Repository Layer
* All repository classes reside in `app/repositories/` with factory access via `ServiceRepositoryFactory`.
* Search/filter params follow the **filters dict** standard: `{ "field": value, "field__gte": 10 }`.
* Heavy queries use `selectinload` hints for performance.

## 4. API Endpoints (v1)
| Path | Description |
|------|-------------|
| `POST /services/internet` | Provision new internet service |
| `GET  /services` | Search all services |
| `PATCH /services/{id}/suspend` | Suspend service |
| `GET  /services/{id}/usage` | Bandwidth + quota |

Authentication: Bearer token with `api` scope (admin) or customer portal token.

## 5. Alerting & Suspension
* Suspension reasons enumerated in `services.enums.SuspensionReason`.
* Alerts stored in `ServiceAlert`, acknowledged via API.

## 6. Integration with Billing
* `CustomerService` has `tariff_id` foreign key.
* Billing module pulls usage from `ServiceUsageTracking` for prepaid / FUP enforcement.

## 7. Future Work
* Dynamic speed-profile adjustments (Smart FUP).
* Voice-service CDR rating & balance auto-top-up.
