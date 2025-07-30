# Complete Splynx Admin Portal Journey
## Comprehensive Guide to Using the Splynx Admin Interface

### Table of Contents
1. [Login & Initial Setup](#login--initial-setup)
2. [Dashboard Overview](#dashboard-overview)
3. [Main Navigation Structure](#main-navigation-structure)
4. [Customer Management](#customer-management)
5. [Service & Tariff Management](#service--tariff-management)
6. [Billing & Financial Operations](#billing--financial-operations)
7. [Network Management](#network-management)
8. [Support & Ticketing](#support--ticketing)
9. [System Administration](#system-administration)
10. [Reports & Analytics](#reports--analytics)
11. [Configuration & Settings](#configuration--settings)
12. [Daily Admin Workflows](#daily-admin-workflows)

---

## Login & Initial Setup

### 1.1 Accessing the Admin Portal

**URL Format:** `https://yourdomain.com/admin`

**Login Process:**
1. Navigate to your Splynx admin URL
2. Enter administrator credentials
3. Complete 2FA if enabled (SMS/Google Authenticator)
4. Review trusted device options
5. Access main dashboard

**First-Time Setup Checklist:**
- [ ] Change default password
- [ ] Configure 2FA security
- [ ] Set session timeout preferences
- [ ] Upload admin avatar
- [ ] Configure notification preferences

### 1.2 Admin Profile Management

**Location:** *Top-right user menu → Profile Settings*

**Key Settings:**
- Personal information and contact details
- Session timeout (default: 1200 seconds)
- Router access permissions
- UI language preferences
- Dashboard widget configuration

---

## Dashboard Overview

### 2.1 Main Dashboard Components

**Default Widgets Available:**
- **Customer Statistics**: New customers, active/blocked counts
- **Online Status**: Currently connected customers
- **Financial Summary**: Today's revenue, pending payments
- **Support Metrics**: Open tickets, unresolved issues
- **Network Status**: Router connectivity, device alerts
- **Recent Activities**: Latest system changes

### 2.2 Dashboard Customization

**Widget Management:**
1. Click **Options** to see available widgets
2. Enable/disable specific widgets
3. Arrange widgets using drag-and-drop
4. Configure widget refresh intervals
5. Set up custom dashboard views per admin role

**Common Widget Types:**
- **Base Widgets**: Core Splynx functionality
- **Entry Point Widgets**: Custom add-on integrations
- **Third-party Integrations**: External service dashboards

---

## Main Navigation Structure

### 3.1 Primary Navigation Menu

**Core Menu Sections:**

#### 📊 **Dashboard**
- Main overview dashboard
- Custom dashboard views
- Quick access widgets

#### 👥 **Customers**
- Customer list and search
- Add new customers
- Import/export customers
- Customer categories and labels

#### 🌐 **Services**
- Internet services
- Voice services  
- Bundle services
- One-time services
- Service monitoring

#### 💰 **Billing**
- Invoices management
- Payment processing
- Transactions
- Credit notes
- Accounting reports

#### 📋 **Tariffs**
- Internet tariffs
- Voice tariffs
- Bundle tariffs
- CAP tariffs
- Discount plans

#### 🔧 **Network**
- Routers & NAS
- Monitoring devices
- IP management
- Online customers
- Network maps

#### 🎫 **Support**
- Tickets management
- Messages & communication
- Ticket groups and types
- SLA tracking

#### ⚙️ **Administration**
- User management
- Locations
- Partners
- System logs
- API keys

#### 📊 **Reports**
- Financial reports
- Customer reports
- Service statistics
- Network analytics

#### 🔧 **Config**
- System configuration
- Templates (email/SMS)
- Scheduling
- Integrations

---

## Customer Management

### 4.1 Customer List Interface

**Navigation:** *Customers → View Customers*

**Key Features:**
- **Search & Filters**: Portal ID, name, email, status, location, tariff
- **Column Customization**: Show/hide customer fields
- **Bulk Actions**: Mass status changes, billing operations
- **Export Options**: CSV, PDF reports
- **Quick Actions**: Edit, view services, create invoice

**Customer Identification:**
- **Primary**: Portal ID/Username (unique system identifier)
- **Secondary**: Customer name, email, phone, account number
- **Service Integration**: Portal ID links to network authentication
- **Support Integration**: Portal ID used for ticket identification

**Customer Status Indicators:**
- 🟢 **New**: Recently added customers
- 🔵 **Active**: Customers with active services
- 🟡 **Suspended**: Temporarily suspended (payment/policy issues)
- 🔴 **Inactive**: Permanently disabled customers
- ⚪ **Pending**: Awaiting activation or approval

### 4.2 Customer Profile Management

**Customer Information Tabs:**

#### **Main Info**
- Personal/company details
- Primary contact information
- **Flexible Contact Management**: Configurable contact system
  - Add contacts as needed (no predefined limits)
  - Configurable contact types and roles per ISP requirements
  - Custom contact permissions and notification preferences
  - Dynamic contact validation rules
- Billing address and service location
- Custom fields and account notes

#### **Contact Management System (Configurable)**
**Dynamic Contact Configuration:**
- **Contact Types**: ISP-configurable (examples: Billing, Technical, Emergency, Legal, etc.)
- **Contact Permissions**: Role-based access per contact type (configurable)
- **Notification Rules**: Custom notification routing per contact type
- **Validation Requirements**: Configurable verification rules per contact
- **Contact Limits**: Configurable maximum contacts per account (default: unlimited)

**Contact Operations:**
- Add/edit/remove contacts based on account needs
- Assign configurable roles and permissions per contact
- Set communication preferences per contact
- Audit trail for contact changes with configurable retention
- Bulk contact operations with configurable validation rules

#### **Services**
- Active service subscriptions
- Service status and configuration
- Network settings (IP, router, equipment)
- Service usage statistics
- **Equipment Management**: Customer premises equipment tracking
  - Equipment inventory and serial numbers
  - Installation/replacement history
  - Equipment status and health monitoring
  - Return/recovery tracking upon termination

#### **Service Provisioning Workflow**
**Automated Provisioning:**
- RADIUS account creation
- IP address allocation from available pools
- Network equipment configuration
- Service activation and testing

**Manual Provisioning (when automation fails):**
- Equipment installation scheduling
- Technician dispatch and coordination
- Field installation completion tracking
- Service testing and customer acceptance

**Provisioning Failure Handling:**
- RADIUS server connectivity issues
- IP pool exhaustion procedures
- Equipment unavailability workflows
- Installation appointment rescheduling
- Customer communication during delays

#### **Billing**
- Invoice history and status tracking
- Payment methods and processing
- Transaction log and audit trail
- Credit/debit balance management
- Proforma invoices and prepayments
- **Payment Failure Management (Configurable)**:
  - **Retry Schedule**: Configurable retry intervals (default: Day 1, 3, 7, 14)
  - **Retry Attempts**: Configurable number of retry attempts (1-10)
  - **Grace Periods**: Configurable grace period before suspension (0-90 days)
  - **Notification Timeline**: Configurable notification schedule and channels
  - **Escalation Rules**: Configurable escalation to management/collections
  - **Payment Method Fallback**: Configurable fallback sequence priority

#### **Financial Operations**
**Payment Processing Workflow:**
- Real-time payment validation
- Payment gateway failover procedures
- Failed payment notification sequence
- Automatic retry configuration
- Manual payment override capabilities

**Suspension & Restoration Process (Configurable):**
- **Grace Period**: Configurable grace period enforcement (0-90 days)
- **Suspension Options**: Configurable suspension types (speed reduction %, full suspension, service-specific)
- **Notification Timeline**: Configurable customer notification schedule (email, SMS, calls)
- **Restoration Triggers**: Configurable automatic restoration rules (payment amount, timing)
- **Manual Override**: Configurable manual restoration workflow and approval levels
- **Service Impact**: Configurable service degradation levels vs complete suspension

#### **Tickets**
- Support ticket history
- Open issues
- Communication thread
- SLA tracking

#### **Files**
- Uploaded documents
- Contracts and agreements
- Identity verification
- Service agreements

#### **Maps**
- Customer location
- Service installation address
- Network coverage area

### 4.3 Adding New Customers

**Navigation:** *Customers → Add Customer*

**Multi-Step Process:**

1. **Personal Information**
   - Customer type (Person/Company)
   - Name and contact details
   - Address information  
   - Partner assignment
   - **Portal ID Generation**: Auto-generated unique identifier

2. **Account Configuration**
   - Portal access credentials setup
   - Communication preferences
   - Billing configuration
   - Security settings

3. **Service Assignment**
   - Select internet tariff
   - Configure network settings
   - Add additional services
   - Set activation date

4. **Final Setup**
   - Custom fields completion
   - Customer labels assignment
   - Notes and comments
   - Welcome communication setup

---

## Service & Tariff Management

### 5.1 Tariff Plans Configuration

**Navigation:** *Tariffs → Internet Tariffs*

**Tariff Configuration Options:**

#### **Basic Settings**
- Tariff name and description
- Partner availability
- Price and VAT settings
- Service activation

#### **Speed Configuration**
- Download speed (kbps)
- Upload speed (kbps)
- Speed limit percentage
- Burst settings
- Aggregation ratio

#### **Fair Usage Policy (FUP)**
- Data allowance limits
- Speed reduction after limit
- Reset periods (daily/monthly)
- Top-up options

#### **Network Settings**
- IP pool assignment
- Router configuration
- VLAN settings
- Quality of Service (QoS)

### 5.2 Service Management

**Customer Services Overview:**

#### **Internet Services**
- Service status monitoring (Pending, Active, Suspended, Terminated)
- Speed testing and verification
- Session management
- Usage tracking

#### **Voice Services**
- Call routing configuration (Active, Suspended, Terminated)
- Number assignment
- Billing rates
- Call logs

#### **Bundle Services**
- Combined service packages (Active, Suspended, Terminated)
- Bundled pricing
- Discount application
- Service dependencies

---

## Billing & Financial Operations

### 6.1 Invoice Management

**Navigation:** *Billing → Invoices*

**Invoice Operations:**

#### **Creating Invoices**
- Manual invoice generation
- Bulk invoice creation
- Proforma invoice conversion
- Recurring invoice setup

#### **Invoice Processing**
- PDF generation and customization
- Email delivery
- Payment tracking
- Collection management

#### **Invoice Templates**
- Custom invoice layouts
- Company branding
- Multi-language support
- Legal compliance formatting

### 6.2 Payment Processing

**Navigation:** *Billing → Payments*

**Payment Methods:**
- Cash payments
- Bank transfers
- Credit/debit cards
- Online payment gateways
- Cryptocurrency (if enabled)

**Payment Operations:**
- Manual payment entry
- Automatic payment matching
- Refund processing
- Payment plan setup

### 6.3 Financial Reporting

**Available Reports:**
- Revenue reports
- Outstanding payments
- Customer aging reports
- Tax reports
- Accounting exports

---

## Network Management

### 7.1 Network Device Monitoring

**Navigation:** *Network → Routers*

**Device Management Features:**

#### **Router Configuration**
- Device connection settings
- SNMP configuration
- Authentication credentials
- Network interface monitoring

#### **Device Monitoring**
- Real-time status
- Performance metrics
- Bandwidth utilization
- Alert configuration

#### **Customer Sessions**
- Active connections
- Session history
- Bandwidth usage
- Connection quality

### 7.2 IP Address Management

**Navigation:** *Network → IP Management*

**IPAM Features:**
- IPv4/IPv6 pool management
- Automatic IP assignment
- Static IP configuration
- Network topology mapping

### 7.3 Online Customer Monitoring

**Navigation:** *Network → Online Customers*

**Monitoring Capabilities:**
- Real-time connection status
- Bandwidth consumption
- Session duration
- Device information
- Quality metrics

---

## Support & Ticketing

### 8.1 Ticket Management

**Navigation:** *Support → Tickets*

**Ticket Interface Features:**

#### **Ticket List View**
- Priority indicators
- Status colors
- Assignment tracking
- SLA countdown
- Quick actions

#### **Ticket Detail View**
- Complete conversation thread
- File attachments
- Status change history
- Time tracking
- Customer information panel

### 8.2 Ticket Configuration

**Ticket Settings:**

#### **Ticket Statuses**
- Custom status definitions with consistent terminology
- Status workflow configuration (New → Assigned → In Progress → Resolved → Closed)
- Color coding and dashboard integration
- SLA time tracking per status

#### **Ticket Groups**
- Department organization and assignment
- Agent assignment and escalation rules
- SLA configuration per group
- Access permissions and routing

#### **Ticket Types**
- Service categories with configurable priorities
- Auto-assignment rules and routing
- Custom SLA definitions per type
- Priority levels: Low, Medium, High, Urgent, Emergency

#### **SLA Configuration**
**Configurable SLA Framework:**
- Response time targets (configurable per priority/type)
- Resolution time targets (configurable per priority/type)
- Escalation triggers (configurable time thresholds)
- Business hours configuration
- Holiday calendar integration
- SLA breach notification rules

**Example SLA Configuration:**
```
Priority: High
Response Time: 2 hours (configurable)
Resolution Time: 24 hours (configurable)
Escalation: 4 hours (configurable)
Business Hours: Mon-Fri 9AM-6PM (configurable)
```

### 8.3 Communication Templates

**Navigation:** *Config → Templates*

**Template Types:**
- Email templates
- SMS templates
- Ticket responses
- Notification messages
- Document templates

---

## System Administration

### 9.1 Administrator Management

**Navigation:** *Administration → Administrators*

**Admin Account Features:**
- Role-based permissions
- Partner restrictions
- Session management
- Activity monitoring
- Password policies

**Available Roles:**
- Super Administrator
- Administrator
- Manager
- Support Agent
- Read-only Access

### 9.2 Location Management

**Navigation:** *Administration → Locations*

**Location Configuration:**
- Service area definitions
- Geographic boundaries
- Timezone settings
- Tax zone assignment
- Service availability

### 9.3 Partner Management

**Navigation:** *Administration → Partners*

**Partner Features:**
- Reseller configuration
- Commission tracking
- Custom branding
- Service restrictions
- Financial controls

---

## Reports & Analytics

### 10.1 Financial Reports

**Available Reports:**
- Revenue analysis
- Payment collection reports
- Tax reports
- Profit & loss statements
- Customer lifetime value

### 10.2 Customer Reports

**Report Types:**
- Customer growth analytics
- Service subscription trends
- Customer satisfaction metrics
- Churn analysis
- Geographic distribution

### 10.3 Network Reports

**Network Analytics:**
- Bandwidth utilization
- Device performance
- Service quality metrics
- Capacity planning
- Outage reports

---

## Configuration & Settings

### 11.1 System Configuration

**Core Settings:**

#### **Company Information**
- Organization details
- Contact information
- Logo and branding
- Legal information

#### **Billing Configuration**
- Currency settings
- Tax configuration
- Payment terms
- Invoice numbering

#### **Email/SMS Settings**
- SMTP configuration
- SMS gateway setup
- Template management
- Delivery tracking

### 11.2 API Configuration

**Navigation:** *Administration → API Keys*

**API Management:**
- Key generation
- Permission assignment
- Usage monitoring
- Security settings

### 11.3 Integration Setup

**Available Integrations:**
- Payment gateways
- SMS providers
- Email services
- Accounting systems
- Monitoring tools

---

## Daily Admin Workflows

### 12.1 Morning Routine

**Daily Checklist:**
1. **Dashboard Review**
   - Check overnight alerts
   - Review new customers
   - Monitor service status
   - Check financial metrics

2. **Network Monitoring**
   - Verify device status
   - Check for outages
   - Review capacity utilization
   - Update maintenance schedules

3. **Customer Service**
   - Review new tickets
   - Check urgent issues
   - Update ticket statuses
   - Schedule follow-ups

### 12.2 Billing Operations

**Monthly Billing Cycle:**
1. **Pre-billing Checks**
   - Verify customer data
   - Update service changes
   - Check payment methods
   - Review discount applications

2. **Invoice Generation**
   - Run billing process
   - Review generated invoices
   - Send invoice notifications
   - Update payment tracking

3. **Collection Management**
   - Review overdue accounts
   - Process payments
   - Handle disputes
   - Update customer status

### 12.3 Customer Support

**Support Workflow:**
1. **Ticket Triage**
   - Prioritize by urgency
   - Assign to appropriate agents
   - Check SLA compliance
   - Escalate critical issues

2. **Issue Resolution**
   - Investigate problems
   - Coordinate with technical teams
   - Update customers
   - Document solutions

3. **Follow-up Actions**
   - Confirm resolution
   - Update knowledge base
   - Process any required credits
   - Close completed tickets

### 12.4 End-of-Day Review

**Daily Wrap-up:**
- Review day's activities
- Check pending approvals
- Schedule tomorrow's tasks
- Backup critical data
- Review security logs

---

## Data Consistency & System Integration

### 10.1 Real-time vs Batch Processing

**Real-time Operations:**
- Customer status changes (immediate RADIUS update)
- Service suspension/restoration (immediate network impact)
- Payment processing (immediate account balance update)
- Critical notifications (immediate delivery)

**Batch Processing Schedule (Configurable):**
- **Usage Data Collection**: Configurable interval (default: 15 minutes, range: 5-60 minutes)
- **Billing Calculations**: Configurable time (default: 2:00 AM, customizable per timezone)
- **Commission Calculations**: Configurable schedule (default: daily 3:00 AM, options: daily/weekly/monthly)
- **Report Generation**: Configurable intervals (dashboard: 5-60 minutes, detailed: hourly/daily/weekly)
- **Data Backups**: Configurable frequency (default: 6 hours, range: 1-24 hours)
- **Cache Refresh**: Configurable intervals (dashboard: 1-60 minutes, reports: 15 minutes - 24 hours)

**Data Synchronization:**
- RADIUS sync delay: Up to 30 seconds
- Billing data lag: Up to 1 hour for usage-based charges
- Dashboard refresh: 5-minute intervals
- Cross-system integration: Up to 15 minutes for complex workflows

### 10.2 Failure Handling & Recovery

**Partial Failure Scenarios:**
- **Customer Created, Service Provisioning Failed**:
  - Customer marked as "Pending" status
  - Automatic retry every 30 minutes for 24 hours
  - Manual intervention notification after 3 failed attempts
  - Rollback option to remove customer if provisioning impossible

- **Payment Processed, Service Activation Failed**:
  - Payment held in escrow status
  - Automatic activation retry every 15 minutes
  - Customer notification of processing delay
  - Manual refund option if activation fails permanently

- **Bulk Operations with Partial Failures**:
  - Detailed success/failure reporting per item
  - Automatic retry queue for failed items
  - Manual intervention queue for complex failures
  - Rollback capabilities for completed items if needed

**System Recovery Procedures:**
- Database transaction rollback for critical failures
- Service state consistency checks every hour
- Automatic reconciliation between systems
- Manual intervention workflows for complex inconsistencies

---

## Business Continuity & Compliance

### 11.1 Service Continuity Planning

**System Outage Procedures:**
- Customer communication via SMS/email (backup providers)
- Service status page updates (external hosting)
- Payment processing via backup gateways
- Support ticket creation via alternative channels
- Emergency contact procedures for critical customers

**Disaster Recovery:**
- Real-time database replication to backup site
- Service restoration priority levels (critical > business > residential)
- Recovery time objectives (RTO): 4 hours for core services
- Recovery point objectives (RPO): 15 minutes data loss maximum
- Staff notification and coordination procedures

### 11.2 Regulatory Compliance Framework

**Data Retention Policies (Configurable):**
- **Customer Data**: Configurable retention period (default: 7 years, range: 1-10 years)
- **Financial Records**: Configurable retention (default: 10 years, min: local tax law requirements)
- **Usage Logs**: Configurable retention (default: 2 years, range: 6 months - 5 years)
- **Support Communications**: Configurable retention (default: 3 years, range: 1-7 years)
- **System Logs**: Configurable retention (default: 1 year, range: 3 months - 3 years)
- **Audit Trails**: Configurable retention based on compliance requirements

**Audit & Compliance:**
- Automated compliance reporting (monthly/quarterly)
- Data protection impact assessments
- Regular security audits and penetration testing
- Customer data deletion procedures (GDPR compliance)
- Cross-border data transfer documentation

**Legal & Regulatory Requirements:**
- Lawful interception capabilities (where required)
- Data localization compliance
- Financial reporting obligations
- Customer privacy protection measures
- Industry-specific compliance monitoring

---

## Performance & Integration Management

### 12.1 System Performance Monitoring

**Performance Limits & Monitoring:**
- Concurrent portal users: 10,000 (auto-scaling beyond)
- Database query performance: <200ms for 95% of queries
- API response times: <500ms for standard operations
- Large file uploads: 100MB limit with progress tracking
- Report generation: 5-minute timeout for complex reports

**Geographic Performance:**
- CDN integration for static assets
- Regional database read replicas
- Latency monitoring and alerting
- Load balancing across geographic regions

### 12.2 Third-Party Integration Management

**Integration Dependency Monitoring:**
- Payment gateway health checks every 2 minutes
- SMS/email provider failover (3 provider rotation)
- RADIUS server clustering and failover
- API rate limiting and throttling protection
- Vendor SLA monitoring and enforcement

**Integration Failure Handling:**
- Automatic failover to backup providers
- Queue-based retry mechanisms
- Manual intervention alerts for prolonged failures
- Customer communication for service impacts
- Vendor escalation procedures

**API Management:**
- Rate limiting: 1000 requests/hour per API key
- Request throttling during peak loads
- API versioning and backward compatibility
- Integration health monitoring
- Usage analytics and optimization

---

## White-Label & Domain Management

### 13.1 Domain & SSL Management

**Custom Domain Implementation:**
- DNS configuration validation and testing
- Automatic SSL certificate provisioning (Let's Encrypt/Commercial)
- Certificate renewal automation (30 days before expiry)
- Domain verification process (DNS TXT records)
- Subdomain vs full domain configuration options

**Email Delivery Management:**
- SPF/DKIM record setup for branded emails
- Email reputation monitoring and maintenance
- Delivery failure handling and fallback
- Bounce management and list hygiene
- Anti-spam compliance monitoring

### 13.2 Branding Inheritance & Override

**Branding Configuration Hierarchy:**
1. **System Default**: Base ISP branding
2. **Reseller Primary**: Main reseller customization
3. **Sub-Reseller**: Inherits from parent with selective overrides
4. **Customer Experience**: Final rendered result with fallbacks

**Asset Management:**
- Logo upload with automatic resizing and optimization
- Asset CDN distribution for performance
- Fallback asset serving for broken links
- Version control for branding assets
- Quality validation for uploaded assets

---

### System-Wide Status Standards

**Customer Status (Consistent Across All Portals):**
- **New**: Recently created, pending activation
- **Active**: Services operational, account in good standing
- **Suspended**: Temporarily disabled (payment/policy issues)
- **Inactive**: Permanently disabled
- **Pending**: Awaiting external action or approval

**Service Status (Consistent Across All Portals):**
- **Pending**: Awaiting activation
- **Active**: Fully operational
- **Suspended**: Administratively disabled
- **Limited**: FUP or policy restrictions applied
- **Terminated**: Permanently ended

**Ticket Status (Consistent Across All Portals):**
- **New**: Just created, unassigned
- **Assigned**: Assigned to specific agent/team
- **In Progress**: Actively being worked
- **Pending Customer**: Waiting for customer response
- **Escalated**: Moved to higher support tier
- **Resolved**: Solution implemented
- **Closed**: Customer confirmed resolution

**Priority Levels (Consistent Across All Portals):**
- **Emergency**: Critical system/service failure
- **Urgent**: High impact, immediate attention needed
- **High**: Significant impact, prompt resolution required
- **Medium**: Standard business impact
- **Low**: Minor issues, normal queue processing

### Communication Standards
- All portals use identical terminology
- Status descriptions provide context without changing core terms
- Documentation uses consistent language across all interfaces
- Support staff trained on unified terminology

### Keyboard Shortcuts
- **Ctrl + /** : Global search
- **Ctrl + D** : Add to bookmarks
- **Ctrl + H** : Return to dashboard
- **F5** : Refresh current page
- **Ctrl + F** : Find on page

### Quick Actions
- **Customer Quick View**: Hover over customer name
- **Service Status Toggle**: Click status indicators
- **Invoice Quick Actions**: Right-click invoice items
- **Bulk Operations**: Select multiple items + action bar

### Search Features
- **Global Search**: Available in top navigation
- **Advanced Filters**: Use dropdown menus
- **Saved Searches**: Bookmark common searches
- **Quick Filters**: Pre-defined filter buttons

---

## Troubleshooting Common Issues

### Performance Issues
- Clear browser cache
- Disable unnecessary widgets
- Check network connectivity
- Review browser compatibility

### Access Problems
- Verify user permissions
- Check session timeout
- Confirm 2FA setup
- Review IP restrictions

### Data Synchronization
- Refresh affected pages
- Check API connectivity
- Review system logs
- Contact technical support

---

This comprehensive guide provides administrators with everything needed to effectively navigate and utilize the Splynx admin portal for daily ISP management operations.