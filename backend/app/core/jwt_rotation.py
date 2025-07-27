"""
JWT key rotation and management for ISP Framework.

Provides secure key rotation, validation, and management for JWT tokens.
"""
import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt
import structlog

from app.core.config import settings
from app.core.observability import log_audit_event

logger = structlog.get_logger("isp.security.jwt")


class JWTKeyManager:
    """Manages JWT signing keys with automatic rotation."""
    
    def __init__(self, key_dir: str = None):
        self.key_dir = key_dir or os.path.join(os.path.dirname(__file__), '..', '..', 'keys')
        self.keys_file = os.path.join(self.key_dir, 'jwt_keys.json')
        self.current_key_id = None
        self.keys: Dict[str, dict] = {}
        
        # Ensure key directory exists
        os.makedirs(self.key_dir, exist_ok=True)
        
        # Load existing keys or generate initial key
        self._load_keys()
        if not self.keys:
            self._generate_initial_key()
    
    def _generate_key_pair(self) -> Tuple[str, str]:
        """Generate RSA key pair for JWT signing."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return private_pem, public_pem
    
    def _generate_initial_key(self):
        """Generate the initial JWT signing key."""
        key_id = self._generate_key_id()
        private_key, public_key = self._generate_key_pair()
        
        key_data = {
            'id': key_id,
            'private_key': private_key,
            'public_key': public_key,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
            'status': 'active'
        }
        
        self.keys[key_id] = key_data
        self.current_key_id = key_id
        self._save_keys()
        
        log_audit_event(
            domain="security",
            event="jwt_key_generated",
            key_id=key_id,
            key_type="initial"
        )
        
        logger.info("Initial JWT key generated", key_id=key_id)
    
    def _generate_key_id(self) -> str:
        """Generate a unique key ID."""
        return f"jwt-{secrets.token_hex(8)}"
    
    def _load_keys(self):
        """Load keys from storage."""
        if os.path.exists(self.keys_file):
            try:
                with open(self.keys_file, 'r') as f:
                    data = json.load(f)
                    self.keys = data.get('keys', {})
                    self.current_key_id = data.get('current_key_id')
                    
                logger.info("JWT keys loaded", key_count=len(self.keys))
            except Exception as e:
                logger.error("Failed to load JWT keys", error=str(e))
                self.keys = {}
                self.current_key_id = None
    
    def _save_keys(self):
        """Save keys to storage."""
        try:
            data = {
                'keys': self.keys,
                'current_key_id': self.current_key_id,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Write to temporary file first, then rename (atomic operation)
            temp_file = self.keys_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            os.rename(temp_file, self.keys_file)
            
            # Set restrictive permissions
            os.chmod(self.keys_file, 0o600)
            
        except Exception as e:
            logger.error("Failed to save JWT keys", error=str(e))
            raise
    
    def get_current_private_key(self) -> str:
        """Get the current private key for signing."""
        if not self.current_key_id or self.current_key_id not in self.keys:
            raise ValueError("No current JWT key available")
        
        return self.keys[self.current_key_id]['private_key']
    
    def get_public_key(self, key_id: str) -> Optional[str]:
        """Get public key for verification by key ID."""
        if key_id in self.keys:
            return self.keys[key_id]['public_key']
        return None
    
    def get_current_key_id(self) -> str:
        """Get the current key ID."""
        return self.current_key_id
    
    def rotate_key(self, force: bool = False) -> str:
        """Rotate to a new JWT signing key."""
        # Check if rotation is needed
        if not force and self.current_key_id:
            current_key = self.keys[self.current_key_id]
            expires_at = datetime.fromisoformat(current_key['expires_at'].replace('Z', '+00:00'))
            
            # Only rotate if key expires within 7 days
            if expires_at > datetime.now(timezone.utc) + timedelta(days=7):
                logger.info("Key rotation not needed", 
                           current_key_id=self.current_key_id,
                           expires_at=expires_at.isoformat())
                return self.current_key_id
        
        # Generate new key
        new_key_id = self._generate_key_id()
        private_key, public_key = self._generate_key_pair()
        
        new_key_data = {
            'id': new_key_id,
            'private_key': private_key,
            'public_key': public_key,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
            'status': 'active'
        }
        
        # Mark old key as deprecated (but keep for verification)
        if self.current_key_id and self.current_key_id in self.keys:
            self.keys[self.current_key_id]['status'] = 'deprecated'
            self.keys[self.current_key_id]['deprecated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Add new key and make it current
        self.keys[new_key_id] = new_key_data
        old_key_id = self.current_key_id
        self.current_key_id = new_key_id
        
        self._save_keys()
        
        log_audit_event(
            domain="security",
            event="jwt_key_rotated",
            old_key_id=old_key_id,
            new_key_id=new_key_id,
            forced=force
        )
        
        logger.info("JWT key rotated", 
                   old_key_id=old_key_id,
                   new_key_id=new_key_id,
                   forced=force)
        
        return new_key_id
    
    def cleanup_expired_keys(self, keep_days: int = 30):
        """Remove expired keys older than keep_days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=keep_days)
        expired_keys = []
        
        for key_id, key_data in list(self.keys.items()):
            if key_data['status'] == 'deprecated':
                deprecated_at = datetime.fromisoformat(key_data.get('deprecated_at', key_data['created_at']).replace('Z', '+00:00'))
                if deprecated_at < cutoff_date:
                    expired_keys.append(key_id)
        
        for key_id in expired_keys:
            del self.keys[key_id]
            logger.info("Expired JWT key removed", key_id=key_id)
        
        if expired_keys:
            self._save_keys()
            log_audit_event(
                domain="security",
                event="jwt_keys_cleaned",
                removed_keys=expired_keys,
                keep_days=keep_days
            )
        
        return expired_keys
    
    def get_key_info(self) -> Dict[str, dict]:
        """Get information about all keys (without private keys)."""
        info = {}
        for key_id, key_data in self.keys.items():
            info[key_id] = {
                'id': key_data['id'],
                'created_at': key_data['created_at'],
                'expires_at': key_data['expires_at'],
                'status': key_data['status'],
                'is_current': key_id == self.current_key_id
            }
        return info
    
    def verify_token_signature(self, token: str) -> Tuple[bool, Optional[dict]]:
        """Verify JWT token signature with any valid key."""
        try:
            # Decode header to get key ID
            header = jwt.get_unverified_header(token)
            key_id = header.get('kid')
            
            if not key_id or key_id not in self.keys:
                return False, None
            
            public_key = self.keys[key_id]['public_key']
            
            # Verify signature
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                options={'verify_exp': True}
            )
            
            return True, payload
            
        except jwt.ExpiredSignatureError:
            return False, {'error': 'token_expired'}
        except jwt.InvalidTokenError as e:
            return False, {'error': str(e)}
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            return False, {'error': 'verification_failed'}


# Global key manager instance
jwt_key_manager = JWTKeyManager()


def get_jwt_key_manager() -> JWTKeyManager:
    """Get the global JWT key manager instance."""
    return jwt_key_manager


def create_jwt_token(payload: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token with the current signing key."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
    
    payload.update({
        'exp': expire,
        'iat': datetime.now(timezone.utc),
        'iss': getattr(settings, 'JWT_ISSUER', 'isp-framework')
    })
    
    private_key = jwt_key_manager.get_current_private_key()
    key_id = jwt_key_manager.get_current_key_id()
    
    return jwt.encode(
        payload,
        private_key,
        algorithm='RS256',
        headers={'kid': key_id}
    )


def verify_jwt_token(token: str) -> Tuple[bool, Optional[dict]]:
    """Verify a JWT token."""
    return jwt_key_manager.verify_token_signature(token)


def rotate_jwt_keys(force: bool = False) -> str:
    """Rotate JWT signing keys."""
    return jwt_key_manager.rotate_key(force=force)


def cleanup_expired_jwt_keys(keep_days: int = 30) -> List[str]:
    """Clean up expired JWT keys."""
    return jwt_key_manager.cleanup_expired_keys(keep_days=keep_days)


def get_jwt_key_info() -> Dict[str, dict]:
    """Get information about JWT keys."""
    return jwt_key_manager.get_key_info()


# Scheduled tasks for key management
async def scheduled_key_rotation():
    """Scheduled task for automatic key rotation."""
    try:
        rotated_key = jwt_key_manager.rotate_key(force=False)
        logger.info("Scheduled key rotation completed", key_id=rotated_key)
    except Exception as e:
        logger.error("Scheduled key rotation failed", error=str(e))


async def scheduled_key_cleanup():
    """Scheduled task for cleaning up expired keys."""
    try:
        removed_keys = jwt_key_manager.cleanup_expired_keys(keep_days=30)
        if removed_keys:
            logger.info("Scheduled key cleanup completed", removed_count=len(removed_keys))
    except Exception as e:
        logger.error("Scheduled key cleanup failed", error=str(e))
