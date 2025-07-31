"""
Portal ID Generation and Management Utilities

This module provides utilities for generating and managing portal IDs
for customer authentication in PPPoE/RADIUS and customer portal systems.

Portal ID Format: [PREFIX][CUSTOMER_ID]
Example: Customer ID 3456 with prefix "1000" → Portal ID "10003456"
"""

import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationError


class PortalIDGenerator:
    """Portal ID generation and validation utilities"""

    # Default configuration
    DEFAULT_PREFIX = "1000"
    MIN_CUSTOMER_ID = 1
    MAX_CUSTOMER_ID = 999999999  # 9 digits max

    # Portal ID validation pattern
    PORTAL_ID_PATTERN = re.compile(r"^[A-Z0-9]{1,20}\d{1,9}$")

    @classmethod
    def generate_portal_id(cls, customer_id: int, prefix: Optional[str] = None) -> str:
        """
        Generate portal ID from customer ID and prefix.

        Args:
            customer_id: The customer's database ID
            prefix: Portal ID prefix (defaults to DEFAULT_PREFIX)

        Returns:
            Generated portal ID string

        Raises:
            ValidationError: If customer_id is invalid or portal ID would be malformed
        """
        if not isinstance(customer_id, int) or customer_id < cls.MIN_CUSTOMER_ID:
            raise ValidationError(
                f"Customer ID must be a positive integer >= {cls.MIN_CUSTOMER_ID}"
            )

        if customer_id > cls.MAX_CUSTOMER_ID:
            raise ValidationError(f"Customer ID must be <= {cls.MAX_CUSTOMER_ID}")

        if prefix is None:
            prefix = cls.DEFAULT_PREFIX

        # Validate prefix
        if not prefix or not isinstance(prefix, str):
            raise ValidationError("Portal ID prefix must be a non-empty string")

        if len(prefix) > 20:
            raise ValidationError("Portal ID prefix must be <= 20 characters")

        if not re.match(r"^[A-Z0-9]+$", prefix):
            raise ValidationError(
                "Portal ID prefix must contain only uppercase letters and numbers"
            )

        portal_id = f"{prefix}{customer_id}"

        # Final validation
        if not cls.validate_portal_id_format(portal_id):
            raise ValidationError(
                f"Generated portal ID '{portal_id}' has invalid format"
            )

        return portal_id

    @classmethod
    def validate_portal_id_format(cls, portal_id: str) -> bool:
        """
        Validate portal ID format.

        Args:
            portal_id: Portal ID to validate

        Returns:
            True if format is valid, False otherwise
        """
        if not isinstance(portal_id, str):
            return False

        return bool(cls.PORTAL_ID_PATTERN.match(portal_id))

    @classmethod
    def extract_customer_id(cls, portal_id: str, prefix: str) -> Optional[int]:
        """
        Extract customer ID from portal ID given the prefix.

        Args:
            portal_id: Portal ID to parse
            prefix: Expected prefix

        Returns:
            Customer ID if extraction successful, None otherwise
        """
        if not cls.validate_portal_id_format(portal_id):
            return None

        if not portal_id.startswith(prefix):
            return None

        try:
            customer_id_str = portal_id[len(prefix) :]
            customer_id = int(customer_id_str)

            if customer_id < cls.MIN_CUSTOMER_ID or customer_id > cls.MAX_CUSTOMER_ID:
                return None

            return customer_id
        except (ValueError, IndexError):
            return None

    @classmethod
    def get_default_prefix(cls) -> str:
        """Get the default portal ID prefix from configuration."""
        return getattr(settings, "default_portal_prefix", cls.DEFAULT_PREFIX)


class PortalIDService:
    """Service for managing portal ID configuration and operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_portal_config(
        self, partner_id: int = 1, service_type: str = "internet"
    ) -> Dict[str, Any]:
        """
        Get portal configuration for a partner and service type.

        Args:
            partner_id: Partner ID (defaults to 1)
            service_type: Service type (defaults to "internet")

        Returns:
            Portal configuration dictionary
        """
        from app.models.portal_config import PortalConfig

        # Try to get specific config for partner and service type
        config = (
            self.db.query(PortalConfig)
            .filter(
                PortalConfig.partner_id == partner_id,
                PortalConfig.service_type == service_type,
                PortalConfig.is_active is True,
            )
            .first()
        )

        # If not found, try to get default config for partner
        if not config:
            config = (
                self.db.query(PortalConfig)
                .filter(
                    PortalConfig.partner_id == partner_id,
                    PortalConfig.is_default is True,
                    PortalConfig.is_active is True,
                )
                .first()
            )

        # If still not found, get any default config
        if not config:
            config = (
                self.db.query(PortalConfig)
                .filter(PortalConfig.is_default is True, PortalConfig.is_active is True)
                .first()
            )

        # Fallback to hardcoded default if no config in database
        if not config:
            return {
                "partner_id": partner_id,
                "prefix": PortalIDGenerator.get_default_prefix(),
                "description": f"Fallback default portal prefix for partner {partner_id}",
                "service_type": service_type,
                "is_default": True,
                "is_active": True,
            }

        return {
            "id": config.id,
            "partner_id": config.partner_id,
            "prefix": config.prefix,
            "description": config.description,
            "service_type": config.service_type,
            "is_default": config.is_default,
            "is_active": config.is_active,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }

    def generate_customer_portal_id(
        self, customer_id: int, partner_id: int = 1, service_type: str = "internet"
    ) -> str:
        """
        Generate portal ID for a customer using partner configuration.

        Args:
            customer_id: Customer's database ID
            partner_id: Partner ID
            service_type: Service type

        Returns:
            Generated portal ID
        """
        config = self.get_portal_config(partner_id, service_type)
        return PortalIDGenerator.generate_portal_id(customer_id, config["prefix"])

    def validate_portal_id_uniqueness(
        self, portal_id: str, exclude_customer_id: Optional[int] = None
    ) -> bool:
        """
        Check if portal ID is unique across all customers.

        Args:
            portal_id: Portal ID to check
            exclude_customer_id: Customer ID to exclude from check (for updates)

        Returns:
            True if unique, False if already exists
        """
        from app.models.base import Customer

        query = self.db.query(Customer).filter(Customer.login == portal_id)

        if exclude_customer_id:
            query = query.filter(Customer.id != exclude_customer_id)

        return query.first() is None

    def update_customer_portal_id(
        self, customer_id: int, new_portal_id: Optional[str] = None
    ) -> str:
        """
        Update customer's portal ID, generating new one if not provided.

        Args:
            customer_id: Customer ID to update
            new_portal_id: New portal ID (auto-generated if None)

        Returns:
            The assigned portal ID

        Raises:
            ValidationError: If portal ID is invalid or not unique
        """
        from app.models.base import Customer

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValidationError(f"Customer with ID {customer_id} not found")

        if new_portal_id is None:
            new_portal_id = self.generate_customer_portal_id(
                customer_id, customer.partner_id
            )
        else:
            if not PortalIDGenerator.validate_portal_id_format(new_portal_id):
                raise ValidationError(f"Invalid portal ID format: {new_portal_id}")

        if not self.validate_portal_id_uniqueness(new_portal_id, customer_id):
            raise ValidationError(f"Portal ID '{new_portal_id}' is already in use")

        # Store old portal ID for audit
        old_portal_id = customer.login

        # Update customer
        customer.login = new_portal_id

        # Log portal ID change for audit
        self._log_portal_id_change(
            customer_id=customer_id,
            old_portal_id=old_portal_id,
            new_portal_id=new_portal_id,
            changed_by=None,  # Will be set by calling service
            change_reason="Portal ID update requested",
        )

        self.db.commit()

        return new_portal_id

    def _log_portal_id_change(
        self,
        customer_id: int,
        old_portal_id: str,
        new_portal_id: str,
        changed_by: Optional[int] = None,
        change_reason: str = None,
    ):
        """Log portal ID change to history table"""
        from app.models.portal_config import PortalIDHistory

        history_entry = PortalIDHistory(
            customer_id=customer_id,
            old_portal_id=old_portal_id,
            new_portal_id=new_portal_id,
            changed_by=changed_by,
            change_reason=change_reason,
        )

        self.db.add(history_entry)
        # Note: commit is handled by calling method

    def get_all_portal_configs(self) -> List[Dict[str, Any]]:
        """Get all portal configurations"""
        from app.models.portal_config import PortalConfig

        configs = (
            self.db.query(PortalConfig).filter(PortalConfig.is_active is True).all()
        )

        return [
            {
                "id": config.id,
                "partner_id": config.partner_id,
                "prefix": config.prefix,
                "description": config.description,
                "service_type": config.service_type,
                "is_default": config.is_default,
                "is_active": config.is_active,
                "created_at": config.created_at,
                "updated_at": config.updated_at,
            }
            for config in configs
        ]

    def create_portal_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new portal configuration"""
        from app.models.portal_config import PortalConfig

        # Validate prefix format
        prefix = config_data.get("prefix")
        if not prefix or not PortalIDGenerator.validate_portal_id_format(f"{prefix}1"):
            raise ValidationError(f"Invalid prefix format: {prefix}")

        # Check if prefix already exists for this partner
        existing = (
            self.db.query(PortalConfig)
            .filter(
                PortalConfig.partner_id == config_data.get("partner_id", 1),
                PortalConfig.prefix == prefix,
                PortalConfig.is_active is True,
            )
            .first()
        )

        if existing:
            raise ValidationError(
                f"Prefix '{prefix}' already exists for partner {config_data.get('partner_id', 1)}"
            )

        # If this is set as default, unset other defaults for this partner
        if config_data.get("is_default", False):
            self.db.query(PortalConfig).filter(
                PortalConfig.partner_id == config_data.get("partner_id", 1),
                PortalConfig.is_default is True,
            ).update({"is_default": False})

        config = PortalConfig(**config_data)
        self.db.add(config)
        self.db.commit()

        return {
            "id": config.id,
            "partner_id": config.partner_id,
            "prefix": config.prefix,
            "description": config.description,
            "service_type": config.service_type,
            "is_default": config.is_default,
            "is_active": config.is_active,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }

    def update_portal_config(
        self, config_id: int, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update portal configuration"""
        from app.models.portal_config import PortalConfig

        config = (
            self.db.query(PortalConfig).filter(PortalConfig.id == config_id).first()
        )
        if not config:
            raise ValidationError(f"Portal configuration with ID {config_id} not found")

        # Validate prefix if being updated
        if "prefix" in update_data:
            prefix = update_data["prefix"]
            if not prefix or not PortalIDGenerator.validate_portal_id_format(
                f"{prefix}1"
            ):
                raise ValidationError(f"Invalid prefix format: {prefix}")

        # If setting as default, unset other defaults for this partner
        if update_data.get("is_default", False):
            self.db.query(PortalConfig).filter(
                PortalConfig.partner_id == config.partner_id,
                PortalConfig.id != config_id,
                PortalConfig.is_default is True,
            ).update({"is_default": False})

        # Update config
        for key, value in update_data.items():
            setattr(config, key, value)

        self.db.commit()

        return {
            "id": config.id,
            "partner_id": config.partner_id,
            "prefix": config.prefix,
            "description": config.description,
            "service_type": config.service_type,
            "is_default": config.is_default,
            "is_active": config.is_active,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }

    def get_portal_id_history(
        self, customer_id: Optional[int] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get portal ID change history"""
        from app.models.portal_config import PortalIDHistory

        query = self.db.query(PortalIDHistory)

        if customer_id:
            query = query.filter(PortalIDHistory.customer_id == customer_id)

        history = query.order_by(PortalIDHistory.changed_at.desc()).limit(limit).all()

        return [
            {
                "id": entry.id,
                "customer_id": entry.customer_id,
                "old_portal_id": entry.old_portal_id,
                "new_portal_id": entry.new_portal_id,
                "changed_by": entry.changed_by,
                "change_reason": entry.change_reason,
                "changed_at": entry.changed_at,
            }
            for entry in history
        ]
