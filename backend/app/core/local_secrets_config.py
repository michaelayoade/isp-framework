"""
Local secrets configuration for ISP Framework.

Provides configuration and utilities for local-only secrets management.
"""

import base64
import os
from pathlib import Path

import structlog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = structlog.get_logger("isp.local_secrets")


class LocalSecretsConfig:
    """Configuration for local secrets management."""

    def __init__(self):
        self.secrets_dir = Path(os.getenv("ISP_SECRETS_DIR", "./secrets"))
        self.encrypted_file = self.secrets_dir / "secrets.enc"
        self.key_file = self.secrets_dir / ".key"

        # Ensure secrets directory exists with proper permissions
        self.secrets_dir.mkdir(mode=0o700, exist_ok=True)

    def generate_encryption_key(self) -> bytes:
        """Generate a new encryption key."""
        return Fernet.generate_key()

    def save_key_to_file(self, key: bytes) -> bool:
        """Save encryption key to file with secure permissions."""
        try:
            with open(self.key_file, "wb") as f:
                f.write(key)

            # Set restrictive permissions (owner read/write only)
            os.chmod(self.key_file, 0o600)

            logger.info("Encryption key saved to file", key_file=str(self.key_file))
            return True

        except Exception as e:
            logger.error("Failed to save encryption key", error=str(e))
            return False

    def load_key_from_file(self) -> bytes:
        """Load encryption key from file."""
        try:
            if not self.key_file.exists():
                logger.info("Key file not found, generating new key")
                key = self.generate_encryption_key()
                if self.save_key_to_file(key):
                    return key
                else:
                    raise Exception("Failed to save new key")

            with open(self.key_file, "rb") as f:
                key = f.read()

            logger.info("Encryption key loaded from file")
            return key

        except Exception as e:
            logger.error("Failed to load encryption key", error=str(e))
            raise

    def derive_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        if salt is None:
            salt = b"isp-framework-local-salt"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        logger.info("Encryption key derived from password")
        return key

    def setup_local_secrets(
        self, use_password: bool = False, password: str = None
    ) -> dict:
        """Set up local secrets management."""
        setup_info = {
            "backend": "encrypted_file",
            "secrets_dir": str(self.secrets_dir),
            "encrypted_file": str(self.encrypted_file),
            "key_method": "file" if not use_password else "password",
        }

        try:
            if use_password:
                if not password:
                    password = os.getenv("ISP_MASTER_PASSWORD")
                    if not password:
                        raise ValueError("Password required but not provided")

                key = self.derive_key_from_password(password)
                setup_info["key_source"] = "password_derived"
            else:
                key = self.load_key_from_file()
                setup_info["key_source"] = "file"
                setup_info["key_file"] = str(self.key_file)

            # Set environment variables for secrets manager
            os.environ["SECRETS_BACKEND"] = "encrypted_file"
            os.environ["ENCRYPTED_SECRETS_FILE"] = str(self.encrypted_file)
            os.environ["ISP_SECRETS_KEY"] = base64.urlsafe_b64encode(key).decode()

            setup_info["status"] = "success"
            logger.info("Local secrets setup completed", **setup_info)

        except Exception as e:
            setup_info["status"] = "error"
            setup_info["error"] = str(e)
            logger.error("Local secrets setup failed", error=str(e))

        return setup_info

    def migrate_env_secrets_to_file(self) -> dict:
        """Migrate existing environment secrets to encrypted file."""
        migration_info = {
            "migrated_secrets": [],
            "failed_secrets": [],
            "total_migrated": 0,
        }

        try:
            from app.core.secrets_manager import secrets_manager

            # Common secret environment variables to migrate
            env_secrets = {
                "DATABASE_PASSWORD": "database.password",
                "JWT_SECRET_KEY": "jwt.secret_key",
                "JWT_REFRESH_SECRET": "jwt.refresh_secret",
                "SMTP_PASSWORD": "smtp.password",
                "MINIO_SECRET_KEY": "minio.secret_key",
                "RADIUS_SHARED_SECRET": "radius.shared_secret",
            }

            for env_var, secret_key in env_secrets.items():
                env_value = os.getenv(env_var)
                if env_value:
                    if secrets_manager.set_secret(secret_key, env_value):
                        migration_info["migrated_secrets"].append(
                            {"env_var": env_var, "secret_key": secret_key}
                        )
                        migration_info["total_migrated"] += 1
                        logger.info(f"Migrated {env_var} to encrypted file")
                    else:
                        migration_info["failed_secrets"].append(
                            {
                                "env_var": env_var,
                                "secret_key": secret_key,
                                "error": "Failed to set secret",
                            }
                        )

            migration_info["status"] = "success"

        except Exception as e:
            migration_info["status"] = "error"
            migration_info["error"] = str(e)
            logger.error("Secret migration failed", error=str(e))

        return migration_info

    def validate_setup(self) -> dict:
        """Validate local secrets setup."""
        validation = {
            "secrets_dir_exists": self.secrets_dir.exists(),
            "secrets_dir_permissions": (
                oct(self.secrets_dir.stat().st_mode)[-3:]
                if self.secrets_dir.exists()
                else None
            ),
            "encrypted_file_exists": self.encrypted_file.exists(),
            "key_file_exists": self.key_file.exists(),
            "key_file_permissions": (
                oct(self.key_file.stat().st_mode)[-3:]
                if self.key_file.exists()
                else None
            ),
            "environment_configured": bool(os.getenv("ISP_SECRETS_KEY")),
            "backend_configured": os.getenv("SECRETS_BACKEND") == "encrypted_file",
        }

        # Test encryption/decryption
        try:
            from app.core.secrets_manager import secrets_manager

            test_key = "test.validation.key"
            test_value = "test_validation_value_123"

            # Test set and get
            if secrets_manager.set_secret(test_key, test_value):
                retrieved = secrets_manager.get_secret(test_key)
                validation["encryption_test"] = retrieved == test_value

                # Clean up test secret
                secrets_manager.set_secret(test_key, None)
            else:
                validation["encryption_test"] = False

        except Exception as e:
            validation["encryption_test"] = False
            validation["encryption_error"] = str(e)

        validation["overall_status"] = all(
            [
                validation["secrets_dir_exists"],
                validation["environment_configured"],
                validation["backend_configured"],
                validation.get("encryption_test", False),
            ]
        )

        return validation


def setup_local_secrets_cli():
    """CLI function to set up local secrets."""
    import argparse

    parser = argparse.ArgumentParser(description="Set up local secrets management")
    parser.add_argument(
        "--password", action="store_true", help="Use password-based key derivation"
    )
    parser.add_argument(
        "--migrate", action="store_true", help="Migrate environment secrets to file"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate current setup"
    )

    args = parser.parse_args()

    config = LocalSecretsConfig()

    if args.validate:
        validation = config.validate_setup()
        print("🔍 Local Secrets Validation")
        print("=" * 40)
        for key, value in validation.items():
            status = "✅" if value else "❌"
            print(f"{status} {key}: {value}")

        if validation["overall_status"]:
            print("\n🎉 Local secrets setup is valid!")
        else:
            print("\n⚠️  Local secrets setup has issues")

        return validation["overall_status"]

    if args.migrate:
        migration = config.migrate_env_secrets_to_file()
        print("🔄 Secret Migration Results")
        print("=" * 40)
        print(f"Total migrated: {migration['total_migrated']}")

        if migration["migrated_secrets"]:
            print("\nMigrated secrets:")
            for secret in migration["migrated_secrets"]:
                print(f"  ✅ {secret['env_var']} → {secret['secret_key']}")

        if migration["failed_secrets"]:
            print("\nFailed migrations:")
            for secret in migration["failed_secrets"]:
                print(
                    f"  ❌ {secret['env_var']}: {secret.get('error', 'Unknown error')}"
                )

        return migration["status"] == "success"

    # Default: setup local secrets
    use_password = args.password
    password = None

    if use_password:
        import getpass

        password = getpass.getpass("Enter master password: ")

    setup_info = config.setup_local_secrets(use_password, password)

    print("🔐 Local Secrets Setup")
    print("=" * 40)
    for key, value in setup_info.items():
        print(f"{key}: {value}")

    if setup_info["status"] == "success":
        print("\n🎉 Local secrets setup completed successfully!")
        print("\nNext steps:")
        print("1. Run with --migrate to migrate existing environment secrets")
        print("2. Run with --validate to verify the setup")
        print("3. Start your application - it will use encrypted file storage")
    else:
        print(f"\n❌ Setup failed: {setup_info.get('error', 'Unknown error')}")

    return setup_info["status"] == "success"


if __name__ == "__main__":
    setup_local_secrets_cli()
