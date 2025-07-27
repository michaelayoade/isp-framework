# API Management System Documentation

## Overview

The API Management System provides comprehensive control over API access, rate limiting, usage analytics, versioning, and quotas for the ISP Framework. This system ensures secure, scalable, and efficient API access control and monitoring.

## Architecture

The system follows the established modular architecture with:
- **Models**: Database entities for API keys, usage logs, rate limits, and quotas
- **Schemas**: Pydantic validation models for all API operations
- **Services**: Business logic for API key management, rate limiting, and analytics
- **Repositories**: Data access layer with advanced querying capabilities
- **API Endpoints**: RESTful endpoints for all API management operations

## Core Components

### 1. API Key Management

**Features:**
- Secure API key generation and management
- Granular permissions system
- Customer, reseller, and admin key assignment
- Key expiration and lifecycle management
- Real-time usage tracking

**Key Model:**
- `APIKey`: Stores API keys with permissions, rate limits, and usage metadata

### 2. Rate Limiting

**Features:**
- Configurable rate limits per API key and endpoint
- Multiple time windows (second, minute, hour, day)
- Automatic request counting and window management
- Rate limit violation handling with proper HTTP responses

**Key Models:**
- `RateLimitConfiguration`: Stores rate limit rules
- `RateLimitTracking`: Tracks current usage within time windows

### 3. Usage Analytics

**Features:**
- Comprehensive API usage logging
- Response time monitoring
- Error rate tracking
- Request/response size analytics
- IP address and user agent tracking

**Key Model:**
- `APIUsageLog`: Detailed logging of all API requests

### 4. API Versioning

**Features:**
- Semantic versioning support
- Deprecation management
- Migration guides and changelogs
- Sunset date tracking

**Key Model:**
- `APIVersion`: Manages API version lifecycle

### 5. Quota Management

**Features:**
- Daily, monthly, and custom quota periods
- Usage tracking and enforcement
- Automatic quota resets
- Over-quota handling

**Key Model:**
- `APIQuota`: Manages usage quotas for API keys

## API Endpoints

### API Key Management

#### Create API Key
```http
POST /api/v1/api-management/keys
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Customer Portal Key",
  "description": "API key for customer portal access",
  "customer_id": 123,
  "permissions": {"read": true, "write": false, "admin": false},
  "rate_limit": 1000,
  "rate_limit_period": "hour",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

#### List API Keys
```http
GET /api/v1/api-management/keys
Authorization: Bearer <token>
```

#### Get API Key Details
```http
GET /api/v1/api-management/keys/{key_id}
Authorization: Bearer <token>
```

#### Update API Key
```http
PUT /api/v1/api-management/keys/{key_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Key Name",
  "permissions": {"read": true, "write": true, "admin": false}
}
```

#### Revoke API Key
```http
PUT /api/v1/api-management/keys/{key_id}/revoke
Authorization: Bearer <token>
```

#### Delete API Key
```http
DELETE /api/v1/api-management/keys/{key_id}
Authorization: Bearer <token>
```

### Rate Limit Management

#### Create Rate Limit Configuration
```http
POST /api/v1/api-management/rate-limits
Authorization: Bearer <token>
Content-Type: application/json

{
  "endpoint": "/api/v1/customers",
  "max_requests": 100,
  "window_size": 3600,
  "is_active": true
}
```

#### List Rate Limits
```http
GET /api/v1/api-management/rate-limits
Authorization: Bearer <token>
```

### Usage Analytics

#### Get Usage Analytics
```http
GET /api/v1/api-management/analytics
Authorization: Bearer <token>
```

#### Get Detailed Usage Logs
```http
GET /api/v1/api-management/usage-logs
Authorization: Bearer <token>
```

#### Get API Key Usage
```http
GET /api/v1/api-management/keys/{key_id}/usage
Authorization: Bearer <token>
```

### API Versioning

#### Create API Version
```http
POST /api/v1/api-management/versions
Authorization: Bearer <token>
Content-Type: application/json

{
  "version": "v2",
  "description": "New API version with enhanced features",
  "is_deprecated": false,
  "sunset_date": "2025-12-31T23:59:59Z",
  "migration_guide_url": "https://docs.ispframework.com/migration/v2"
}
```

#### List API Versions
```http
GET /api/v1/api-management/versions
Authorization: Bearer <token>
```

### Quota Management

#### Create Quota
```http
POST /api/v1/api-management/quotas
Authorization: Bearer <token>
Content-Type: application/json

{
  "api_key_id": 123,
  "quota_type": "daily",
  "max_requests": 10000,
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-01-31T23:59:59Z"
}
```

## Authentication Methods

### 1. Bearer Token (JWT)
Used for admin, reseller, and customer authentication:
```http
Authorization: Bearer <jwt_token>
```

### 2. API Key
Used for programmatic access:
```http
X-API-Key: <api_key>
```

### 3. OAuth 2.0
Used for third-party integrations:
```http
Authorization: Bearer <oauth_token>
```

## Rate Limiting Behavior

### Rate Limit Headers
Every API response includes rate limit information:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 3600
```

### Rate Limit Exceeded
When rate limit is exceeded:
```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200

{
  "detail": "Rate limit exceeded. Try again in 3600 seconds."
}
```

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message",
  "error_code": "API_KEY_INVALID",
  "timestamp": "2024-01-01T12:00:00Z",
  "path": "/api/v1/api-management/keys"
}
```

### Common Error Codes
- `API_KEY_INVALID`: Invalid or missing API key
- `API_KEY_REVOKED`: API key has been revoked
- `API_KEY_EXPIRED`: API key has expired
- `RATE_LIMIT_EXCEEDED`: Rate limit has been exceeded
- `QUOTA_EXCEEDED`: Usage quota has been exceeded
- `PERMISSION_DENIED`: Insufficient permissions

## Usage Examples

### Customer Portal Integration
```python
import requests

# Create customer API key
headers = {"Authorization": f"Bearer {customer_token}"}
response = requests.post(
    "https://api.ispframework.com/api/v1/api-management/keys",
    headers=headers,
    json={
        "name": "Customer Dashboard",
        "permissions": {"read": True, "write": False}
    }
)
api_key = response.json()["key"]

# Use API key for customer operations
headers = {"X-API-Key": api_key}
response = requests.get(
    "https://api.ispframework.com/api/v1/customers/me/services",
    headers=headers
)
```

### Reseller Integration
```python
# Create reseller API key with higher limits
headers = {"Authorization": f"Bearer {reseller_token}"}
response = requests.post(
    "https://api.ispframework.com/api/v1/api-management/keys",
    headers=headers,
    json={
        "name": "Reseller Management",
        "permissions": {"read": True, "write": True},
        "rate_limit": 5000,
        "rate_limit_period": "hour"
    }
)
```

### Third-Party Integration
```python
# OAuth 2.0 flow for third-party applications
# Step 1: Get authorization code
# Step 2: Exchange for access token
# Step 3: Use token for API access
```

## Monitoring and Analytics

### Usage Dashboard
The system provides comprehensive analytics through:
- Real-time usage metrics
- Error rate monitoring
- Response time analytics
- Geographic usage patterns
- API key performance tracking

### Alerting
Configure alerts for:
- Rate limit violations
- Unusual usage patterns
- API key compromises
- System performance issues

## Database Schema

### Key Tables
- `api_keys`: API key storage and metadata
- `api_usage_logs`: Detailed usage tracking
- `rate_limit_tracking`: Current rate limit status
- `api_versions`: API version management
- `api_quotas`: Usage quota tracking

### Indexes
- Optimized indexes for fast lookups
- Composite indexes for complex queries
- Time-based indexes for analytics

## Security Best Practices

### API Key Security
- Use HTTPS for all API communications
- Rotate API keys regularly
- Implement key expiration
- Monitor usage patterns
- Use granular permissions

### Rate Limiting
- Set appropriate limits based on use case
- Implement exponential backoff
- Provide clear error messages
- Monitor for abuse patterns

### Access Control
- Implement principle of least privilege
- Use role-based permissions
- Regular access reviews
- Audit trail maintenance

## Migration and Deployment

### Database Migration
Run the migration to create API management tables:
```bash
alembic upgrade head
```

### Configuration
Environment variables for configuration:
```bash
API_RATE_LIMIT_DEFAULT=1000
API_RATE_LIMIT_WINDOW=3600
API_QUOTA_DEFAULT=10000
API_KEY_LENGTH=32
```

## Testing

### Unit Tests
```bash
pytest tests/test_api_management.py -v
```

### Integration Tests
```bash
python test_api_management.py
```

### Load Testing
```bash
locust -f tests/load_test_api_management.py
```

## Troubleshooting

### Common Issues
1. **API Key Not Working**: Check key status and permissions
2. **Rate Limit Too Low**: Adjust rate limit configuration
3. **CORS Issues**: Configure CORS settings
4. **Database Connection**: Check database connectivity

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support and Maintenance

### Regular Tasks
- Monitor usage analytics
- Review and rotate API keys
- Update rate limit configurations
- Check for security vulnerabilities
- Update API documentation

### Performance Optimization
- Database query optimization
- Cache frequently accessed data
- Implement request batching
- Monitor and tune rate limits
