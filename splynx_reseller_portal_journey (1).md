# Complete Splynx Reseller Portal Journey
## Comprehensive Guide to the Reseller Management System

### Table of Contents
1. [Reseller Portal Access & Authentication](#reseller-portal-access--authentication)
2. [Dashboard & Business Overview](#dashboard--business-overview)
3. [Customer Management](#customer-management)
4. [Service & Pricing Management](#service--pricing-management)
5. [Commission & Financial Tracking](#commission--financial-tracking)
6. [White-Label & Branding](#white-label--branding)
7. [User & Team Management](#user--team-management)
8. [Billing & Invoicing Operations](#billing--invoicing-operations)
9. [Support & Ticket Management](#support--ticket-management)
10. [Reports & Analytics](#reports--analytics)
11. [Sub-Reseller Management](#sub-reseller-management)
12. [Reseller-Specific Workflows](#reseller-specific-workflows)

---

## Reseller Portal Access & Authentication

### 1.1 Portal Access Structure

**Reseller Portal URL:** `https://yourdomain.com/reseller` or `https://reseller.yourbrand.com`

**Access Hierarchy:**
- **Master ISP Admin**: Full system control
- **Reseller Admin**: Full reseller account control
- **Reseller Manager**: Limited administrative access
- **Reseller User**: Customer service and basic operations
- **Readonly**: View-only access to reports and data

### 1.2 Authentication System

**Separate Authentication Infrastructure:**
- Independent user database from main admin system
- Reseller-specific session management
- Role-based access control within reseller scope
- Multi-factor authentication support

**Login Process:**
```http
POST /reseller/auth/login
{
  "username": "reseller_user@abc.com",
  "password": "secure_password",
  "reseller_code": "ABC_ISP",
  "two_factor_code": "123456"
}
```

**Session Management:**
- Concurrent session control (configurable per user)
- IP whitelisting for enhanced security
- Session timeout configuration
- Activity-based session renewal

### 1.3 User Roles & Permissions

**Reseller Admin:**
- Full customer management
- Pricing and service configuration
- User management within reseller
- Financial operations and reporting
- Sub-reseller creation (if enabled)

**Reseller Manager:**
- Customer creation and modification
- Service provisioning
- Basic financial operations
- Team supervision
- Report generation

**Reseller User:**
- Customer support operations
- Service status monitoring
- Basic customer modifications
- Ticket management
- Payment processing

**Readonly:**
- View customer information
- Access reports and analytics
- Monitor service status
- View financial summaries

---

## Dashboard & Business Overview

### 2.1 Reseller Dashboard

**Key Performance Indicators:**
- **Customer Metrics**: Total customers, active/inactive status
- **Revenue Tracking**: Monthly revenue, commission earned
- **Service Overview**: Service distribution, utilization rates
- **Support Metrics**: Open tickets, resolution times
- **Financial Status**: Account balance, credit utilization

**Real-time Widgets:**
- Customer growth chart
- Commission earnings trend
- Service status overview
- Outstanding payments
- Recent activities

### 2.2 Business Summary

**Account Overview:**
- Reseller account status and health
- Credit limit and current balance
- Commission rates and earnings
- Customer allocation (current vs maximum)
- Service authorization status

**Quick Actions:**
- Add new customer
- Process payment
- Create support ticket
- Generate reports
- Manage pricing

### 2.3 Notification Center

**Reseller-Specific Notifications:**
- New customer activations requiring attention
- Commission payments processed
- Credit limit warnings
- Service suspension alerts
- System maintenance notifications
- Policy updates from master ISP

---

## Customer Management

### 3.1 Customer Overview

**Customer List Management:**
- **Scope**: Only customers assigned to the reseller
- **Filters**: Portal ID, status, service type, location, payment status
- **Actions**: Create, modify, suspend, terminate
- **Bulk Operations**: Mass status changes, service updates

**Customer Identification & Support:**
- **Primary**: Portal ID/Username (unique system identifier)
- **Service Integration**: Portal ID used for network authentication
- **Support Reference**: Portal ID for ticket identification and escalation
- **Billing Integration**: Portal ID links to invoices and payments

**Customer Information Access:**
- Full customer profile management
- **Flexible Contact Management**: Add contacts as needed per customer requirements
  - Configurable contact types based on ISP settings
  - Dynamic contact roles and permissions
  - Custom notification routing per contact
  - No predefined contact limits or mandatory types
- Service configuration and monitoring
- Billing and payment history
- Support ticket access and management
- Usage analytics and reporting
- Equipment tracking and management

### 3.2 Customer Creation Process

**Multi-Step Customer Onboarding:**

#### Step 1: Basic Information
```json
{
  "customer_type": "person", // person, company
  "first_name": "John",
  "last_name": "Doe", 
  "email": "john@example.com",
  "phone": "+1234567890",
  "address": "123 Main St",
  "city": "Lagos",
  "reseller_id": 1,
  "portal_id": "auto-generated", // System generates unique Portal ID
  "generate_credentials": true // Auto-generate portal password
}
```

#### Step 2: Service Selection
- Available services (filtered by reseller permissions)
- Custom pricing application
- Service configuration
- Installation scheduling

#### Step 3: Billing Setup
- Payment method configuration
- Billing cycle selection
- Deposit requirements
- Credit limits

#### Step 4: Access & Security Setup
- **Portal Access**: Auto-generated Portal ID and initial portal password
- **Network Access**: Separate network credentials for internet service
- **Security Settings**: Password policies and access controls
- **Communication**: Welcome email with portal access instructions
- **Service Integration**: Network credentials configured for internet access

**Credential Management:**
- Portal credentials: Customer can manage (portal access)
- Network credentials: Reseller/ISP managed (service access)
- Password reset capabilities per credential type
- Integration with RADIUS authentication system

### 3.3 Customer Lifecycle Management

**Status Management:**
- **New**: Recently added, pending activation
- **Active**: Services operational
- **Suspended**: Temporary service interruption (payment/policy issues)
- **Inactive**: Permanently closed
- **Pending**: Awaiting activation or approval

**Service Operations:**
- Service upgrades/downgrades
- Additional service provisioning
- Temporary service holds
- Service relocation requests

### 3.4 Customer Support Interface

**Integrated Support:**
- View customer support history
- Create tickets on behalf of customers
- Monitor ticket resolution progress
- Access customer communication logs
- Escalate issues to master ISP support

---

## Service & Pricing Management

### 4.1 Service Portfolio

**Available Services:**
- Services authorized for the reseller
- Service categories and types
- Feature availability matrix
- Regional service restrictions

**Service Configuration:**
- Internet service speeds and plans
- Voice service features
- Bundle packages
- Value-added services

### 4.2 Custom Pricing Structure

**Pricing Models:**
- **Markup-based**: Percentage or fixed markup on wholesale prices
- **Fixed Pricing**: Set retail prices independent of wholesale
- **Tiered Pricing**: Different rates based on volume or customer type
- **Promotional Pricing**: Temporary special offers

**Pricing Configuration:**
```json
{
  "reseller_id": 1,
  "service_type": "internet",
  "tariff_id": 5,
  "markup_type": "percent",
  "markup_value": 25.00,
  "min_price": 50.00,
  "max_price": 200.00,
  "effective_from": "2024-01-01",
  "promotional_pricing": {
    "enabled": true,
    "discount_percent": 10,
    "valid_until": "2024-03-31"
  }
}
```

### 4.3 Service Provisioning

### 4.3 Service Provisioning & Equipment Management

**Automated Provisioning:**
- Real-time service activation for standard services
- RADIUS account creation and network resource allocation
- IP address assignment from reseller-allocated pools
- Customer notification workflows upon successful activation
- Service testing and validation automation

**Manual Provisioning & Field Operations:**
- Complex service configurations requiring manual setup
- **Equipment Management**:
  - Customer premises equipment (CPE) inventory tracking
  - Installation appointment scheduling and technician coordination
  - Equipment delivery and installation status tracking
  - Equipment failure replacement workflows
  - Equipment recovery upon service termination

**Provisioning Failure Handling:**
- **RADIUS Integration Issues**: Automatic retry with escalation to master ISP
- **IP Pool Exhaustion**: Notification and additional pool request process  
- **Equipment Unavailability**: Alternative equipment sourcing and customer communication
- **Installation Delays**: Customer notification and rescheduling coordination
- **Network Configuration Issues**: Technical escalation to master ISP engineering

**Installation & Field Coordination:**
- Technician dispatch and tracking system integration
- Customer premises access coordination
- Installation completion verification and testing
- Customer training and orientation scheduling
- Service acceptance and quality assurance procedures

---

## Commission & Financial Tracking

### 5.1 Commission Structure

**Commission Types:**
- **Setup Commissions**: One-time payments for new customers
- **Recurring Commissions**: Monthly percentage of customer payments
- **Usage Commissions**: Based on customer usage patterns
- **Retention Bonuses**: Rewards for customer loyalty
- **Performance Incentives**: Volume-based bonus structures

**Commission Calculation:**
```json
{
  "commission_id": 1,
  "reseller_id": 1,
  "customer_id": 123,
  "commission_type": "recurring",
  "base_amount": 99.99,
  "commission_rate": 15.00,
  "commission_amount": 14.99,
  "period_start": "2024-01-01",
  "period_end": "2024-01-31",
  "status": "approved"
}
```

### 5.2 Financial Dashboard

**Revenue Tracking:**
- Monthly/quarterly/annual revenue summaries
- Commission earnings breakdown
- Payment collection rates
- Outstanding receivables
- Customer lifetime value analysis

**Financial Health Metrics:**
- Customer acquisition cost
- Average revenue per customer
- Churn rate impact on revenue
- Service profitability analysis
- Seasonal trend analysis

### 5.3 Commission Payment & Processing

**Commission Payment Schedule (Configurable per Reseller):**
- **Payment Frequency**: Configurable (monthly, quarterly, bi-annual, annual)
- **Payment Timing**: Configurable processing date (1st-28th of month)
- **Minimum Threshold**: Configurable minimum payment amount ($50-$1000)
- **Payment Methods**: Configurable options (bank transfer, wire, check, digital wallet)
- **Payment Currency**: Configurable currency and conversion timing

**Payment Processing Workflow:**
- Commission calculation and verification period (1-15th of month)
- Dispute resolution window (5 business days)
- Payment approval and processing (15th-20th of month)
- Payment confirmation and receipt delivery

**Financial Integration:**
- Banking integration for direct transfers
- Tax documentation and 1099 generation (US)
- VAT handling for international resellers
- Currency conversion at payment time (not calculation time)
- Multi-currency support for international operations

**Commission Dispute Resolution:**
- Online dispute submission with supporting documentation
- 30-day review period for complex disputes
- Escalation to master ISP management
- Interest payments for delayed resolutions
- Audit trail for all commission adjustments

### 5.4 Credit Management & Financial Controls

**Account Balance Management:**
- Current account balance monitoring
- Credit limit utilization tracking (75%, 90%, 100% alerts)
- Payment terms enforcement (Net 30, Net 15, etc.)
- Automatic payment processing setup
- Manual payment submission and tracking

**Credit Limit Impact & Controls (Configurable):**
- **Warning Threshold**: Configurable warning level (default: 80%, range: 50-95%)
- **Restriction Threshold**: Configurable restriction level (default: 90%, range: 75-99%)
- **Action at Limit**: Configurable actions at 100% utilization:
  - New customer creation (suspend/require approval/continue)
  - Existing customer services (continue/review/restrict)
  - Payment processing (continue/review/escalate)
- **Emergency Credit**: Configurable emergency credit rules (amount %, duration, approval level)

**Credit Limit Operations:**
- **Service Impact**: Existing customers protected, new business suspended
- **Emergency Credit**: 48-hour emergency credit available (up to 25% of limit)
- **Payment Allocation**: Automatic payment application to oldest charges first
- **Collections Process**: Graduated collection procedures with clear timelines

**Credit Limit Increase Process:**
- Financial review and credit application
- Business growth documentation requirements
- Payment history analysis (12-month minimum)
- Approval process and timing (5-10 business days)
- Temporary vs permanent limit increases

---

## White-Label & Branding

### 6.1 Brand Customization

**Visual Identity:**
- Custom logo upload and management
- Brand color scheme configuration
- Custom domain setup
- Branded email templates
- Marketing material customization

**Branding Configuration:**
```json
{
  "reseller_id": 1,
  "white_label_enabled": true,
  "branding": {
    "brand_name": "ABC Internet Services",
    "logo_url": "https://cdn.abc.com/logo.png",
    "primary_color": "#0066CC",
    "secondary_color": "#FF6600",
    "domain": "portal.abc-internet.com",
    "support_email": "support@abc-internet.com",
    "support_phone": "+1-555-ABC-HELP"
  }
}
```

### 6.2 Customer-Facing Branding

**Portal Customization:**
- Branded customer portal interface
- Custom login screens
- Personalized communications
- Branded invoices and statements
- Custom terms and conditions

**Communication Branding:**
- Email templates with reseller branding
- SMS sender ID customization
- Automated notification branding
- Support ticket branding
- Invoice and receipt branding

### 6.3 Marketing Support

**Marketing Materials:**
- Branded service brochures
- Custom pricing sheets
- Social media templates
- Website integration tools
- Lead capture forms

---

## User & Team Management

### 7.1 Reseller User Administration

**User Management Interface:**
- Add/remove team members
- Role assignment and permissions
- Access level configuration
- Performance monitoring
- Activity tracking

**User Creation Process:**
```json
{
  "reseller_id": 1,
  "username": "manager1",
  "email": "manager@abc-internet.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "manager",
  "permissions": ["customer_create", "customer_edit", "billing_view"],
  "allowed_customer_ids": [], // Empty = all customers
  "ip_whitelist": ["192.168.1.0/24"],
  "department": "Customer Service"
}
```

### 7.2 Permission Management

**Granular Permissions:**
- Customer management (view, create, edit, delete)
- Service operations (provision, modify, suspend)
- Financial operations (billing, payments, reporting)
- Support management (tickets, communication)
- User administration (add users, modify permissions)

**Role-Based Access Control:**
- Predefined role templates
- Custom role creation
- Permission inheritance
- Temporary access grants
- Emergency access procedures

### 7.3 Team Performance

**Activity Monitoring:**
- User login tracking
- Customer interaction logs
- Performance metrics
- Productivity indicators
- Quality assurance metrics

---

## Billing & Invoicing Operations

### 8.1 Billing Management

**Invoice Generation:**
- Automated monthly billing cycles
- Custom billing schedules
- Proforma invoice creation
- Service-specific billing
- Promotional pricing application

**Billing Operations:**
- Invoice review and approval
- Payment allocation
- Refund processing
- Credit note management
- Dispute resolution

### 8.2 Payment Processing

**Payment Methods:**
- Credit/debit card processing
- Bank transfer management
- Digital wallet integration
- Cash payment recording
- Cryptocurrency support (if enabled)

**Payment Workflow:**
- Automated payment processing
- Payment confirmation
- Failed payment handling
- Payment plan management
- Refund processing

### 8.3 Financial Reporting

**Billing Reports:**
- Revenue summaries
- Collection efficiency
- Outstanding receivables
- Payment method analysis
- Customer payment patterns

---

## Support & Ticket Management

### 9.1 Ticket System Integration

**Support Capabilities:**
- Customer ticket creation
- Internal ticket management
- Escalation to master ISP
- Resolution tracking
- Customer communication

**Ticket Categories:**
- Technical support issues
- Billing inquiries
- Service requests
- Complaints and feedback
- Emergency support

### 9.2 Support Workflow

**Ticket Lifecycle:**
1. **Creation**: Customer or reseller creates ticket
2. **Assignment**: Route to appropriate team member
3. **Investigation**: Diagnose and research issue
4. **Resolution**: Implement solution
5. **Closure**: Confirm customer satisfaction

**Escalation Process:**
- Level 1: Reseller support team
- Level 2: Reseller technical specialists
- Level 3: Master ISP support team
- Emergency: Direct ISP engineering

### 9.3 Knowledge Management

**Support Resources:**
- Knowledge base articles
- Troubleshooting guides
- Service documentation
- Common solution database
- Video tutorials

---

## Reports & Analytics

### 10.1 Business Intelligence

**Key Reports:**
- Customer acquisition and churn analysis
- Revenue and commission tracking
- Service utilization reports
- Support performance metrics
- Financial health indicators

**Report Categories:**
- **Operational**: Customer metrics, service status
- **Financial**: Revenue, commissions, payments
- **Performance**: KPIs, growth metrics
- **Compliance**: Regulatory and audit reports

### 10.2 Custom Reporting

**Report Builder:**
- Drag-and-drop report creation
- Custom field selection
- Filter and grouping options
- Automated report scheduling
- Export capabilities (PDF, Excel, CSV)

**Dashboard Analytics:**
- Real-time metrics
- Trend analysis
- Comparative reporting
- Predictive analytics
- Goal tracking

### 10.3 Data Export

**Export Options:**
- Customer data exports
- Financial data extracts
- Service utilization reports
- Commission statements
- Audit trail exports

---

## Sub-Reseller Management

### 11.1 Hierarchical Structure

**Multi-Level Reseller Support:**
- Parent-child reseller relationships
- Commission pass-through calculations
- Shared customer management
- Consolidated reporting
- Inherited branding options

**Sub-Reseller Creation:**
```json
{
  "parent_reseller_id": 1,
  "name": "Regional ABC Partner",
  "level": 1,
  "commission_percent": 8.00,
  "inherited_branding": true,
  "customer_limit": 500,
  "allowed_services": ["internet", "voice"]
}
```

### 11.2 Sub-Reseller Management

**Management Capabilities:**
- Sub-reseller creation and configuration
- Commission structure management
- Performance monitoring
- Support and training
- Policy enforcement

**Relationship Management:**
- Regular performance reviews
- Training and certification
- Marketing support
- Technical assistance
- Conflict resolution

---

## Reseller-Specific Workflows

### 12.1 Monthly Business Cycle

**Regular Operations:**
1. **Customer Review**: Analyze customer status and needs
2. **Commission Reconciliation**: Review and approve commissions
3. **Performance Analysis**: Evaluate key metrics
4. **Support Review**: Assess support quality and efficiency
5. **Planning**: Set goals and strategies for next period

### 12.2 Customer Onboarding Workflow

**Streamlined Process:**
1. **Lead Qualification**: Assess customer requirements
2. **Service Recommendation**: Propose appropriate services
3. **Pricing Presentation**: Custom pricing based on reseller rates
4. **Contract Execution**: Terms and service agreements
5. **Service Provisioning**: Technical implementation
6. **Customer Orientation**: Portal access and support information

### 12.3 Issue Resolution Workflow

**Support Process:**
1. **Issue Identification**: Customer reports problem
2. **Initial Diagnosis**: Reseller team investigation
3. **Resolution Attempt**: Apply known solutions
4. **Escalation**: Engage master ISP if needed
5. **Follow-up**: Ensure customer satisfaction

### 12.4 Business Growth Workflow

**Expansion Process:**
1. **Market Analysis**: Identify growth opportunities
2. **Service Expansion**: Request additional service authorization
3. **Pricing Strategy**: Develop competitive pricing
4. **Marketing Campaign**: Launch promotional activities
5. **Performance Monitoring**: Track results and adjust strategy

---

## Reseller Configuration Management

### 15.1 Configurable Reseller Operations

**Customer Management Configuration:**
- **Contact Types**: Use ISP-defined contact types or request custom types
- **Customer Limits**: Configure maximum customers, service types, and geographic restrictions
- **Onboarding Process**: Customize customer creation workflow and requirements
- **Customer Categories**: Define customer segments and apply different rules per segment

**Financial Configuration:**
- **Commission Structure**: Configure commission rates, payment schedules, and thresholds
- **Credit Management**: Set credit limit thresholds, warning levels, and restriction rules
- **Payment Processing**: Configure payment methods, retry schedules, and failure handling
- **Pricing Models**: Set markup rules, promotional pricing, and discount structures

**Service Configuration:**
- **Available Services**: Configure which services the reseller can offer
- **Service Provisioning**: Set automatic vs manual provisioning rules per service type
- **Equipment Management**: Configure equipment types, installation processes, and tracking
- **Service Policies**: Set service suspension, restoration, and termination rules

**Support Configuration:**
- **Ticket Routing**: Configure ticket assignment, escalation, and resolution rules
- **SLA Settings**: Set response time commitments and escalation procedures
- **Communication**: Configure notification preferences and customer communication rules
- **Knowledge Base**: Customize support resources and troubleshooting guides

### 15.2 Inherited vs Custom Configuration

**Inherited from Master ISP:**
- Core system functionality and constraints
- Regulatory compliance requirements
- Base security and audit policies
- Fundamental service definitions

**Reseller-Configurable:**
- Customer communication preferences and branding
- Service pricing and promotional offers
- Support processes and escalation rules
- Custom fields and data collection

**Request-Based Configuration:**
- New service types or custom configurations
- Enhanced credit limits or special terms
- Custom integration requirements
- Advanced feature enablement

---

## Terminology Consistency

### System-Wide Standards

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

### Reseller Benefits
- Consistent communication with master ISP
- Unified staff training across all systems
- Clear escalation terminology
- Professional customer experience

---

## Integration & API Access

### 13.1 API Integration

**Reseller API Access:**
- Customer management APIs
- Service provisioning APIs
- Billing and payment APIs
- Reporting and analytics APIs
- Communication APIs

**API Capabilities:**
```http
GET /reseller/api/customers
POST /reseller/api/customers/{id}/services
GET /reseller/api/commissions
POST /reseller/api/tickets
GET /reseller/api/reports/revenue
```

### 13.2 Third-Party Integrations

**External System Integration:**
- CRM system synchronization
- Accounting software integration
- Marketing automation tools
- Customer communication platforms
- Business intelligence tools

### 13.3 Webhook Support

**Event Notifications:**
- New customer registrations
- Service activations/deactivations
- Payment processing events
- Commission calculations
- Support ticket updates

---

## Security & Compliance

### 14.1 Security Measures

**Data Protection:**
- Role-based data access
- Customer data isolation
- Encrypted communications
- Secure authentication
- Audit trail maintenance

**Access Control:**
- IP whitelisting
- Session management
- Failed login protection
- Two-factor authentication
- Regular security reviews

### 14.2 Compliance Framework

**Regulatory Compliance:**
- Data privacy protection
- Financial regulation compliance
- Industry standard adherence
- Audit trail maintenance
- Regular compliance assessments

---

## Mobile Reseller Experience

### 15.1 Mobile Portal

**Mobile-Optimized Interface:**
- Responsive design for all devices
- Touch-friendly navigation
- Quick action shortcuts
- Offline capability for basic functions
- Push notifications

**Mobile-Specific Features:**
- Customer location services
- Mobile payment processing
- Photo documentation
- Voice notes for tickets
- GPS-based service mapping

---

This comprehensive reseller portal journey provides resellers with complete business management capabilities, from customer acquisition and service delivery to financial tracking and business growth, all within a branded, secure environment that maintains the reseller's market position while leveraging the master ISP's infrastructure and expertise.