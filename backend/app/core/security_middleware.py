"""
Security middleware and hardening utilities for ISP Framework.

Provides rate limiting, security headers, input validation, and threat protection.
"""
import time
import ipaddress
from typing import Dict, List
from collections import defaultdict, deque
from datetime import datetime, timedelta
import re

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
import structlog

from app.core.config import settings
from app.core.observability import log_audit_event

logger = structlog.get_logger("isp.security")


class RateLimitStore:
    """In-memory rate limit store with sliding window."""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
    
    def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """Check if key is rate limited using sliding window."""
        now = time.time()
        window_start = now - window
        
        # Clean old requests
        while self.requests[key] and self.requests[key][0] < window_start:
            self.requests[key].popleft()
        
        # Check if limit exceeded
        if len(self.requests[key]) >= limit:
            return True
        
        # Add current request
        self.requests[key].append(now)
        return False
    
    def block_ip(self, ip: str, duration: int):
        """Block IP for specified duration in seconds."""
        self.blocked_ips[ip] = datetime.now() + timedelta(seconds=duration)
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked."""
        if ip in self.blocked_ips:
            if datetime.now() < self.blocked_ips[ip]:
                return True
            else:
                del self.blocked_ips[ip]
        return False
    
    def cleanup_expired(self):
        """Clean up expired entries."""
        now = datetime.now()
        expired_ips = [ip for ip, expiry in self.blocked_ips.items() if now >= expiry]
        for ip in expired_ips:
            del self.blocked_ips[ip]


# Global rate limit store
rate_limit_store = RateLimitStore()


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""
    
    def __init__(self, app, config: dict = None):
        super().__init__(app)
        self.config = config or {}
        
        # Rate limiting config
        self.rate_limits = {
            'default': {'requests': 100, 'window': 60},  # 100 req/min
            'auth': {'requests': 5, 'window': 60},       # 5 auth attempts/min
            'api': {'requests': 1000, 'window': 60},     # 1000 API calls/min
        }
        
        # Security patterns
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'union\s+select',             # SQL injection
            r'\.\./',                      # Path traversal
            r'eval\s*\(',                  # Code injection
            r'exec\s*\(',                  # Code execution
        ]
        
        # Blocked user agents
        self.blocked_user_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'zap'
        ]
        
        # Trusted IP ranges (can be configured)
        self.trusted_ips = self._parse_trusted_ips()
    
    def _parse_trusted_ips(self) -> List[ipaddress.IPv4Network]:
        """Parse trusted IP ranges from config."""
        trusted_ranges = getattr(settings, 'TRUSTED_IP_RANGES', [
            '127.0.0.0/8',    # Localhost
            '10.0.0.0/8',     # Private
            '172.16.0.0/12',  # Private
            '192.168.0.0/16', # Private
        ])
        
        networks = []
        for range_str in trusted_ranges:
            try:
                networks.append(ipaddress.IPv4Network(range_str))
            except ValueError:
                logger.warning(f"Invalid IP range: {range_str}")
        
        return networks
    
    def _is_trusted_ip(self, ip: str) -> bool:
        """Check if IP is in trusted ranges."""
        try:
            ip_addr = ipaddress.IPv4Address(ip)
            return any(ip_addr in network for network in self.trusted_ips)
        except ValueError:
            return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP considering proxies."""
        # Check X-Forwarded-For header (from load balancer/proxy)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(',')[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else '127.0.0.1'
    
    def _get_rate_limit_key(self, request: Request, ip: str) -> tuple:
        """Generate rate limit key and determine limit type."""
        path = request.url.path
        
        # Authentication endpoints
        if '/auth/' in path or '/login' in path or '/token' in path:
            return f"auth:{ip}", 'auth'
        
        # API endpoints
        if path.startswith('/api/'):
            # Per-user rate limiting if authenticated
            user_id = getattr(request.state, 'user_id', None)
            if user_id:
                return f"api:user:{user_id}", 'api'
            else:
                return f"api:ip:{ip}", 'api'
        
        # Default rate limiting
        return f"default:{ip}", 'default'
    
    def _check_suspicious_content(self, content: str) -> List[str]:
        """Check for suspicious patterns in request content."""
        threats = []
        content_lower = content.lower()
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                threats.append(pattern)
        
        return threats
    
    def _check_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious."""
        if not user_agent:
            return True  # Missing user agent is suspicious
        
        user_agent_lower = user_agent.lower()
        return any(blocked in user_agent_lower for blocked in self.blocked_user_agents)
    
    async def dispatch(self, request: Request, call_next):
        """Main security middleware logic."""
        time.time()
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('User-Agent', '')
        
        # Skip security checks for trusted IPs (internal services)
        if self._is_trusted_ip(client_ip):
            return await call_next(request)
        
        # Check if IP is blocked
        if rate_limit_store.is_ip_blocked(client_ip):
            log_audit_event(
                domain="security",
                event="blocked_ip_access_attempt",
                ip_address=client_ip,
                user_agent=user_agent,
                path=request.url.path
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "IP temporarily blocked due to suspicious activity"}
            )
        
        # Check user agent
        if self._check_user_agent(user_agent):
            log_audit_event(
                domain="security",
                event="suspicious_user_agent",
                ip_address=client_ip,
                user_agent=user_agent,
                path=request.url.path
            )
            rate_limit_store.block_ip(client_ip, 3600)  # Block for 1 hour
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )
        
        # Rate limiting
        rate_key, limit_type = self._get_rate_limit_key(request, client_ip)
        limit_config = self.rate_limits[limit_type]
        
        if rate_limit_store.is_rate_limited(
            rate_key, 
            limit_config['requests'], 
            limit_config['window']
        ):
            log_audit_event(
                domain="security",
                event="rate_limit_exceeded",
                ip_address=client_ip,
                user_agent=user_agent,
                path=request.url.path,
                limit_type=limit_type
            )
            
            # Block IP after repeated rate limit violations
            violations_key = f"violations:{client_ip}"
            if rate_limit_store.is_rate_limited(violations_key, 3, 300):  # 3 violations in 5 min
                rate_limit_store.block_ip(client_ip, 1800)  # Block for 30 minutes
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": limit_config['window']
                },
                headers={"Retry-After": str(limit_config['window'])}
            )
        
        # Content inspection for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body:
                    content = body.decode('utf-8', errors='ignore')
                    threats = self._check_suspicious_content(content)
                    
                    if threats:
                        log_audit_event(
                            domain="security",
                            event="suspicious_content_detected",
                            ip_address=client_ip,
                            user_agent=user_agent,
                            path=request.url.path,
                            threats=threats,
                            content_sample=content[:200]
                        )
                        
                        # Block IP for repeated suspicious content
                        rate_limit_store.block_ip(client_ip, 7200)  # Block for 2 hours
                        
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "Suspicious content detected"}
                        )
            except Exception as e:
                logger.warning(f"Content inspection failed: {e}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add security headers
            response.headers.update({
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Content-Security-Policy': "default-src 'self' cdn.jsdelivr.net fastapi.tiangolo.com; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; img-src 'self' fastapi.tiangolo.com data:;",
                'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
            })
            
            return response
            
        except Exception as e:
            # Log security-relevant errors
            if isinstance(e, HTTPException) and e.status_code >= 400:
                log_audit_event(
                    domain="security",
                    event="http_error",
                    ip_address=client_ip,
                    user_agent=user_agent,
                    path=request.url.path,
                    status_code=e.status_code,
                    error=str(e)
                )
            raise


def setup_security_middleware(app: FastAPI):
    """Setup security middleware and configurations."""
    
    # HTTPS redirect in production
    if getattr(settings, 'ENVIRONMENT', 'development') == 'production':
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Trusted host middleware
    # Use lowercase 'allowed_hosts' field from Settings, fallback to env/uppercase for legacy support
    allowed_hosts = getattr(settings, 'allowed_hosts', getattr(settings, 'ALLOWED_HOSTS', ['localhost', '127.0.0.1']))
    if allowed_hosts and allowed_hosts != ['*']:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    
    # Custom security middleware
    security_config = getattr(settings, 'SECURITY_CONFIG', {})
    app.add_middleware(SecurityMiddleware, config=security_config)
    
    # CORS configuration (restrictive by default)
    from fastapi.middleware.cors import CORSMiddleware
    
    cors_origins = getattr(settings, 'CORS_ORIGINS', [])
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
            allow_headers=['*'],
            expose_headers=['X-Request-ID'],
            max_age=3600
        )
    
    logger.info("Security middleware configured", 
                https_redirect=getattr(settings, 'ENVIRONMENT', 'development') == 'production',
                trusted_hosts=allowed_hosts,
                cors_origins=cors_origins)


def get_security_headers() -> Dict[str, str]:
    """Get recommended security headers."""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self' cdn.jsdelivr.net fastapi.tiangolo.com; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; img-src 'self' fastapi.tiangolo.com data:;",
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }


def cleanup_security_store():
    """Cleanup expired entries from security store."""
    rate_limit_store.cleanup_expired()


# Security monitoring endpoint
async def get_security_stats() -> dict:
    """Get security statistics for monitoring."""
    return {
        "blocked_ips": len(rate_limit_store.blocked_ips),
        "active_rate_limits": len(rate_limit_store.requests),
        "timestamp": datetime.now().isoformat()
    }
