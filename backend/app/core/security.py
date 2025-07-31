import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import redis
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.customer.base import Customer
from app.models.customer.portal_complete import CustomerPortalSession
from app.models.foundation.base import Reseller

logger = logging.getLogger(__name__)

# Redis connection for token blacklist
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
except Exception as e:
    logger.warning(
        f"Redis connection failed: {e}. Token revocation will use database only."
    )
    redis_client = None


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    scopes: Optional[List[str]] = None,
    user_role: Optional[str] = None,
) -> str:
    """Create a JWT access token with role and scope information."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    # Add unique token identifier for revocation tracking
    jti = str(uuid.uuid4())

    to_encode.update(
        {
            "exp": expire,
            "type": "access",
            "jti": jti,
            "iat": datetime.now(timezone.utc),
            "scope": " ".join(scopes) if scopes else "",
            "role": user_role,
        }
    )

    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with reuse detection."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    # Add unique token identifier for reuse detection
    jti = str(uuid.uuid4())

    to_encode.update(
        {
            "exp": expire,
            "type": "refresh",
            "jti": jti,
            "iat": datetime.now(timezone.utc),
        }
    )

    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify and decode a JWT token with blacklist check."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != token_type:
            return None

        # Check if token is blacklisted (revoked)
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            logger.info(f"Revoked token attempted access: {jti}")
            return None

        return payload
    except JWTError:
        return None


def create_credentials_exception(
    detail: str = "Could not validate credentials",
) -> HTTPException:
    """Create a credentials exception."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


# OAuth2 scheme with scopes
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scopes={
        "api": "General API access",
        "admin_portal": "Administrator portal access",
        "customer_portal": "Customer portal access",
        "reseller_portal": "Reseller portal access",
        "billing": "Billing system access",
        "network": "Network management access",
        "reports": "Reports and analytics access",
    },
)


def revoke_token(jti: str, expires_at: datetime) -> bool:
    """Add token to revocation blacklist."""
    if not redis_client:
        logger.warning("Redis not available for token revocation")
        return False

    try:
        # Calculate TTL based on token expiry
        ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            redis_client.setex(f"revoked_token:{jti}", ttl, "1")
            logger.info(f"Token {jti} added to blacklist with TTL {ttl}s")
            return True
    except Exception as e:
        logger.error(f"Failed to revoke token {jti}: {e}")

    return False


def is_token_revoked(jti: str) -> bool:
    """Check if token is in revocation blacklist."""
    if not redis_client:
        return False

    try:
        return redis_client.exists(f"revoked_token:{jti}") > 0
    except Exception as e:
        logger.error(f"Failed to check token revocation {jti}: {e}")
        return False


def detect_refresh_token_reuse(jti: str) -> bool:
    """Detect if refresh token has been used before (reuse attack)."""
    if not redis_client:
        return False

    try:
        key = f"used_refresh_token:{jti}"
        if redis_client.exists(key):
            logger.warning(f"Refresh token reuse detected: {jti}")
            return True

        # Mark token as used with 30-day TTL
        redis_client.setex(key, 30 * 24 * 60 * 60, "1")
        return False
    except Exception as e:
        logger.error(f"Failed to check refresh token reuse {jti}: {e}")
        return False


async def get_current_user(
    security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
) -> dict:
    """Get current user from JWT token with scope validation."""
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    # Verify token
    payload = verify_token(token, "access")
    if payload is None:
        raise credentials_exception

    # Extract user info
    username = payload.get("sub")
    user_id = payload.get("user_id")
    token_scopes = payload.get("scope", "").split()
    user_role = payload.get("role")

    if username is None:
        raise credentials_exception

    # Validate required scopes
    if security_scopes.scopes:
        required_scopes = set(security_scopes.scopes)
        user_scopes = set(token_scopes)

        if not required_scopes.issubset(user_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return {
        "username": username,
        "user_id": user_id,
        "scopes": token_scopes,
        "role": user_role,
        "jti": payload.get("jti"),
    }


# Convenience functions for common scope requirements
async def require_admin_access(
    current_user: dict = Security(get_current_user, scopes=["admin_portal"])
):
    """Require admin portal access."""
    return current_user


async def require_api_access(
    current_user: dict = Security(get_current_user, scopes=["api"])
):
    """Require general API access."""
    return current_user


async def require_billing_access(
    current_user: dict = Security(get_current_user, scopes=["billing"])
):
    """Require billing system access."""
    return current_user


async def require_network_access(
    current_user: dict = Security(get_current_user, scopes=["network"])
):
    """Require network management access."""
    return current_user


# Customer Portal Authentication


def get_current_admin_user(
    current_user: dict = Security(get_current_user, scopes=["admin"])
) -> dict:
    """Get current admin user with admin scope validation."""
    return current_user


def get_current_customer(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Customer:
    """Get current customer from portal session token or JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate customer credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # First try to validate as portal session token
        session = (
            db.query(CustomerPortalSession)
            .filter(
                CustomerPortalSession.session_token == token,
                CustomerPortalSession.is_active is True,
                CustomerPortalSession.expires_at > datetime.now(),
            )
            .first()
        )

        if session:
            # Update last activity
            session.last_activity = datetime.now()
            db.commit()

            # Get customer
            customer = db.query(Customer).filter_by(id=session.customer_id).first()
            if customer:
                return customer

        # If not a portal session, try JWT token
        payload = verify_token(token)
        customer_id: int = payload.get("sub")
        if customer_id is None:
            raise credentials_exception

        # Get customer from database
        customer = db.query(Customer).filter_by(id=customer_id).first()
        if customer is None:
            raise credentials_exception

        return customer

    except (JWTError, ValueError):
        raise credentials_exception


def get_current_reseller(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Reseller:
    """Get current reseller from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate reseller credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify JWT token
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception

        # Extract reseller info from token
        reseller_id = payload.get("sub")
        user_type = payload.get("user_type")

        # Ensure this is a reseller token
        if user_type != "reseller" or reseller_id is None:
            raise credentials_exception

        # Get reseller from database
        reseller = (
            db.query(Reseller)
            .filter(Reseller.id == reseller_id, Reseller.is_active is True)
            .first()
        )

        if reseller is None:
            raise credentials_exception

        return reseller

    except (JWTError, ValueError):
        raise credentials_exception
