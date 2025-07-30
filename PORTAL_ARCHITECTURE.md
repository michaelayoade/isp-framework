# Portal Architecture - ISP Framework

## 🏗️ **Multi-Portal Architecture Overview**

The ISP Framework implements a multi-portal architecture with three distinct applications, each with separate authentication flows and user experiences:

### **1. Admin Portal** (`/admin`)
**Target Users**: ISP Staff, Administrators, Support Teams
**Authentication**: OAuth 2.0 + JWT (Administrator accounts)
**Features**:
- Complete customer management (CRUD operations)
- Billing and invoice management
- Network infrastructure monitoring
- Service provisioning and management
- Support ticket handling
- Analytics and reporting
- System configuration

### **2. Customer Portal** (`/customer`)
**Target Users**: End customers (Internet/Voice service subscribers)
**Authentication**: Customer credentials + JWT
**Features**:
- Account overview and service details
- Bill viewing and payment processing
- Usage statistics and data consumption
- Service plan changes and upgrades
- Support ticket creation and tracking
- Document downloads (invoices, contracts)
- Profile management

### **3. Reseller Portal** (`/reseller`)
**Target Users**: Partner resellers and distributors
**Authentication**: Reseller credentials + JWT
**Features**:
- Customer registration and management
- Commission tracking and reporting
- Service plan catalog and pricing
- Bulk operations and provisioning
- Partner-specific analytics
- White-label branding options
- API access and integration tools

## 🔐 **Authentication Architecture**

### **Separate Authentication Flows**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin Portal  │    │ Customer Portal │    │ Reseller Portal │
│                 │    │                 │    │                 │
│ /admin/login    │    │ /customer/login │    │ /reseller/login │
│ Administrator   │    │ Customer        │    │ Reseller        │
│ OAuth 2.0 + JWT │    │ Credentials+JWT │    │ Credentials+JWT │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │   Backend API       │
                    │   Role-based Auth   │
                    │   /api/v1/*         │
                    └─────────────────────┘
```

### **User Models & Roles**
- **Administrator**: Full system access, all endpoints
- **Customer**: Limited to own account data and self-service operations
- **Reseller**: Access to assigned customers and partner functions

## 📁 **Frontend Structure**

```
frontend/src/app/
├── (admin)/              # Admin Portal
│   ├── login/
│   ├── dashboard/
│   ├── customers/
│   ├── billing/
│   ├── network/
│   ├── services/
│   └── layout.tsx
├── (customer)/           # Customer Portal  
│   ├── login/
│   ├── dashboard/
│   ├── account/
│   ├── billing/
│   ├── support/
│   └── layout.tsx
├── (reseller)/           # Reseller Portal
│   ├── login/
│   ├── dashboard/
│   ├── customers/
│   ├── commissions/
│   ├── analytics/
│   └── layout.tsx
├── globals.css
├── layout.tsx           # Root layout
└── page.tsx             # Landing/routing page
```

## 🎨 **UI/UX Differentiation**

### **Admin Portal**
- **Theme**: Professional dark/light theme with ISP branding
- **Navigation**: Full sidebar with all management features
- **Complexity**: Advanced tables, charts, and configuration options
- **Colors**: Primary green with professional accents

### **Customer Portal**
- **Theme**: Clean, consumer-friendly interface
- **Navigation**: Simple top navigation with key self-service features
- **Complexity**: Simplified views focused on account management
- **Colors**: Softer green palette with customer-friendly design

### **Reseller Portal**
- **Theme**: Business-focused with partner branding options
- **Navigation**: Horizontal tabs with partner-specific features
- **Complexity**: Business intelligence and bulk operation tools
- **Colors**: Customizable branding with white-label support

## 🔒 **Security Considerations**

### **Authentication Isolation**
- Separate JWT tokens for each portal type
- Different token expiration policies per user type
- Portal-specific session management

### **Authorization**
- Role-based access control (RBAC) at API level
- Portal-specific route guards
- Feature flags per user type

### **Data Isolation**
- Customers can only access their own data
- Resellers can only access assigned customers
- Administrators have full access with audit logging

## 🚀 **Implementation Plan**

### **Phase 1: Portal Structure Setup**
1. Create separate route groups for each portal
2. Implement distinct authentication flows
3. Set up portal-specific layouts and themes

### **Phase 2: Authentication Integration**
1. Extend backend auth to support multiple user types
2. Implement portal-specific JWT tokens
3. Create login pages for each portal

### **Phase 3: Feature Migration**
1. Move admin features to admin portal
2. Create customer self-service features
3. Implement reseller partner features

### **Phase 4: UI/UX Customization**
1. Apply portal-specific themes and branding
2. Optimize navigation for each user type
3. Implement responsive design for all portals

## 📊 **Benefits**

- **Security**: Isolated authentication and authorization
- **User Experience**: Tailored interfaces for different user types
- **Maintainability**: Clear separation of concerns
- **Scalability**: Independent deployment and scaling options
- **Branding**: White-label support for reseller portal
- **Performance**: Optimized bundles per portal type
