# Outstanding Backend & Frontend Tasks
## Alignment with UX Guide and User Journey Documents

This document outlines the remaining work to align the ISP Framework implementation with the comprehensive UX guide and user journey specifications.

---

## Backend Tasks (Priority Order)

### 1. Customer/Service API Separation
**Priority: Critical**
- [ ] Refactor `POST /customers` to accept customer-only schema (remove nested `services`)
- [ ] Add `/customers/{id}/services/internet` endpoint with tariff selection
- [ ] Add `/customers/{id}/services/voice` endpoint with plan configuration  
- [ ] Add `/customers/{id}/services/bundle` endpoint with package options
- [ ] Move provisioning logic from customer service layer to service modules
- [ ] Add RBAC checks for service creation endpoints
- [ ] Unit tests for customer-only creation + separate service addition

### 2. Async Provisioning Queue
**Priority: High**
- [ ] Create `provision_jobs` table (job_id, customer_id, service_type, status, retry_count, scheduled_at)
- [ ] Implement async worker for provisioning tasks
- [ ] Add idempotency keys to prevent duplicate provisioning
- [ ] Retry logic with exponential backoff for failed provisions
- [ ] Manual intervention queue for failed provisions requiring admin attention
- [ ] Webhook notifications on provisioning status changes

### 3. Billing Automation & Proration
**Priority: High**
- [ ] Billing event generator for service lifecycle (activation, suspension, cancellation)
- [ ] Proration calculation engine for mid-cycle service changes
- [ ] Recurring invoice cron with proper cycle handling
- [ ] Invoice batch generation with preview functionality
- [ ] Payment retry scheduler with dunning sequence
- [ ] Commission calculation for reseller billing

### 4. SLA Monitoring & Escalation
**Priority: Medium**
- [ ] SLA breach detection cron job
- [ ] Escalation queue table and API (`/tickets/escalations`)
- [ ] Alert generation on SLA breaches
- [ ] Automatic ticket escalation based on priority and time
- [ ] SLA reporting and analytics endpoints

### 5. API Management & Quotas
**Priority: Medium**
- [ ] API key quota enforcement middleware
- [ ] Daily/monthly usage aggregation job
- [ ] Rate limiting per API key
- [ ] Usage analytics endpoints for reseller dashboard
- [ ] API key rotation functionality

### 6. Plugin System Enhancement
**Priority: Low**
- [ ] Plugin health check endpoints (`/plugins/{id}/health`)
- [ ] Safe plugin reload mechanism (`/plugins/{id}/reload`)
- [ ] Plugin watchdog service for monitoring
- [ ] Plugin marketplace metadata API
- [ ] Dynamic plugin configuration management

### 7. Communications Rule Engine
**Priority: Medium**
- [ ] Expand rule definitions beyond invoices
- [ ] Event emitters for ticket updates, service changes, SLA breaches
- [ ] Template variable expansion for all event types
- [ ] Notification preference enforcement
- [ ] Delivery status tracking and retry logic

### 8. File Storage & Document Management
**Priority: Low**
- [ ] File expiry date column and lifecycle management
- [ ] Customer quota enforcement on uploads
- [ ] Nightly purge job for expired files
- [ ] Signed URL generation for secure downloads
- [ ] File preview/thumbnail generation

### 9. Security & RBAC Enhancement
**Priority: Critical**
- [ ] Row-level security for customer data access
- [ ] Object ownership verification in all repositories
- [ ] Reseller customer isolation enforcement
- [ ] Audit logging for sensitive operations
- [ ] Session management and device tracking

### 10. Real-time Features
**Priority: Medium**
- [ ] WebSocket endpoints for live data updates
- [ ] RADIUS session sync daemon
- [ ] Real-time notification delivery
- [ ] Live dashboard metrics streaming
- [ ] Online customer status tracking

---

## Frontend Tasks (by Portal)

### Admin Portal
- [ ] **Customer Management**
  - [ ] Wizard-based customer creation (3 steps: Basic → Billing → Confirmation)
  - [ ] Customer detail page with tabbed navigation (Overview, Services, Billing, Support, Documents)
  - [ ] Quick action bar (Suspend, Payment, Create Ticket, Edit)
  - [ ] Service addition flows (Internet, Voice, Bundle)
  
- [ ] **Service Management**
  - [ ] Service list table with status indicators and bulk actions
  - [ ] Provisioning queue dashboard with retry/manual intervention
  - [ ] Service configuration forms with tariff selection
  
- [ ] **Billing & Payments**
  - [ ] Batch invoice generation with preview and CSV export
  - [ ] Failed payment center with retry and reminder actions
  - [ ] Payment processing dashboard with analytics
  
- [ ] **Support & Ticketing**
  - [ ] Ticket list with SLA countdown badges
  - [ ] Escalation queue with priority filtering
  - [ ] Ticket detail with timeline and internal/external notes
  
- [ ] **Network Management**
  - [ ] Real-time online customers widget
  - [ ] Router and IP pool utilization dashboards
  - [ ] RADIUS session monitoring

### Reseller Portal
- [ ] **Customer Acquisition**
  - [ ] Lead management and conversion tracking
  - [ ] Customer onboarding wizard
  - [ ] Service recommendation engine
  
- [ ] **Financial Management**
  - [ ] Commission tracking dashboard
  - [ ] Credit utilization monitoring
  - [ ] Payment due notifications
  
- [ ] **API Management**
  - [ ] API key creation and management
  - [ ] Usage analytics and quota monitoring
  - [ ] Rate limiting configuration

### Customer Portal
- [ ] **Account Management**
  - [ ] Self-service profile updates
  - [ ] Service status overview
  - [ ] Usage monitoring and alerts
  
- [ ] **Billing & Payments**
  - [ ] One-click bill payment
  - [ ] Invoice history and downloads
  - [ ] Payment method management
  
- [ ] **Support**
  - [ ] Ticket creation and tracking
  - [ ] Knowledge base integration
  - [ ] Satisfaction rating system

### Cross-Portal Features
- [ ] **Data Tables v2**
  - [ ] Column visibility toggle
  - [ ] Quick filter chips
  - [ ] Advanced bulk actions
  - [ ] Smart pagination with total counts
  - [ ] Virtual scrolling for large datasets
  
- [ ] **Performance & Offline**
  - [ ] Workbox service worker implementation
  - [ ] Multi-level caching strategy
  - [ ] Offline data synchronization
  
- [ ] **Error Handling**
  - [ ] Typed error boundaries with recovery actions
  - [ ] Retry mechanisms for failed operations
  - [ ] User-friendly error messages
  
- [ ] **Accessibility & UX**
  - [ ] WCAG 2.1 AA compliance
  - [ ] Keyboard navigation support
  - [ ] Screen reader optimization
  - [ ] Mobile-responsive design

---

## Testing & Documentation

### Backend Testing
- [ ] Unit tests for all new service layers
- [ ] Integration tests for API endpoints
- [ ] Load testing for provisioning queue
- [ ] Security testing for RBAC implementation

### Frontend Testing
- [ ] Component unit tests with Jest/RTL
- [ ] E2E tests with Playwright covering full user journeys
- [ ] Accessibility testing with axe-core
- [ ] Performance testing with Lighthouse

### Documentation
- [ ] API documentation updates for new endpoints
- [ ] User journey documentation alignment
- [ ] Deployment and configuration guides
- [ ] Troubleshooting and maintenance procedures

---

## Implementation Priority

1. **Phase 1 (Weeks 1-4)**: Critical backend API fixes and customer/service separation
2. **Phase 2 (Weeks 5-8)**: Async provisioning, billing automation, and RBAC security
3. **Phase 3 (Weeks 9-12)**: Admin portal UI alignment with UX guide
4. **Phase 4 (Weeks 13-16)**: Reseller and customer portal implementation
5. **Phase 5 (Weeks 17-20)**: Advanced features, performance optimization, and testing
6. **Phase 6 (Weeks 21-24)**: Documentation, deployment, and production readiness

Each phase includes comprehensive testing and documentation updates to ensure production readiness.
