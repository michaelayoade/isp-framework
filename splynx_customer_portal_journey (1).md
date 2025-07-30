**Security Features:**
- Portal ID-based session management
- Login attempt monitoring per Portal ID
- Device recognition and trust
- Two-factor authentication (optional)
- IP-based security alerts# Complete Splynx Customer Portal Journey
## Comprehensive Guide to the Customer Self-Service Portal

### Table of Contents
1. [Portal Access & Login](#portal-access--login)
2. [Dashboard Overview](#dashboard-overview)
3. [Personal Profile Management](#personal-profile-management)
4. [Service Management](#service-management)
5. [Billing & Payment Center](#billing--payment-center)
6. [Usage Monitoring](#usage-monitoring)
7. [Support & Ticketing](#support--ticketing)
8. [Document Center](#document-center)
9. [Account Settings](#account-settings)
10. [Mobile Portal Experience](#mobile-portal-experience)
11. [Common Customer Workflows](#common-customer-workflows)

---

## Portal Access & Login

### 1.1 Accessing the Customer Portal

**Portal URL:** `https://yourdomain.com/portal` or custom branded URL

**Login Process:**
1. Navigate to customer portal URL
2. Enter login credentials (Portal ID/Username + password)
3. Complete any required verification  
4. Access personalized dashboard

**Login Credentials:**
- **Portal ID**: Unique customer identifier (e.g., "CUST001234", "user123")
- **Portal Password**: Customer-set password for portal access (changeable)
- **Network Credentials**: Separate credentials for internet service (admin managed)

**Credential Types:**
1. **Portal Access Credentials**
   - Portal ID + Portal Password
   - Used for: Customer portal login, bill payments, support tickets
   - Password: Customer can change anytime without affecting service

2. **Network Access Credentials** 
   - Portal ID + Network Password (fixed)
   - Used for: Internet connection (PPPoE, WiFi authentication)
   - Password: Managed by ISP, changed only by support request

**Alternative Login**: Email address (if configured as secondary portal option)

### 1.4 Portal ID System

**Portal ID Characteristics:**
- **Unique System-Wide**: No duplicates across entire platform
- **Stable Reference**: Never changes once assigned
- **Integration Key**: Used for RADIUS, billing, support tickets
- **Format Options**: Configurable (CUST001234, user123, etc.)
- **Auto-Generation**: System creates unique IDs for new customers

**Operational Benefits:**
- **Network Authentication**: Same credentials for internet access
- **Support Efficiency**: Staff use Portal ID for quick customer lookup
- **Billing Integration**: Stable reference for payment processing
- **Multi-User Accounts**: Family members share Portal ID, separate access levels
- **Service Integration**: Links to all customer services and history

**Login Entry Points:**
- Direct portal URL access
- Email links from invoices/notifications
- SMS links for quick access
- Mobile app integration
- Social media login (if enabled)
- Self-registration forms (if enabled)

### 1.2 First-Time Login Experience

**Welcome Wizard:**
1. **Profile Completion**
   - Verify contact information
   - Set communication preferences
   - Upload profile picture (optional)

2. **Service Overview**
   - Review active services
   - Understand billing cycle
   - Set up payment methods

3. **Portal Tour**
   - Dashboard navigation
   - Key features overview
   - Help and support options

### 1.3 Password Management

**Password Management:**
- **Portal Password Reset**: Self-service via Portal ID + email verification
- **Network Password**: Contact support for network credential changes
- **Security Questions**: Additional verification for portal access
- **SMS Verification**: Temporary access codes to registered phone

**Important Note**: 
- Changing your portal password does NOT affect your internet service
- Network access uses separate credentials managed by your ISP
- Contact support if you need to change network/internet login credentials

**Account Identification:**
- **Primary**: Portal ID/Username (unique system identifier)
- **Secondary**: Email address (can be updated by customer)
- **Verification**: Account number, service address, or phone number

---

## Dashboard Overview

### 2.1 Main Dashboard Components

**At-a-Glance Information:**
- **Account Status**: Active, blocked, suspended indicators
- **Current Balance**: Outstanding amounts, credit balance
- **Next Bill Date**: Upcoming invoice information
- **Service Status**: All services operational status
- **Recent Activity**: Latest transactions and activities

**Quick Action Widgets:**
- **Pay Now**: Quick payment for outstanding invoices
- **Download Invoice**: Latest bill download
- **Create Ticket**: Fast support access
- **Usage Summary**: Current month's usage
- **Service Controls**: Basic service management

### 2.2 Personalized Dashboard

**Customizable Widgets:**
- Service usage charts
- Payment history summary
- Upcoming service renewals
- Support ticket status
- News and announcements
- Promotional offers

**Dashboard Personalization:**
- Widget arrangement (drag & drop)
- Color theme selection
- Information density preferences
- Quick access shortcuts

### 2.3 Notifications Center

**Real-time Notifications:**
- Service interruptions
- Payment confirmations
- Invoice generation
- Support ticket updates
- Account changes
- Promotional announcements

**Notification Preferences:**
- Email notifications on/off
- SMS alerts configuration
- In-portal notification settings
- Notification frequency control

---

## Personal Profile Management

### 3.1 Profile Information

**Personal Details Section:**
- Name and primary contact information
- **Flexible Contact Management**: Add contacts as needed for your account
  - Contact types based on your ISP's available options
  - Configurable contact roles and notification preferences
  - Add additional authorized contacts when needed
  - No mandatory contact types (add only what you need)
- Postal address and service location
- Communication preferences per contact
- Emergency contact information and notification preferences

**Contact Management Features:**
- Add/edit contacts based on your account needs
- Set notification preferences per contact (configurable options)
- Manage communication channels per contact (email, SMS, phone)
- Update contact information without affecting service
- Remove contacts when no longer needed

**Business Information (if applicable):**
- Company name and registration
- Tax identification numbers
- Business contact details
- Authorized representatives

### 3.2 Contact Preferences

**Communication Settings:**
- Preferred contact method (email, SMS, phone)
- Language preferences
- Timezone settings
- Marketing communication opt-in/out

**Document Delivery:**
- Electronic vs printed invoices
- Document format preferences (PDF, email)
- Delivery schedule preferences
- Archive access preferences

### 3.3 Profile Security

**Security Management:**
- Change password
- Security questions setup
- Login history review
- Active sessions management
- Two-factor authentication setup

---

## Service Management

### 4.1 Service Overview

**Active Services Display:**
- **Internet Services**: Speed, data allowance, IP addresses
- **Voice Services**: Number assignments, call features
- **Bundle Services**: Combined package details
- **Additional Services**: Value-added services

**Service Status Indicators:**
- 🟢 **Active**: Service operational
- 🟡 **Limited**: FUP restrictions applied
- 🔴 **Suspended**: Service temporarily disabled
- ⚪ **Pending**: Activation in progress
- ⚫ **Terminated**: Service permanently ended

### 4.2 Service Details

**Internet Service Management:**
- Current speed package
- Data usage and FUP status
- IP address assignments
- Router/equipment information
- Speed test results
- Network status

**Voice Service Management:**
- Phone number details
- Call forwarding settings
- Voicemail configuration
- Call history and logs
- Feature activation/deactivation

### 4.3 Service Requests

**Available Actions:**
- **Upgrade/Downgrade Plans**: Service modification requests
- **Temporary Suspension**: Vacation holds
- **Service Addition**: Add new services
- **Technical Support**: Service-specific issues
- **Relocation Requests**: Address changes

**Request Tracking:**
- Service request status
- Estimated completion dates
- Technical appointment scheduling
- Progress notifications

---

## Billing & Payment Center

### 5.1 Invoice Management

**Invoice Overview:**
- Current outstanding balance
- Invoice history (last 12 months)
- Payment due dates
- Invoice status tracking

**Invoice Details:**
- Line-item breakdown
- Service period information
- Tax calculations
- Discount applications
- Payment terms

**Invoice Actions:**
- Download PDF invoices
- Email invoice copies
- Print-friendly formats
- Dispute invoice items
- Set up payment plans

### 5.2 Payment Processing & Failure Handling

**Payment Methods:**
- **Credit/Debit Cards**: Visa, MasterCard, local cards with automatic retry
- **Bank Transfer**: Direct debit with failure notification
- **Digital Wallets**: PayPal, mobile money with instant confirmation
- **Cryptocurrency**: (if enabled) with volatility protection
- **Cash Payments**: Agent locations with receipt tracking

**Payment Features:**
- One-time payments with instant confirmation
- Recurring payment setup with failure protection
- **Payment Failure Management**:
  - Automatic retry attempts (Day 1, 3, 7, 14)
  - Multiple payment method fallback sequence
  - Grace period notifications and countdown
  - Partial payment acceptance and allocation
  - Emergency payment options during suspension

**Failed Payment Process (Your ISP's Configuration):**
Your ISP configures the payment retry and suspension process. Typical process:
1. **Retry Attempts**: Automatic retry attempts (timing varies by ISP policy)
2. **Notification Schedule**: Email, SMS, and call notifications (frequency per ISP configuration)
3. **Grace Period**: Configured grace period before service impact (varies by ISP)
4. **Service Impact**: Service suspension method (speed reduction or full suspension per ISP policy)
5. **Restoration**: Automatic restoration timing upon payment (immediate or per ISP schedule)

**Your ISP's Specific Policy:**
- View your ISP's specific payment and suspension policy in Account Settings
- Grace period and notification schedule configured for your account type
- Payment retry attempts and timing as per your service agreement
- Service restoration process and timing based on your ISP's configuration

**Service Restoration:**
- Immediate restoration upon payment (automated)
- Grace period extension for financial hardship (contact support)
- Payment plan options for large outstanding balances
- Service restoration testing and confirmation

### 5.3 Financial History

**Transaction History:**
- All payments and charges
- Credit note applications
- Refund processing
- Deposit tracking
- Late fee applications

**Financial Reports:**
- Monthly spending summaries
- Annual expense reports
- Tax-related documents
- Usage-based billing details
- Credit utilization reports

### 5.4 Credit Management

**Account Credit:**
- Current credit balance
- Credit application history
- Credit expiration tracking
- Bonus credit notifications

**Top-up Services:**
- Data top-up purchases
- Emergency credit activation
- Prepaid service recharges
- Gift credit options

---

## Usage Monitoring

### 6.1 Internet Usage Monitoring

**Usage Dashboard:**
- Real-time data consumption (updated every 15 minutes)
- Daily/weekly/monthly trends and patterns
- Upload vs download breakdown with detailed analytics
- Peak usage times and bandwidth utilization
- Historical usage patterns and seasonal trends

**Usage Data Accuracy:**
- **Data Collection**: RADIUS accounting every 15 minutes
- **Billing Accuracy**: Usage data finalized daily at 2:00 AM
- **Dispute Resolution**: 30-day usage history available for review
- **Data Retention**: 24 months of detailed usage records
- **Billing Disputes**: Online dispute submission with usage evidence

**FUP (Fair Usage Policy) Monitoring:**
- Current allowance utilization with visual indicators
- Remaining data allocation and reset countdown
- **FUP Reset Timing**: Automatic reset on billing cycle date
- Speed reduction notifications and restoration timeline
- Usage alerts and warnings (75%, 90%, 100% thresholds)
- Emergency data top-up options during FUP restrictions

**Usage Alerts & Notifications (Configurable):**
- **Custom Alert Thresholds**: Set your own usage alert percentages (10%-95%)
- **Notification Preferences**: Choose how you want to be notified (email, SMS, portal)
- **Alert Frequency**: Configure notification frequency (once, daily, weekly)
- **Multiple Thresholds**: Set multiple alert levels (e.g., 75%, 90%, 95%)
- **Family Controls**: Configure usage monitoring for different devices/users (if supported)
- **Bill Protection**: Set spending alert thresholds to prevent bill shock

### 6.2 Voice Usage

**Call Analytics:**
- Call duration summaries
- Most called numbers
- Cost per call analysis
- International usage
- Feature usage statistics

**Call History:**
- Detailed call logs
- Call duration and costs
- Destination analysis
- Time-based usage patterns

### 6.3 Usage Alerts

**Automated Notifications:**
- Data usage warnings (75%, 90%, 100%)
- FUP threshold alerts
- Unusual usage pattern detection
- Bill shock prevention
- Service interruption notices

**Custom Alerts:**
- User-defined usage limits
- Cost thresholds
- Service-specific monitoring
- Family usage controls

---

## Support & Ticketing

### 6.1 Ticket Management

**Create Support Tickets:**
- Service issue categories
- Priority level selection
- Detailed problem description
- File attachment support
- Preferred contact method

**Ticket Categories:**
- Technical issues
- Billing inquiries
- Service requests
- Account management
- General information

**Priority Selection:**
- **Emergency**: Critical service failure
- **Urgent**: High impact issue
- **High**: Significant service impact
- **Medium**: Standard issue
- **Low**: Minor issue or question

**SLA Transparency:**
Customers can view expected response and resolution times based on:
- Selected priority level
- Service level agreement
- Business hours configuration
- Current support queue status

### 6.2 Ticket Tracking

**Ticket Status Dashboard:**
- **New**: Recently submitted, being reviewed
- **Assigned**: Assigned to support agent
- **In Progress**: Actively being worked on
- **Pending Customer**: Waiting for your response
- **Escalated**: Transferred to specialized team
- **Resolved**: Solution provided, pending confirmation
- **Closed**: Issue confirmed resolved

**Communication Thread:**
- Complete message history
- Agent responses
- Customer replies
- File attachments
- Status change notifications

### 6.3 Self-Service Support

**Knowledge Base:**
- FAQ sections
- Troubleshooting guides
- Video tutorials
- Setup instructions
- Common solutions

**Diagnostic Tools:**
- Connection speed tests
- Network connectivity checks
- Service status verification
- Equipment diagnostic tools

### 6.4 Live Support Options

**Real-time Support:**
- Live chat integration
- Callback request system
- Video call support (if available)
- Screen sharing for technical issues

**Support Availability:**
- Business hours display
- Expected response times
- Emergency contact options
- Escalation procedures

---

## Document Center

### 7.1 Document Library

**Available Documents:**
- Service agreements and contracts
- Invoice archives
- Payment receipts
- Terms and conditions
- Privacy policies
- Technical documentation

**Document Categories:**
- Billing documents
- Legal agreements
- Technical manuals
- Promotional materials
- Regulatory notices

### 7.2 Document Management

**Document Actions:**
- Download PDF versions
- Email document copies
- Print-friendly formats
- Search document content
- Organize by categories

**Document Security:**
- Secure document access
- Download tracking
- Expiration date management
- Access permission controls

---

## Account Settings

### 8.1 Communication Preferences

**Notification Settings:**
- Email notification preferences
- SMS alert configuration
- In-portal notification settings
- Marketing communication controls
- Language and timezone preferences

### 8.2 Privacy Settings

**Data Management:**
- Personal data visibility
- Third-party data sharing
- Marketing consent management
- Cookie preferences
- Account deletion requests

### 8.3 Access Management

**Login Security:**
- Password change functionality
- Two-factor authentication setup
- Session management
- Device authorization
- Login history review

---

## Mobile Portal Experience

### 9.1 Mobile-Optimized Interface

**Responsive Design:**
- Touch-friendly navigation
- Optimized layouts for mobile
- Quick access menus
- Swipe gestures
- Mobile-specific features

**Mobile App Features:**
- Push notifications
- Offline document access
- Mobile payment integration
- Location-based services
- Camera integration for tickets

### 9.2 ISP Policy & Configuration Transparency

**Your ISP's Service Policies:**
- **Payment Policy**: View your ISP's payment retry schedule and grace periods
- **Suspension Policy**: Understand how service suspensions work for your account type
- **Data Usage Policy**: Review FUP rules, fair usage policies, and restrictions
- **Support SLA**: See response time commitments and escalation procedures
- **Service Restoration**: Understand automatic restoration rules and timing

**Configurable Account Settings:**
- **Notification Preferences**: Customize how and when you receive communications
- **Usage Alerts**: Set custom thresholds based on your ISP's available options
- **Contact Management**: Add contacts based on your ISP's supported contact types
- **Payment Options**: Configure payment methods from your ISP's available options
- **Service Preferences**: Customize service-related settings within your ISP's parameters

**Policy Updates & Changes:**
- Automatic notification when your ISP updates service policies
- Clear explanation of how policy changes affect your account
- Advance notice period for policy changes (as per service agreement)
- Opt-in/opt-out options for policy changes where applicable

**Quick Actions:**
- One-tap payments
- Speed test integration
- Emergency contact
- Service status checks
- Usage monitoring widgets

---

## Common Customer Workflows

### 10.1 Monthly Billing Cycle

**Customer Journey:**
1. **Invoice Notification**
   - Email/SMS notification received
   - Portal notification appears
   - Invoice becomes available

2. **Invoice Review**
   - Login to portal
   - Review invoice details
   - Check service usage
   - Verify charges

3. **Payment Processing**
   - Select payment method
   - Process payment
   - Receive confirmation
   - Update account balance

4. **Post-Payment Actions**
   - Download receipt
   - Update payment methods
   - Review account status

### 10.2 Service Issue Resolution

**Customer Journey:**
1. **Issue Identification**
   - Notice service problem
   - Check service status
   - Review recent changes

2. **Self-Service Attempts**
   - Check knowledge base
   - Run diagnostic tools
   - Try troubleshooting steps

3. **Support Request**
   - Create support ticket
   - Provide detailed description
   - Attach relevant files
   - Select priority level

4. **Issue Tracking**
   - Monitor ticket progress
   - Respond to agent queries
   - Receive status updates
   - Confirm resolution

### 10.3 Service Upgrade Process

**Customer Journey:**
1. **Service Review**
   - Analyze current usage
   - Identify upgrade needs
   - Compare available plans

2. **Upgrade Request**
   - Select new service plan
   - Review pricing changes
   - Submit upgrade request
   - Confirm terms and conditions

3. **Approval Process**
   - Wait for admin approval
   - Receive confirmation
   - Schedule implementation
   - Receive updated service info

4. **Service Activation**
   - Monitor activation progress
   - Test new service levels
   - Update payment methods
   - Receive updated billing

### 10.4 Account Maintenance

**Regular Tasks:**
- **Weekly**: Check usage levels, review notifications
- **Monthly**: Pay invoices, review charges, check service status
- **Quarterly**: Update contact information, review service needs
- **Annually**: Review service plans, update security settings

---

## Customer Portal Features by User Type

### 10.5 Residential Customers

**Focus Areas:**
- Simple service management
- Easy payment processing
- Usage monitoring
- Basic support features
- Family account controls

### 10.6 Business Customers

**Enhanced Features:**
- Multiple service management
- Advanced billing features
- User hierarchy management
- Custom reporting
- API integration options
- Dedicated support channels

### 10.7 Prepaid Customers

**Specialized Features:**
- Credit balance monitoring
- Top-up services
- Usage-based alerts
- Emergency credit options
- Prepaid plan management

---

## Service Continuity & System Status

### 12.1 System Status & Outage Communication

**Service Status Information:**
- **Real-time Network Status**: Current operational status of all services
- **Planned Maintenance**: Scheduled maintenance windows with advance notice
- **Service Outage Updates**: Live updates during unplanned outages
- **Geographic Impact**: Outage impact by service area and location
- **Estimated Resolution**: Real-time updates on restoration progress

**Outage Communication Channels:**
- **In-Portal Notifications**: Service status banner and detailed status page
- **SMS Alerts**: Critical outage notifications to primary and emergency contacts
- **Email Updates**: Detailed outage information and restoration progress
- **Social Media**: Public status updates via official ISP social channels
- **Customer Service**: Dedicated outage hotline with automated updates

**Service Degradation Handling:**
- **Reduced Speed Periods**: Automatic notification of temporary speed reductions
- **Service Quality Issues**: Proactive monitoring and customer notification
- **Alternative Service Options**: Temporary solutions during extended outages
- **Compensation**: Automatic service credits for prolonged outages
- **Customer Support**: Enhanced support availability during service issues

### 12.2 Business Continuity Features

**Portal Availability During Outages:**
- **Backup Portal Access**: Secondary portal URL for system maintenance
- **Mobile App**: Offline capability for basic account information
- **SMS Services**: Account balance and payment options via SMS
- **Phone Support**: Enhanced phone support during portal outages
- **Emergency Payment**: Alternative payment methods during system downtime

**Data Protection & Recovery:**
- **Account Data Backup**: Regular backup of customer account information
- **Payment History**: Secure backup of financial transaction history
- **Service History**: Complete service and support history preservation
- **Communication Logs**: Backup of all customer communications
- **Recovery Procedures**: Automatic data recovery and integrity verification

---

## Usage Data & Billing Accuracy

### 13.1 Usage Data Collection & Accuracy

**Data Collection Process:**
- **Real-time Monitoring**: Continuous usage tracking via network equipment
- **Batch Processing**: Usage data finalized every 15 minutes for accuracy
- **Quality Assurance**: Automated data validation and error correction
- **Redundant Collection**: Multiple data sources for accuracy verification
- **Historical Tracking**: Complete usage history for pattern analysis

**Billing Accuracy & Dispute Resolution:**
- **Usage Verification**: 30-day detailed usage logs available for customer review
- **Billing Dispute Process**: Online dispute submission with supporting evidence
- **Investigation Timeline**: 5-10 business day investigation period
- **Resolution Options**: Usage adjustments, service credits, or payment plans
- **Appeal Process**: Escalation to management for complex disputes

**Data Retention & Privacy:**
- **Retention Period**: 24 months of detailed usage data for billing accuracy
- **Privacy Protection**: Usage data encryption and access control
- **Data Deletion**: Automatic deletion of expired usage data
- **Export Options**: Customer data export upon request
- **Regulatory Compliance**: Data handling in compliance with privacy laws

---

### System-Wide Standards

**Account Status (Consistent Across All Portals):**
- **New**: Account setup in progress
- **Active**: Services operational
- **Suspended**: Temporarily disabled (payment/policy issues)
- **Inactive**: Account permanently closed
- **Pending**: Awaiting activation or approval

**Service Status (Consistent Across All Portals):**
- **Pending**: Activation in progress
- **Active**: Fully operational
- **Suspended**: Temporarily disabled
- **Limited**: Usage restrictions applied
- **Terminated**: Service ended

**Support Ticket Status (Consistent Across All Portals):**
- **New**: Recently submitted
- **Assigned**: Being reviewed by support team
- **In Progress**: Actively being resolved
- **Pending Customer**: Awaiting your response
- **Escalated**: Transferred to specialized team
- **Resolved**: Solution provided
- **Closed**: Issue confirmed resolved

**Priority Levels (Consistent Across All Portals):**
- **Emergency**: Critical service failure
- **Urgent**: High impact issue
- **High**: Significant service impact
- **Medium**: Standard issue
- **Low**: Minor issue or general question

### Customer Benefits
- Clear understanding of account and service status
- Consistent communication with support teams
- Professional, unified experience
- Easy escalation and resolution tracking
- **Credential Security**: Portal and network access properly separated

### **Credential Management Standards**
**Portal Access (Customer Controlled):**
- Portal ID + Portal Password
- Used for: Bill payment, support, account management
- Customer can change portal password anytime

**Network Access (ISP Controlled):**
- Portal ID + Network Password  
- Used for: Internet connection, WiFi authentication
- Managed by ISP to ensure service stability
- Changes require support request to prevent service interruption

---

## Portal Accessibility & Support

### 11.1 Accessibility Features

**Universal Design:**
- Screen reader compatibility
- Keyboard navigation support
- High contrast themes
- Font size adjustment
- Multi-language support

### 11.2 Help & Support

**In-Portal Help:**
- Contextual help tooltips
- Step-by-step guides
- Video tutorials
- Interactive tours
- FAQ integration

**Contact Support:**
- Multiple contact channels
- Support ticket system
- Live chat integration
- Callback requests
- Email support

---

## Portal Security & Privacy

### 12.1 Security Measures

**Data Protection:**
- SSL/TLS encryption
- Secure authentication
- Session management
- Data encryption at rest
- Regular security updates

**User Security:**
- Strong password requirements
- Account lockout policies
- Login monitoring
- Suspicious activity alerts
- Secure logout procedures

### 12.2 Privacy Controls

**Data Management:**
- Personal data access
- Data correction tools
- Data deletion requests
- Privacy preference controls
- Third-party sharing controls

---

This comprehensive customer portal journey provides customers with a complete self-service experience, from basic account management to advanced service controls, ensuring they can efficiently manage their ISP services with minimal need for direct support contact.