# API Endpoint Consolidation & RESTful Redesign

## Phase 2: RESTful Design Mapping

**Total Endpoints Analyzed**: 467 across 35 files  
**Router Prefixes**: 26 identified  
**Unknown Mappings**: 86 endpoints need proper router assignment

## Major Consolidation Opportunities

### 1. **Redundant/Verbose Naming Issues**

#### ❌ **Problem: Double Naming**
- `/api-management` → should be `/api` (management is implied)
- `/dead-letter-queue` → should be `/background/failed-tasks` 
- `/service_plans` vs `/service_templates` vs `/service_instances` → consolidate under `/services`

#### ❌ **Problem: Inconsistent Resource Naming**
- `/partners` (should be `/resellers` per business model)
- `/tickets` (should be `/support/tickets`)
- `/customers/services` vs `/services/instances` (duplicate functionality)

#### ❌ **Problem: Non-RESTful Paths**
- `/auth/2fa/api-keys` → should be `/auth/two-factor/keys`
- `/audit/audit-queue` → should be `/audit/queue`
- `/alerts/webhooks/grafana` → should be `/integrations/grafana/alerts`

### 2. **Proposed RESTful Resource Mapping**

#### **Core Business Resources**
```
Current                          →  Proposed RESTful
/auth/*                         →  /auth/* (keep as-is)
/customers/*                    →  /customers/* (good)
/partners/*                     →  /resellers/* (align with business model)
/billing/*                      →  /billing/* (good)
/tickets/*                      →  /support/tickets/*
```

#### **Service Management Consolidation**
```
Current                          →  Proposed RESTful
/services/*                     →  /services/* (base)
/services/plans/*               →  /services/plans/* (deprecated → /services/templates)
/services/templates/*           →  /services/templates/*
/services/instances/*           →  /services/subscriptions/*
/services/provisioning/*        →  /services/provisioning/*
/customers/services/*           →  /customers/{id}/services/* (nested resource)
```

#### **Network & Infrastructure**
```
Current                          →  Proposed RESTful
/network/devices/*              →  /network/devices/*
/network/radius/*               →  /network/radius/*
/alerts/*                       →  /monitoring/alerts/*
/dashboard/*                    →  /monitoring/dashboard/*
```

#### **Platform Services**
```
Current                          →  Proposed RESTful
/api-management/*               →  /api/management/*
/files/*                        →  /files/* (good)
/communications/*               →  /communications/* (good)
/webhooks/*                     →  /integrations/webhooks/*
/background/*                   →  /background/tasks/*
/audit/*                        →  /audit/* (good)
```

### 3. **Specific Path Consolidations**

#### **Authentication Cleanup**
```
/auth/2fa/api-keys              →  /auth/two-factor/keys
/auth/2fa/setup                 →  /auth/two-factor/setup
/auth/portal/*                  →  /auth/portal/* (keep)
/auth/reseller/*                →  /auth/resellers/* (align naming)
```

#### **API Management Simplification**
```
/api-management/keys            →  /api/keys
/api-management/versions        →  /api/versions
/api-management/usage/analytics →  /api/usage/analytics
/api-management/rate-limit/check → /api/rate-limits/check
```

#### **Audit System Cleanup**
```
/audit/audit-queue              →  /audit/queue
/audit/configuration-snapshots  →  /audit/configurations
/audit/cdc-log                  →  /audit/change-log
```

#### **Service Management Unification**
```
/services/instances/{id}        →  /services/subscriptions/{id}
/customers/services/{id}        →  /customers/{customer_id}/services/{id}
/services/plans/*               →  /services/templates/* (deprecate plans)
```

### 4. **Implementation Strategy**

#### **Phase 3A: High-Impact Consolidations (Week 1)**
1. **API Management**: `/api-management/*` → `/api/*`
2. **Service Unification**: Consolidate service plans/templates/instances
3. **Authentication**: Clean up 2FA and reseller auth paths
4. **Audit**: Simplify audit-queue and configuration paths

#### **Phase 3B: Business Alignment (Week 2)**  
1. **Partners → Resellers**: `/partners/*` → `/resellers/*`
2. **Support**: `/tickets/*` → `/support/tickets/*`
3. **Monitoring**: `/alerts/*` + `/dashboard/*` → `/monitoring/*`
4. **Integrations**: `/webhooks/*` → `/integrations/webhooks/*`

#### **Phase 3C: Advanced Consolidations (Week 3)**
1. **Customer Services**: Nested resource pattern `/customers/{id}/services/*`
2. **Background Tasks**: `/background/*` → `/background/tasks/*`
3. **Network**: Ensure consistency in `/network/*` paths
4. **Files**: Validate `/files/*` RESTful compliance

### 5. **Backward Compatibility Strategy**

#### **Redirect Implementation**
- Add `307 Temporary Redirect` for old → new paths
- Maintain redirects for 6 months minimum
- Log usage of deprecated paths for monitoring

#### **API Versioning**
- Keep `/api/v1/` prefix for all endpoints
- Consider `/api/v2/` for major breaking changes
- Document migration path in API docs

### 6. **Quality Metrics**

#### **Before Consolidation**
- 467 total endpoints
- 26 router prefixes
- 86 unmapped endpoints
- Multiple naming inconsistencies

#### **After Consolidation (Target)**
- ~400 endpoints (eliminate duplicates)
- ~20 router prefixes (consolidate related)
- 0 unmapped endpoints
- Consistent RESTful naming

### 7. **Next Steps**

1. **Review & Approval**: Get user approval for consolidation strategy
2. **Implementation Plan**: Detailed file-by-file refactor plan
3. **Testing Strategy**: Update all tests for new paths
4. **Documentation**: Update OpenAPI, Postman, SDKs
5. **Deployment**: Staged rollout with monitoring

---

**Ready for Phase 3 Implementation?** 
This consolidation will significantly improve API consistency, reduce developer confusion, and align with RESTful best practices.
