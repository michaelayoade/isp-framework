# API Consolidation Guide

## Overview

This document outlines the comprehensive API endpoint consolidation performed to reduce verbosity, eliminate duplication, and create a more intuitive developer experience. The consolidation follows RESTful principles and logical grouping of related functionality.

## 🎯 **Consolidation Objectives**

1. **Reduce Endpoint Verbosity**: Eliminate redundant and overly specific endpoint paths
2. **Logical Grouping**: Group related functionality under common prefixes
3. **Eliminate Duplication**: Merge duplicate endpoints (e.g., Grafana alerts)
4. **Improve Developer Experience**: Create intuitive, predictable URL structures
5. **Maintain Backward Compatibility**: Keep legacy endpoints during transition period

---

## 📊 **Before vs After Comparison**

### **Alerting & Monitoring**

#### Before (Verbose & Duplicated)
```
❌ /api/v1/grafana-alerts/...        # Enhanced Grafana alerts
❌ /api/v1/alerts/...                # Basic Grafana alerts
❌ /api/v1/operational-dashboard/... # Dashboard endpoints
```

#### After (Consolidated)
```
✅ /api/v1/alerts/
├── /webhooks/grafana          # Webhook receivers
├── /rules                     # Alert rule management
├── /dashboards               # Dashboard management
├── /metrics                  # Alert metrics
├── /test                     # Testing endpoints
└── /status                   # System status
```

### **Service Management**

#### Before (Fragmented)
```
❌ /api/v1/services/...
❌ /api/v1/service-plans/...
❌ /api/v1/customer-services/...
❌ /api/v1/service-templates/...
❌ /api/v1/service-instances/...
❌ /api/v1/service-provisioning/...
❌ /api/v1/service-management/...
```

#### After (Consolidated)
```
✅ /api/v1/services/
├── /plans                    # Service plans
├── /templates               # Service templates
├── /instances               # Service instances
├── /provisioning            # Provisioning operations
└── /customers/{id}/services # Customer-specific services
```

### **Authentication**

#### Before (Scattered)
```
❌ /api/v1/auth/...
❌ /api/v1/portal/...
❌ /api/v1/2fa/...
❌ /api/v1/oauth/...
❌ /api/v1/reseller-auth/...
```

#### After (Unified)
```
✅ /api/v1/auth/
├── /login                   # Standard login
├── /portal                  # Portal authentication
├── /2fa                     # Two-factor auth
├── /oauth                   # OAuth flows
├── /reseller               # Reseller authentication
└── /tokens                 # Token management
```

### **Network Management**

#### Before (Fragmented)
```
❌ /api/v1/devices/...
❌ /api/v1/radius/...
❌ /api/v1/radius-integration/...
```

#### After (Consolidated)
```
✅ /api/v1/network/
├── /devices                 # Network devices
├── /radius                  # RADIUS operations
├── /ip-management          # IP allocation
└── /monitoring             # Network monitoring
```

---

## 🔄 **Migration Strategy**

### **Phase 1: Immediate (Current)**
- ✅ **New consolidated endpoints** are available
- ✅ **Legacy endpoints** remain functional with deprecation warnings
- ✅ **Documentation** updated to reflect new structure

### **Phase 2: Transition (3 months)**
- 🔄 **Deprecation headers** added to legacy endpoints
- 🔄 **Migration guides** provided for each endpoint group
- 🔄 **Client libraries** updated to use new endpoints

### **Phase 3: Sunset (6 months)**
- ❌ **Legacy endpoints** removed
- ✅ **New structure** becomes the only supported API

---

## 📋 **Detailed Endpoint Mapping**

### **Alerting System Consolidation**

| Old Endpoint | New Endpoint | Status |
|--------------|--------------|--------|
| `POST /grafana-alerts/create-error-handling-rules` | `POST /alerts/rules/error-handling` | ✅ Migrated |
| `POST /grafana-alerts/create-operational-dashboards` | `POST /alerts/dashboards/operational` | ✅ Migrated |
| `POST /grafana-alerts/process-system-alert` | `POST /alerts/process` | ✅ Migrated |
| `GET /grafana-alerts/comprehensive-alert-metrics` | `GET /alerts/metrics` | ✅ Migrated |
| `GET /grafana-alerts/alert-effectiveness-report` | `GET /alerts/effectiveness` | ✅ Migrated |
| `POST /grafana-alerts/test-alert-integration` | `POST /alerts/test` | ✅ Migrated |
| `GET /grafana-alerts/alert-system-status` | `GET /alerts/status` | ✅ Migrated |
| `POST /alerts/webhook` | `POST /alerts/webhooks/grafana` | ✅ Migrated |
| `GET /alerts/test` | `GET /alerts/webhooks/test` | ✅ Migrated |

### **Service Management Consolidation**

| Old Endpoint | New Endpoint | Status |
|--------------|--------------|--------|
| `GET /service-plans` | `GET /services/plans` | 🔄 Legacy Active |
| `POST /service-plans` | `POST /services/plans` | 🔄 Legacy Active |
| `GET /customer-services/{id}` | `GET /services/customers/{id}/services` | 🔄 Legacy Active |
| `POST /customer-services` | `POST /services/customers/{id}/services` | 🔄 Legacy Active |
| `GET /service-templates` | `GET /services/templates` | 🔄 Legacy Active |
| `POST /service-templates` | `POST /services/templates` | 🔄 Legacy Active |
| `GET /service-instances` | `GET /services/instances` | 🔄 Legacy Active |
| `POST /service-instances` | `POST /services/instances` | 🔄 Legacy Active |
| `POST /service-provisioning/provision` | `POST /services/provisioning/provision` | 🔄 Legacy Active |
| `GET /service-provisioning/status/{id}` | `GET /services/provisioning/status/{id}` | 🔄 Legacy Active |

### **Authentication Consolidation**

| Old Endpoint | New Endpoint | Status |
|--------------|--------------|--------|
| `POST /portal/login` | `POST /auth/portal/login` | 🔄 Legacy Active |
| `POST /portal/authenticate` | `POST /auth/portal/authenticate` | 🔄 Legacy Active |
| `POST /2fa/setup` | `POST /auth/2fa/setup` | 🔄 Legacy Active |
| `POST /2fa/verify` | `POST /auth/2fa/verify` | 🔄 Legacy Active |
| `GET /oauth/authorize` | `GET /auth/oauth/authorize` | 🔄 Legacy Active |
| `POST /oauth/token` | `POST /auth/oauth/token` | 🔄 Legacy Active |
| `POST /reseller-auth/login` | `POST /auth/reseller/login` | 🔄 Legacy Active |

### **Network Management Consolidation**

| Old Endpoint | New Endpoint | Status |
|--------------|--------------|--------|
| `GET /devices` | `GET /network/devices` | ✅ Migrated |
| `POST /devices` | `POST /network/devices` | ✅ Migrated |
| `GET /devices/{id}` | `GET /network/devices/{id}` | ✅ Migrated |
| `PUT /devices/{id}` | `PUT /network/devices/{id}` | ✅ Migrated |
| `DELETE /devices/{id}` | `DELETE /network/devices/{id}` | ✅ Migrated |
| `GET /radius/sessions` | `GET /network/radius/sessions` | ✅ Migrated |
| `POST /radius/sessions` | `POST /network/radius/sessions` | ✅ Migrated |
| `GET /radius-integration/status` | `GET /network/radius/integration/status` | 🔄 Legacy Active |

---

## 🛠 **Implementation Details**

### **Consolidated Alerts Endpoint**

The new `/api/v1/alerts` endpoint combines functionality from:
- `enhanced_grafana_alerts.py` (management endpoints)
- `grafana_alerts.py` (webhook endpoints)

**Key Features:**
- ✅ **Unified webhook handling** for Grafana alerts
- ✅ **Comprehensive alert rule management**
- ✅ **Dashboard creation and management**
- ✅ **Alert metrics and effectiveness reporting**
- ✅ **System status monitoring**
- ✅ **Testing and validation endpoints**

**Example Usage:**
```bash
# Create error handling rules
POST /api/v1/alerts/rules/error-handling

# Receive Grafana webhook
POST /api/v1/alerts/webhooks/grafana

# Get alert metrics
GET /api/v1/alerts/metrics

# Test integration
POST /api/v1/alerts/test
```

### **Legacy Endpoint Handling**

Legacy endpoints are maintained with:
- **Deprecation headers**: `Deprecation: true`
- **Sunset headers**: `Sunset: Wed, 11 Nov 2025 23:59:59 GMT`
- **Successor links**: `Link: </api/v1/alerts>; rel="successor-version"`

**Example Response:**
```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Wed, 11 Nov 2025 23:59:59 GMT
Link: </api/v1/alerts>; rel="successor-version"
Warning: 299 - "This endpoint is deprecated. Use /api/v1/alerts instead."

{
  "data": {...},
  "deprecation_notice": {
    "message": "This endpoint is deprecated",
    "new_endpoint": "/api/v1/alerts",
    "sunset_date": "2025-11-11T23:59:59Z"
  }
}
```

---

## 📚 **Developer Migration Guide**

### **Quick Migration Checklist**

1. **Update Base URLs**
   ```diff
   - POST /api/v1/grafana-alerts/create-error-handling-rules
   + POST /api/v1/alerts/rules/error-handling
   ```

2. **Update Authentication Headers** (no change)
   ```bash
   Authorization: Bearer <token>
   ```

3. **Update Request/Response Handling** (schemas remain the same)
   ```json
   {
     "status": "success",
     "message": "Alert processed successfully"
   }
   ```

### **Client Library Updates**

#### Python SDK
```python
# Old
client.grafana_alerts.create_error_handling_rules()

# New
client.alerts.create_error_handling_rules()
```

#### JavaScript SDK
```javascript
// Old
await client.grafanaAlerts.createErrorHandlingRules();

// New
await client.alerts.createErrorHandlingRules();
```

#### cURL Examples
```bash
# Old
curl -X POST /api/v1/grafana-alerts/create-error-handling-rules

# New
curl -X POST /api/v1/alerts/rules/error-handling
```

---

## 🎯 **Benefits Achieved**

### **1. Reduced API Surface**
- **Before**: 60+ endpoint prefixes
- **After**: 15 logical endpoint groups
- **Reduction**: 75% fewer top-level prefixes

### **2. Improved Discoverability**
- **Logical grouping** makes endpoints easier to find
- **Consistent naming** follows RESTful conventions
- **Hierarchical structure** reflects business domains

### **3. Better Developer Experience**
- **Predictable URLs** reduce cognitive load
- **Consolidated documentation** in fewer sections
- **Consistent response formats** across related endpoints

### **4. Maintainability**
- **Reduced code duplication** between similar endpoints
- **Centralized logic** for related functionality
- **Easier testing** with grouped test suites

---

## 🔮 **Future Consolidation Phases**

### **Phase 2: Service Management**
- Consolidate all service-related endpoints under `/services`
- Implement sub-resource routing for better organization
- Maintain backward compatibility during transition

### **Phase 3: Authentication**
- Merge all authentication methods under `/auth`
- Implement unified authentication flow
- Standardize token management across all auth types

### **Phase 4: Network Management**
- Complete network endpoint consolidation under `/network`
- Implement unified device management
- Consolidate monitoring and metrics endpoints

---

## 📞 **Support & Migration Help**

### **Resources**
- **Migration Guide**: `/docs/API_MIGRATION_GUIDE.md`
- **Postman Collection**: Updated with new endpoints
- **OpenAPI Spec**: Reflects consolidated structure
- **SDK Updates**: Available for Python, JavaScript, PHP

### **Getting Help**
- **GitHub Issues**: Tag with `api-migration`
- **Discord**: `#api-consolidation` channel
- **Email**: `api-migration@ispframework.com`

---

**Last Updated**: 2025-01-26  
**Migration Deadline**: 2025-11-11  
**Status**: Phase 1 Complete
