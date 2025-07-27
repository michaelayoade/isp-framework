"""
Secrets management for ISP Framework.

Provides secure handling of sensitive configuration data with support for
various backends (environment variables, Vault, AWS Secrets Manager).
"""
import os
import json
import base64
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog

from app.core.config import settings
from app.core.observability import log_audit_event

logger = structlog.get_logger("isp.secrets")


class SecretsManager:
    """Manages application secrets with multiple backend support."""
    
    def __init__(self):
        # Use local backends only - environment or encrypted file
        self.backend = getattr(settings, 'SECRETS_BACKEND', 'environment')
        
        # Force local backends only
        if self.backend not in ['environment', 'encrypted_file']:
            logger.warning(f"Cloud backend '{self.backend}' not supported in local mode, falling back to 'environment'")
            self.backend = 'environment'
        
        self.encryption_key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key) if self.encryption_key else None
        
        logger.info("Local secrets manager initialized", backend=self.backend, encryption_enabled=bool(self.cipher_suite))
    
    def _get_encryption_key(self) -> Optional[bytes]:
        """Get or generate encryption key for local secret encryption."""
        key_env = os.getenv('ISP_SECRETS_KEY')
        if key_env:
            return base64.urlsafe_b64decode(key_env.encode())
        
        # Generate key from master password if available
        master_password = os.getenv('ISP_MASTER_PASSWORD')
        if master_password:
            salt = os.getenv('ISP_SECRETS_SALT', 'isp-framework-salt').encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        
        return None
    
    def get_secret(self, key: str, default: Any = None) -> Any:
        """Get a secret value from the configured local backend."""
        try:
            if self.backend == 'environment':
                return self._get_from_environment(key, default)
            elif self.backend == 'encrypted_file':
                return self._get_from_encrypted_file(key, default)
            else:
                logger.warning(f"Unknown local secrets backend: {self.backend}")
                return default
        except Exception as e:
            logger.error(f"Failed to get secret '{key}'", error=str(e))
            return default
    
    def set_secret(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a secret value in the configured local backend."""
        try:
            if self.backend == 'environment':
                return self._set_to_environment(key, value)
            elif self.backend == 'encrypted_file':
                return self._set_to_encrypted_file(key, value)
            else:
                logger.warning(f"Unknown local secrets backend: {self.backend}")
                return False
        except Exception as e:
            logger.error(f"Failed to set secret '{key}'", error=str(e))
            return False
    
    def _get_from_environment(self, key: str, default: Any = None) -> Any:
        """Get secret from environment variables."""
        env_key = f"ISP_SECRET_{key.upper().replace('.', '_').replace('-', '_')}"
        value = os.getenv(env_key, default)
        
        # Try to decrypt if it looks like encrypted data
        if isinstance(value, str) and value.startswith('enc:') and self.cipher_suite:
            try:
                encrypted_data = base64.urlsafe_b64decode(value[4:].encode())
                decrypted = self.cipher_suite.decrypt(encrypted_data)
                return decrypted.decode()
            except Exception as e:
                logger.warning(f"Failed to decrypt secret '{key}'", error=str(e))
                return default
        
        return value
    
    def _set_to_environment(self, key: str, value: Any) -> bool:
        """Set secret to environment (not persistent, for runtime only)."""
        env_key = f"ISP_SECRET_{key.upper().replace('.', '_').replace('-', '_')}"
        
        # Encrypt sensitive values
        if self.cipher_suite and isinstance(value, str):
            try:
                encrypted = self.cipher_suite.encrypt(value.encode())
                encrypted_value = 'enc:' + base64.urlsafe_b64encode(encrypted).decode()
                os.environ[env_key] = encrypted_value
            except Exception as e:
                logger.warning(f"Failed to encrypt secret '{key}'", error=str(e))
                os.environ[env_key] = str(value)
        else:
            os.environ[env_key] = str(value)
        
        return True
    
    # Vault methods removed - using local backends only
    
    # AWS methods removed - using local backends only
    
    def _get_from_encrypted_file(self, key: str, default: Any = None) -> Any:
        """Get secret from encrypted file."""
        if not self.cipher_suite:
            logger.warning("No encryption key available for encrypted file backend")
            return default
        
        secrets_file = getattr(settings, 'ENCRYPTED_SECRETS_FILE', 'secrets.enc')
        
        try:
            if not os.path.exists(secrets_file):
                return default
            
            with open(secrets_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            secrets = json.loads(decrypted_data.decode())
            
            return secrets.get(key, default)
            
        except Exception as e:
            logger.warning(f"Failed to read encrypted secrets file", error=str(e))
            return default
    
    def _set_to_encrypted_file(self, key: str, value: Any) -> bool:
        """Set secret to encrypted file."""
        if not self.cipher_suite:
            logger.warning("No encryption key available for encrypted file backend")
            return False
        
        secrets_file = getattr(settings, 'ENCRYPTED_SECRETS_FILE', 'secrets.enc')
        
        try:
            # Load existing secrets
            secrets = {}
            if os.path.exists(secrets_file):
                with open(secrets_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                secrets = json.loads(decrypted_data.decode())
            
            # Update secret
            secrets[key] = value
            secrets['_updated_at'] = datetime.now().isoformat()
            
            # Encrypt and save
            json_data = json.dumps(secrets, indent=2)
            encrypted_data = self.cipher_suite.encrypt(json_data.encode())
            
            with open(secrets_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(secrets_file, 0o600)
            
            log_audit_event(
                domain="secrets",
                event="secret_stored_file",
                secret_key=key
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write encrypted secrets file", error=str(e))
            return False
    
    def rotate_encryption_key(self) -> bool:
        """Rotate the encryption key (for encrypted file backend)."""
        if self.backend != 'encrypted_file':
            logger.warning("Key rotation only supported for encrypted_file backend")
            return False
        
        try:
            # Generate new key
            new_key = Fernet.generate_key()
            new_cipher = Fernet(new_key)
            
            # Re-encrypt all secrets with new key
            secrets_file = getattr(settings, 'ENCRYPTED_SECRETS_FILE', 'secrets.enc')
            
            if os.path.exists(secrets_file):
                # Decrypt with old key
                with open(secrets_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                
                # Encrypt with new key
                new_encrypted_data = new_cipher.encrypt(decrypted_data)
                
                # Write back
                with open(secrets_file, 'wb') as f:
                    f.write(new_encrypted_data)
            
            # Update cipher suite
            self.encryption_key = new_key
            self.cipher_suite = new_cipher
            
            log_audit_event(
                domain="secrets",
                event="encryption_key_rotated"
            )
            
            logger.info("Encryption key rotated successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to rotate encryption key", error=str(e))
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the local secrets backend."""
        health = {
            "backend": self.backend,
            "status": "unknown",
            "details": {}
        }
        
        try:
            if self.backend == 'environment':
                health["status"] = "healthy"
                health["details"]["encryption_available"] = self.cipher_suite is not None
                health["details"]["local_backend"] = True
            
            elif self.backend == 'encrypted_file':
                health["status"] = "healthy" if self.cipher_suite else "unhealthy"
                health["details"]["local_backend"] = True
                if not self.cipher_suite:
                    health["details"]["error"] = "No encryption key available"
                else:
                    # Check if we can read/write to the secrets file
                    secrets_file = getattr(settings, 'ENCRYPTED_SECRETS_FILE', 'secrets.enc')
                    health["details"]["secrets_file"] = secrets_file
                    health["details"]["file_exists"] = os.path.exists(secrets_file)
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["details"]["error"] = str(e)
        
        return health


# Global secrets manager instance
secrets_manager = SecretsManager()


def get_secret(key: str, default: Any = None) -> Any:
    """Get a secret value (convenience function)."""
    return secrets_manager.get_secret(key, default)


def set_secret(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set a secret value (convenience function)."""
    return secrets_manager.set_secret(key, value, ttl)


# Common secret keys used throughout the application
class SecretKeys:
    """Common secret keys used in the application."""
    
    # Database
    DATABASE_PASSWORD = "database.password"
    DATABASE_URL = "database.url"
    
    # JWT
    JWT_SECRET_KEY = "jwt.secret_key"
    JWT_REFRESH_SECRET = "jwt.refresh_secret"
    
    # Email/SMTP
    SMTP_PASSWORD = "smtp.password"
    SMTP_USERNAME = "smtp.username"
    
    # External APIs
    PAYMENT_GATEWAY_SECRET = "payment.gateway_secret"
    SMS_API_KEY = "sms.api_key"
    
    # MinIO/S3
    MINIO_SECRET_KEY = "minio.secret_key"
    S3_SECRET_KEY = "s3.secret_key"
    
    # Third-party integrations
    RADIUS_SHARED_SECRET = "radius.shared_secret"
    WEBHOOK_SIGNING_SECRET = "webhook.signing_secret"


def initialize_secrets_from_env():
    """Initialize common secrets from environment variables."""
    """This function migrates existing env vars to the secrets manager."""
    
    env_to_secret_mapping = {
        'DATABASE_PASSWORD': SecretKeys.DATABASE_PASSWORD,
        'JWT_SECRET_KEY': SecretKeys.JWT_SECRET_KEY,
        'SMTP_PASSWORD': SecretKeys.SMTP_PASSWORD,
        'MINIO_SECRET_KEY': SecretKeys.MINIO_SECRET_KEY,
        'RADIUS_SHARED_SECRET': SecretKeys.RADIUS_SHARED_SECRET,
    }
    
    migrated_count = 0
    for env_key, secret_key in env_to_secret_mapping.items():
        env_value = os.getenv(env_key)
        if env_value:
            if set_secret(secret_key, env_value):
                migrated_count += 1
                logger.info(f"Migrated {env_key} to secrets manager")
    
    if migrated_count > 0:
        logger.info(f"Migrated {migrated_count} secrets from environment variables")
    
    return migrated_count
