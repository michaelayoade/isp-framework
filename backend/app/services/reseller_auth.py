"""
Reseller Authentication Service

Authentication and authorization service for reseller management in single-tenant ISP Framework.
Provides JWT-based authentication separate from admin authentication.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.models.foundation import Reseller
from app.repositories.reseller import ResellerRepository
from app.core.config import settings
from app.core.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings for resellers (separate from admin)
RESELLER_SECRET_KEY = settings.secret_key + "_reseller"  # Different key for resellers
RESELLER_ALGORITHM = "HS256"
RESELLER_ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours (longer for resellers)


class ResellerAuthService:
    """Service for reseller authentication and authorization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ResellerRepository(db)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def authenticate_reseller(self, email: str, password: str) -> Optional[Reseller]:
        """Authenticate reseller by email and password"""
        logger.info(f"Authenticating reseller: {email}")
        
        reseller = self.repository.get_by_email(email)
        if not reseller:
            logger.warning(f"Reseller not found: {email}")
            return None
        
        if not reseller.is_active:
            logger.warning(f"Inactive reseller attempted login: {email}")
            return None
        
        # Check if reseller has password_hash field (we'll add this to model)
        if not hasattr(reseller, 'password_hash') or not reseller.password_hash:
            logger.warning(f"Reseller has no password set: {email}")
            return None
        
        if not self.verify_password(password, reseller.password_hash):
            logger.warning(f"Invalid password for reseller: {email}")
            return None
        
        logger.info(f"Reseller authenticated successfully: {email}")
        return reseller
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token for reseller"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=RESELLER_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, RESELLER_SECRET_KEY, algorithm=RESELLER_ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, RESELLER_SECRET_KEY, algorithms=[RESELLER_ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
    
    def get_current_reseller(self, token: str) -> Optional[Reseller]:
        """Get current reseller from JWT token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        reseller_id = payload.get("sub")
        if not reseller_id:
            return None
        
        try:
            reseller_id = int(reseller_id)
            reseller = self.repository.get_by_id(reseller_id)
            if not reseller or not reseller.is_active:
                return None
            return reseller
        except (ValueError, TypeError):
            return None
    
    def login_reseller(self, email: str, password: str) -> Dict[str, Any]:
        """Login reseller and return token"""
        reseller = self.authenticate_reseller(email, password)
        if not reseller:
            raise ValidationError("Invalid email or password")
        
        # Create access token
        access_token_expires = timedelta(minutes=RESELLER_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={
                "sub": str(reseller.id),
                "email": reseller.email,
                "name": reseller.name,
                "type": "reseller"  # Token type identifier
            },
            expires_delta=access_token_expires
        )
        
        # Update last login time
        if hasattr(reseller, 'last_login'):
            update_data = {'last_login': datetime.now(timezone.utc)}
            self.repository.update(reseller.id, update_data)
        
        logger.info(f"Reseller logged in successfully: {reseller.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": RESELLER_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "reseller": {
                "id": reseller.id,
                "name": reseller.name,
                "email": reseller.email,
                "code": reseller.code,
                "territory": reseller.territory,
                "commission_percentage": float(reseller.commission_percentage),
                "is_active": reseller.is_active
            }
        }
    
    def set_reseller_password(self, reseller_id: int, password: str) -> bool:
        """Set password for reseller (admin function)"""
        logger.info(f"Setting password for reseller: {reseller_id}")
        
        reseller = self.repository.get_by_id(reseller_id)
        if not reseller:
            raise NotFoundError(f"Reseller with ID {reseller_id} not found")
        
        # Hash password and update reseller
        password_hash = self.get_password_hash(password)
        update_data = {
            'password_hash': password_hash,
            'updated_at': datetime.now(timezone.utc)
        }
        
        self.repository.update(reseller.id, update_data)
        logger.info(f"Password set successfully for reseller: {reseller_id}")
        return True
    
    def change_reseller_password(self, reseller_id: int, current_password: str, new_password: str) -> bool:
        """Change reseller password (reseller function)"""
        logger.info(f"Changing password for reseller: {reseller_id}")
        
        reseller = self.repository.get_by_id(reseller_id)
        if not reseller:
            raise NotFoundError(f"Reseller with ID {reseller_id} not found")
        
        # Verify current password
        if not hasattr(reseller, 'password_hash') or not reseller.password_hash:
            raise ValidationError("No password set for this reseller")
        
        if not self.verify_password(current_password, reseller.password_hash):
            raise ValidationError("Current password is incorrect")
        
        # Set new password
        password_hash = self.get_password_hash(new_password)
        update_data = {
            'password_hash': password_hash,
            'updated_at': datetime.now(timezone.utc)
        }
        
        self.repository.update(reseller.id, update_data)
        logger.info(f"Password changed successfully for reseller: {reseller_id}")
        return True
    
    def refresh_token(self, token: str) -> Dict[str, Any]:
        """Refresh access token"""
        payload = self.verify_token(token)
        if not payload:
            raise ValidationError("Invalid token")
        
        reseller_id = payload.get("sub")
        if not reseller_id:
            raise ValidationError("Invalid token payload")
        
        reseller = self.repository.get_by_id(int(reseller_id))
        if not reseller or not reseller.is_active:
            raise ValidationError("Reseller not found or inactive")
        
        # Create new access token
        access_token_expires = timedelta(minutes=RESELLER_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={
                "sub": str(reseller.id),
                "email": reseller.email,
                "name": reseller.name,
                "type": "reseller"
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": RESELLER_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def validate_reseller_access(self, reseller_id: int, customer_id: int) -> bool:
        """Validate that reseller has access to specific customer"""
        # Check if customer is assigned to this reseller
        from app.models.base import Customer
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            return False
        
        # Customer must be assigned to this reseller
        return customer.reseller_id == reseller_id
    
    def get_reseller_permissions(self, reseller_id: int) -> Dict[str, Any]:
        """Get reseller permissions and access levels"""
        reseller = self.repository.get_by_id(reseller_id)
        if not reseller:
            return {}
        
        customer_count = self.repository.get_reseller_customer_count(reseller_id)
        customer_limit_reached = (
            reseller.customer_limit is not None and 
            customer_count >= reseller.customer_limit
        )
        
        return {
            "reseller_id": reseller_id,
            "can_manage_customers": True,
            "can_view_reports": True,
            "can_assign_customers": not customer_limit_reached,
            "customer_count": customer_count,
            "customer_limit": reseller.customer_limit,
            "territory": reseller.territory,
            "commission_percentage": float(reseller.commission_percentage)
        }
