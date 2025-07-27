import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.models import Administrator
from app.models.auth.two_factor import TwoFactorAuth, TwoFactorBackupCode, TwoFactorSession, ApiKey
from app.repositories.base import BaseRepository
import logging
import json

logger = logging.getLogger(__name__)


class TwoFactorService:
    """Service for handling Two-Factor Authentication"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tfa_repo = BaseRepository(TwoFactorAuth, db)
        self.backup_repo = BaseRepository(TwoFactorBackupCode, db)
        self.session_repo = BaseRepository(TwoFactorSession, db)
        self.admin_repo = BaseRepository(Administrator, db)

    def setup_totp(self, admin_id: int, issuer_name: str = "ISP Framework") -> Dict[str, Any]:
        """Set up TOTP 2FA for an administrator"""
        admin = self.admin_repo.get(admin_id)
        if not admin:
            raise ValueError("Administrator not found")
        
        # Check if 2FA is already enabled
        existing_2fa = self.tfa_repo.get_by_field("admin_id", admin_id)
        if existing_2fa and existing_2fa.is_enabled:
            raise ValueError("2FA is already enabled for this administrator")
        
        # Generate secret key
        secret_key = pyotp.random_base32()
        
        # Create or update 2FA record
        tfa_data = {
            "admin_id": admin_id,
            "method": "totp",
            "secret_key": secret_key,  # In production, this should be encrypted
            "is_enabled": False  # Will be enabled after verification
        }
        
        if existing_2fa:
            tfa = self.tfa_repo.update(existing_2fa.id, tfa_data)
        else:
            tfa = self.tfa_repo.create(tfa_data)
        
        # Generate QR code
        totp = pyotp.TOTP(secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=admin.email,
            issuer_name=issuer_name
        )
        
        # Create QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        logger.info(f"TOTP 2FA setup initiated for admin: {admin.username}")
        
        return {
            "secret_key": secret_key,
            "qr_code": f"data:image/png;base64,{qr_code_base64}",
            "manual_entry_key": secret_key,
            "issuer": issuer_name,
            "account_name": admin.email
        }

    def verify_totp_setup(self, admin_id: int, verification_code: str) -> Dict[str, Any]:
        """Verify TOTP setup and enable 2FA"""
        tfa = self.tfa_repo.get_by_field("admin_id", admin_id)
        if not tfa or not tfa.secret_key:
            raise ValueError("2FA setup not found. Please initiate setup first.")
        
        if tfa.is_enabled:
            raise ValueError("2FA is already enabled")
        
        # Verify the code
        totp = pyotp.TOTP(tfa.secret_key)
        if not totp.verify(verification_code, valid_window=2):  # Allow 2 time windows (±60 seconds)
            raise ValueError("Invalid verification code")
        
        # Generate backup codes
        backup_codes = self._generate_backup_codes(admin_id)
        
        # Enable 2FA
        update_data = {
            "is_enabled": True,
            "verified_at": datetime.utcnow(),
            "backup_codes": json.dumps(backup_codes)  # In production, encrypt this
        }
        self.tfa_repo.update(tfa.id, update_data)
        
        logger.info(f"TOTP 2FA enabled for admin ID: {admin_id}")
        
        return {
            "enabled": True,
            "backup_codes": backup_codes,
            "message": "2FA has been successfully enabled"
        }

    def verify_totp_code(self, admin_id: int, code: str, client_ip: str = None) -> bool:
        """Verify TOTP code for authentication"""
        tfa = self.tfa_repo.get_by_field("admin_id", admin_id)
        if not tfa or not tfa.is_enabled:
            return False
        
        # Check if account is locked
        if tfa.locked_until and datetime.utcnow() < tfa.locked_until:
            logger.warning(f"2FA locked for admin ID: {admin_id}")
            return False
        
        # Try TOTP verification first
        totp = pyotp.TOTP(tfa.secret_key)
        if totp.verify(code, valid_window=1):
            # Reset failed attempts and update last used
            self.tfa_repo.update(tfa.id, {
                "failed_attempts": 0,
                "last_used": datetime.utcnow(),
                "locked_until": None
            })
            logger.info(f"TOTP verification successful for admin ID: {admin_id}")
            return True
        
        # Try backup code verification
        if self._verify_backup_code(admin_id, code, client_ip):
            self.tfa_repo.update(tfa.id, {
                "failed_attempts": 0,
                "last_used": datetime.utcnow(),
                "locked_until": None
            })
            logger.info(f"Backup code verification successful for admin ID: {admin_id}")
            return True
        
        # Increment failed attempts
        failed_attempts = tfa.failed_attempts + 1
        update_data = {"failed_attempts": failed_attempts}
        
        # Lock account after 5 failed attempts
        if failed_attempts >= 5:
            update_data["locked_until"] = datetime.utcnow() + timedelta(minutes=30)
            logger.warning(f"2FA locked due to failed attempts for admin ID: {admin_id}")
        
        self.tfa_repo.update(tfa.id, update_data)
        return False

    def disable_2fa(self, admin_id: int, verification_code: str) -> bool:
        """Disable 2FA for an administrator"""
        tfa = self.tfa_repo.get_by_field("admin_id", admin_id)
        if not tfa or not tfa.is_enabled:
            return False
        
        # Verify current code before disabling
        if not self.verify_totp_code(admin_id, verification_code):
            return False
        
        # Disable 2FA and clear sensitive data
        update_data = {
            "is_enabled": False,
            "secret_key": None,
            "backup_codes": None,
            "failed_attempts": 0,
            "locked_until": None
        }
        self.tfa_repo.update(tfa.id, update_data)
        
        # Remove all backup codes
        backup_codes = self.backup_repo.get_all(filters={"admin_id": admin_id})
        for backup_code in backup_codes:
            self.backup_repo.delete(backup_code.id)
        
        logger.info(f"2FA disabled for admin ID: {admin_id}")
        return True

    def create_2fa_session(self, admin_id: int, client_ip: str, user_agent: str) -> str:
        """Create a temporary 2FA session for pending verification"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=5)  # 5-minute expiration
        
        session_data = {
            "admin_id": admin_id,
            "session_token": session_token,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "expires_at": expires_at
        }
        
        self.session_repo.create(session_data)
        logger.info(f"2FA session created for admin ID: {admin_id}")
        return session_token

    def verify_2fa_session(self, session_token: str, verification_code: str) -> Optional[Administrator]:
        """Verify 2FA session and complete authentication"""
        session = self.session_repo.get_by_field("session_token", session_token)
        if not session or session.is_verified:
            return None
        
        if datetime.utcnow() > session.expires_at:
            logger.info(f"2FA session expired: {session_token[:10]}...")
            return None
        
        # Verify the 2FA code
        if not self.verify_totp_code(session.admin_id, verification_code, session.client_ip):
            return None
        
        # Mark session as verified
        self.session_repo.update(session.id, {
            "is_verified": True,
            "verified_at": datetime.utcnow()
        })
        
        # Return the administrator
        admin = self.admin_repo.get(session.admin_id)
        logger.info(f"2FA session verified for admin: {admin.username}")
        return admin

    def get_2fa_status(self, admin_id: int) -> Dict[str, Any]:
        """Get 2FA status for an administrator"""
        tfa = self.tfa_repo.get_by_field("admin_id", admin_id)
        
        if not tfa:
            return {
                "enabled": False,
                "method": None,
                "backup_codes_remaining": 0
            }
        
        # Count remaining backup codes
        backup_codes_remaining = 0
        if tfa.backup_codes:
            try:
                codes = json.loads(tfa.backup_codes)
                backup_codes_remaining = len(codes)
            except:
                backup_codes_remaining = 0
        
        return {
            "enabled": tfa.is_enabled,
            "method": tfa.method,
            "verified_at": tfa.verified_at,
            "last_used": tfa.last_used,
            "backup_codes_remaining": backup_codes_remaining,
            "locked_until": tfa.locked_until
        }

    def _generate_backup_codes(self, admin_id: int, count: int = 10) -> List[str]:
        """Generate backup codes for 2FA recovery"""
        backup_codes = []
        
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = secrets.token_hex(4).upper()
            backup_codes.append(code)
            
            # Store hashed version in database
            code_data = {
                "admin_id": admin_id,
                "code_hash": get_password_hash(code)
            }
            self.backup_repo.create(code_data)
        
        return backup_codes

    def _verify_backup_code(self, admin_id: int, code: str, client_ip: str = None) -> bool:
        """Verify a backup code"""
        backup_codes = self.backup_repo.get_all_by_field("admin_id", admin_id)
        
        for backup_code in backup_codes:
            if backup_code.is_used:
                continue
                
            if verify_password(code, backup_code.code_hash):
                # Mark code as used
                self.backup_repo.update(backup_code.id, {
                    "is_used": True,
                    "used_at": datetime.utcnow(),
                    "used_ip": client_ip
                })
                return True
        
        return False


class ApiKeyService:
    """Service for handling API Key authentication"""
    
    def __init__(self, db: Session):
        self.db = db
        self.api_key_repo = BaseRepository(ApiKey, db)
        self.admin_repo = BaseRepository(Administrator, db)

    def create_api_key(
        self,
        admin_id: int,
        key_name: str,
        scopes: str = "api",
        permissions: Dict[str, Any] = None,
        expires_in_days: int = None
    ) -> Dict[str, Any]:
        """Create a new API key"""
        admin = self.admin_repo.get(admin_id)
        if not admin:
            raise ValueError("Administrator not found")
        
        # Generate API key
        api_key = f"isp_{secrets.token_urlsafe(32)}"
        key_prefix = api_key[:12]  # First 12 characters for identification
        
        # Set expiration if specified
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        key_data = {
            "admin_id": admin_id,
            "key_name": key_name,
            "key_prefix": key_prefix,
            "key_hash": get_password_hash(api_key),
            "scopes": scopes,
            "permissions": json.dumps(permissions or {}),
            "expires_at": expires_at
        }
        
        api_key_record = self.api_key_repo.create(key_data)
        
        logger.info(f"API key created: {key_name} for admin: {admin.username}")
        
        return {
            "api_key": api_key,  # Only returned once
            "key_id": api_key_record.id,
            "key_name": key_name,
            "key_prefix": key_prefix,
            "scopes": scopes.split(","),
            "expires_at": expires_at,
            "created_at": api_key_record.created_at
        }

    def validate_api_key(self, api_key: str, client_ip: str = None) -> Optional[Dict[str, Any]]:
        """Validate an API key and return associated data"""
        if not api_key.startswith("isp_"):
            return None
        
        key_prefix = api_key[:12]
        api_key_record = self.api_key_repo.get_by_field("key_prefix", key_prefix)
        
        if not api_key_record or not api_key_record.is_active:
            return None
        
        # Verify the full key
        if not verify_password(api_key, api_key_record.key_hash):
            return None
        
        # Check expiration
        if api_key_record.expires_at and datetime.utcnow() > api_key_record.expires_at:
            logger.info(f"API key expired: {key_prefix}")
            return None
        
        # Check IP restrictions if configured
        if api_key_record.allowed_ips:
            try:
                allowed_ips = json.loads(api_key_record.allowed_ips)
                if client_ip and client_ip not in allowed_ips:
                    logger.warning(f"API key access denied from IP: {client_ip}")
                    return None
            except:
                pass
        
        # Update usage statistics
        self.api_key_repo.update(api_key_record.id, {
            "last_used": datetime.utcnow(),
            "usage_count": api_key_record.usage_count + 1
        })
        
        # Get admin details
        admin = self.admin_repo.get(api_key_record.admin_id)
        
        return {
            "api_key_id": api_key_record.id,
            "admin_id": admin.id,
            "admin_username": admin.username,
            "scopes": api_key_record.scopes.split(","),
            "permissions": json.loads(api_key_record.permissions or "{}"),
            "key_name": api_key_record.key_name
        }

    def revoke_api_key(self, key_id: int, admin_id: int) -> bool:
        """Revoke an API key"""
        api_key = self.api_key_repo.get(key_id)
        if not api_key or api_key.admin_id != admin_id:
            return False
        
        self.api_key_repo.update(key_id, {"is_active": False})
        logger.info(f"API key revoked: {api_key.key_name}")
        return True

    def list_api_keys(self, admin_id: int) -> List[Dict[str, Any]]:
        """List API keys for an administrator"""
        api_keys = self.api_key_repo.get_all(filters={"admin_id": admin_id})
        
        return [
            {
                "id": key.id,
                "key_name": key.key_name,
                "key_prefix": key.key_prefix,
                "scopes": key.scopes.split(","),
                "is_active": key.is_active,
                "last_used": key.last_used,
                "usage_count": key.usage_count,
                "expires_at": key.expires_at,
                "created_at": key.created_at
            }
            for key in api_keys
        ]
