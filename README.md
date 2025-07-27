# ISP Framework
## Enterprise-Grade Internet Service Provider Management Platform

[![Status](https://img.shields.io/badge/Status-Active%20Development-green.svg)](https://github.com/ispframework/isp-framework)
[![Milestone](https://img.shields.io/badge/Milestone-3%20Complete-blue.svg)](#milestone-progress)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL-336791.svg)](https://postgresql.org/)

## 🎯 **Project Overview**

The ISP Framework is a comprehensive, enterprise-grade management platform designed specifically for Internet Service Providers. It provides a complete solution for customer management, service provisioning, billing, network infrastructure monitoring, and business operations.

### **Key Features**
- 🔐 **Enterprise Authentication** - OAuth 2.0 + JWT with unified token validation
- 👥 **Customer Management** - Hierarchical accounts with comprehensive profiles
- 📊 **Service Management** - Internet, Voice, and Bundle service provisioning
- 💰 **Billing System** - Automated invoicing, payments, and financial reporting
- 🌐 **Network Infrastructure** - Device monitoring, RADIUS, and IPAM integration
- 🎫 **Support System** - Ticket management with SLA tracking
- 📈 **Analytics & Reporting** - Business intelligence and usage analytics
- 🔧 **Framework Layer** - Custom entities, forms, and business rules
- 🔑 **API Management** - Comprehensive API key management, rate limiting, and usage analytics

## 🚀 **Current Status**

### **✅ Milestone 1: Enhanced Authentication & Customer Management (COMPLETED)**
- **OAuth 2.0 Authentication System** - RFC-compliant with client credentials flow
- **Unified Authentication** - Single dependency supporting OAuth + JWT tokens
- **Customer CRUD Operations** - Complete Create, Read, Update, Delete functionality
- **Advanced Customer Features** - Labels, notes, documents, billing configuration
- **Search & Filtering** - Multi-criteria search with pagination
- **Service Management System Endpoints**
  - `POST /service-templates` - Create service templates
  - `GET /service-templates` - List service templates
  - `POST /service-instances` - Create customer service instances
  - `GET /service-instances` - List customer services
  - `POST /service-provisioning` - Provision new services
  - `GET /service-management` - Service management dashboard
- **API Management System Endpoints**
  - `POST /api-management/keys` - Create API keys
  - `GET /api-management/keys` - List API keys
  - `PUT /api-management/keys/{id}/revoke` - Revoke API keys
  - `GET /api-management/analytics` - Usage analytics
  - `POST /api-management/rate-limits` - Configure rate limits
  - `GET /api-management/usage-logs` - Detailed usage logs

### **🔄 Next Milestone: Service Management & Billing Integration**
- Service plan management (Internet, Voice, Bundle)
- Service provisioning and activation workflows
- Invoice generation and payment processing
- Financial reporting and analytics

## 📦 **Implemented Modules (July 2025)**

- Authentication (OAuth 2.0 + JWT, 2FA, API keys)
- Customer & Portal ID management
- Reseller management system (single-tenant delegation)
- Service management (templates, instances, provisioning, alerts)
- Billing & Accounting (invoices, payments, credit notes)
- Network & IPAM (sites, routers, IP pools, RADIUS)
- Device management (SNMP monitoring, backup, discovery)
- Plugin system & API management
- File-storage (MinIO)

---

## 🏗️ **Architecture**

### **Backend Stack**
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: OAuth 2.0 + JWT tokens
- **Caching**: Redis
- **File Storage**: MinIO
- **Migrations**: Alembic
- **API Documentation**: OpenAPI/Swagger

### **Project Structure**
```
isp-framework/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API routes and endpoints
│   │   │   └── v1/
│   │   │       ├── endpoints/ # Individual endpoint modules
│   │   │       └── dependencies.py # Authentication dependencies
│   │   ├── core/              # Core configuration and utilities
│   │   │   ├── config.py      # Application configuration
│   │   │   ├── database.py    # Database connection
│   │   │   ├── security.py    # Security utilities
│   │   │   └── exceptions.py  # Custom exceptions
│   │   ├── models/            # SQLAlchemy database models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # Business logic layer
│   │   ├── repositories/      # Data access layer
│   │   └── main.py           # Application entry point
│   ├── alembic/              # Database migrations
│   └── requirements.txt      # Python dependencies
├── frontend/                  # React/Next.js frontend (planned)
├── docs/                     # Project documentation
│   ├── TECHNICAL_REQUIREMENTS.md
│   ├── FUNCTIONAL_REQUIREMENTS.md
│   ├── DEVELOPMENT_GUIDELINES.md
│   ├── API_CONTRACT_UPDATES.md
│   └── MILESTONE_1_SUMMARY.md
└── docker-compose.yml        # Development environment
```

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (recommended)

### **Development Setup**

1. **Clone the repository**
   ```bash
   git clone https://github.com/ispframework/isp-framework.git
   cd isp-framework
   ```

2. **Start the database services**
   ```bash
   docker-compose up -d postgres redis minio freeradius
   ```

3. **Set up the backend environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and secrets
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Admin Panel: http://localhost:8000/admin
   - Health Check: http://localhost:8000/health

### **Initial Setup**

1. **Create admin user**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/setup" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "secure_password", "email": "admin@example.com"}'
   ```

2. **Login and get access token**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "secure_password"}'
   ```

## 📚 **Documentation**

### **Technical Documentation**
- [**Technical Requirements**](docs/TECHNICAL_REQUIREMENTS.md) - Repository patterns, datetime handling, authentication standards
- [**Development Guidelines**](docs/DEVELOPMENT_GUIDELINES.md) - Code organization, testing, security best practices
- [**API Contract Updates**](docs/API_CONTRACT_UPDATES.md) - Schema corrections and authentication specifications

### **Functional Documentation**
- [**Functional Requirements**](docs/FUNCTIONAL_REQUIREMENTS.md) - Customer management, search/filtering, billing configuration
- [**Milestone 1 Summary**](docs/MILESTONE_1_SUMMARY.md) - Comprehensive achievement and lessons learned documentation

### **API Documentation**
- **Interactive API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🧪 **Testing**

### **Manual Testing**
The project includes comprehensive curl-based testing scripts for all endpoints:

```bash
# Test authentication
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "secure_password"}'

# Test customer creation
curl -X POST "http://localhost:8000/api/v1/customers/" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Customer", "email": "test@example.com", "category": "person"}'

# Test customer search
curl -X POST "http://localhost:8000/api/v1/customers/search" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "limit": 10, "offset": 0}'
```

### **Automated Testing**
- Unit tests for service layer methods
- Integration tests for API endpoints
- End-to-end testing workflows
- Performance benchmarking

## 🔐 **Security**

### **Authentication & Authorization**
- **OAuth 2.0** - RFC-compliant implementation with client credentials flow
- **JWT Tokens** - Secure token-based authentication with refresh capability
- **Unified Authentication** - Single dependency supporting multiple token types
- **Role-Based Access Control** - Granular permissions and role inheritance

### **Data Protection**
- **Password Security** - Bcrypt hashing with proper salt
- **Input Validation** - Comprehensive Pydantic schema validation
- **SQL Injection Prevention** - Parameterized queries throughout
- **Secure Headers** - CORS, CSP, and security headers implemented

## 📊 **Database Schema**

The ISP Framework includes a comprehensive database schema with 80+ tables covering:

### **Core Entities**
- **Customers** - Hierarchical customer management with profiles
- **Service Plans** - Internet, Voice, Bundle, and custom services
- **Billing** - Invoices, payments, credit notes, and accounting
- **Network** - Devices, monitoring, RADIUS, and IP management
- **Support** - Tickets, SLA tracking, and knowledge base

### **Extended Features**
- **Reseller Management** - Multi-tier partnerships and commissions
- **Analytics** - Usage tracking and business intelligence
- **Communication** - Templates, campaigns, and preferences
- **Framework Layer** - Custom entities and business rules

## 🛠️ **Development**

### **Key Lessons Learned**
Based on Milestone 1 implementation:

1. **Repository Pattern** - Always use `get_all(filters={})` and `count(filters={})`
2. **DateTime Handling** - Use `datetime.now(timezone.utc)` for timezone-aware operations
3. **Schema Alignment** - Remove password fields after hashing before model instantiation
4. **Unified Authentication** - Single dependency with OAuth + JWT fallback validation
5. **Comprehensive Testing** - Systematic curl-based testing reveals integration issues

### **Code Quality Standards**
- **Error Handling** - Comprehensive exception management
- **Logging** - Detailed service-level logging for debugging
- **Documentation** - Extensive inline and API documentation
- **Security** - Proper input validation and secure coding practices

## 🚀 **Deployment**

### **Production Environment**
- **Container Orchestration** - Docker Compose for development, Kubernetes for production
- **Database** - PostgreSQL with connection pooling and read replicas
- **Caching** - Redis cluster for session management and caching
- **File Storage** - MinIO or AWS S3 for document storage
- **Monitoring** - Prometheus metrics and Grafana dashboards

### **Environment Variables**
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/isp_framework
POSTGRES_USER=isp_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=isp_framework

# Security Configuration
SECRET_KEY=your-secret-key-here
OAUTH_CLIENT_SECRET=oauth-client-secret

# External Services
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

## 📈 **Roadmap**

### **Phase 1: Foundation (COMPLETED)**
- ✅ Enhanced Authentication & Customer Management
- ✅ OAuth 2.0 + JWT unified authentication
- ✅ Comprehensive customer CRUD with extended features
- ✅ Search, filtering, and pagination
- ✅ Technical documentation and guidelines

### **Phase 2: Service Management (In Progress)**
- 🔄 Internet service plans and provisioning
- 🔄 Voice service configuration and SIP integration
- 🔄 Bundle service management and pricing
- 🔄 Service activation and deactivation workflows

### **Phase 3: Billing & Financial (Planned)**
- 📋 Invoice generation and management
- 📋 Payment processing and tracking
- 📋 Credit management and adjustments
- 📋 Financial reporting and analytics

### **Phase 4: Network Infrastructure (Planned)**
- 📋 Device monitoring and management
- 📋 RADIUS authentication integration
- 📋 IP address management (IPAM)
- 📋 Network topology and performance monitoring

### **Phase 5: Support & Operations (Planned)**
- 📋 Ticket management system
- 📋 SLA tracking and escalation
- 📋 Knowledge base and documentation
- 📋 Mass incident management

## 🤝 **Contributing**

### **Development Process**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the development guidelines in `docs/DEVELOPMENT_GUIDELINES.md`
4. Write comprehensive tests for new functionality
5. Ensure all tests pass and code follows style guidelines
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### **Code Standards**
- Follow PEP 8 for Python code formatting
- Use type hints for all function parameters and return values
- Write comprehensive docstrings for all public methods
- Implement proper error handling and logging
- Include unit tests for all new functionality

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 **Support**

### **Documentation**
- [Technical Requirements](docs/TECHNICAL_REQUIREMENTS.md)
- [Functional Requirements](docs/FUNCTIONAL_REQUIREMENTS.md)
- [Development Guidelines](docs/DEVELOPMENT_GUIDELINES.md)
- [API Documentation](http://localhost:8000/docs)

### **Community**
- **Issues**: [GitHub Issues](https://github.com/ispframework/isp-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ispframework/isp-framework/discussions)
- **Wiki**: [Project Wiki](https://github.com/ispframework/isp-framework/wiki)

### **Professional Support**
For enterprise support, custom development, and consulting services, please contact the development team.

---

**Last Updated:** July 23, 2025  
**Version:** 1.0.0  
**Milestone Status:** Phase 1 Complete, Phase 2 In Progress  
**Project Completion:** 15% (Foundation Established)
