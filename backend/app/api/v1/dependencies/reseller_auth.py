"""
Reseller Authentication Dependencies

FastAPI dependencies for reseller authentication and authorization.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.reseller_auth import ResellerAuthService
from app.models.foundation import Reseller

security = HTTPBearer()


async def get_current_reseller(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Reseller:
    """
    Dependency to get current authenticated reseller from JWT token.
    Raises HTTPException if token is invalid or reseller not found.
    """
    auth_service = ResellerAuthService(db)
    reseller = auth_service.get_current_reseller(credentials.credentials)
    
    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return reseller


async def get_optional_reseller(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Reseller]:
    """
    Dependency to get current reseller if token is provided and valid.
    Returns None if no token or invalid token (doesn't raise exception).
    """
    if not credentials:
        return None
    
    auth_service = ResellerAuthService(db)
    return auth_service.get_current_reseller(credentials.credentials)


async def validate_reseller_customer_access(
    customer_id: int,
    current_reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
) -> bool:
    """
    Dependency to validate that current reseller has access to specific customer.
    Raises HTTPException if reseller doesn't have access.
    """
    auth_service = ResellerAuthService(db)
    has_access = auth_service.validate_reseller_access(current_reseller.id, customer_id)
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Reseller does not have access to customer {customer_id}"
        )
    
    return True


async def get_reseller_permissions(
    current_reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to get current reseller's permissions and access levels.
    """
    auth_service = ResellerAuthService(db)
    return auth_service.get_reseller_permissions(current_reseller.id)
