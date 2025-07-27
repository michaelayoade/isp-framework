"""
Portal ID Service

Service for managing portal ID generation, validation, and configuration
according to the ISP Framework portal ID system.
"""

import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.customer.portal import PortalConfig, PortalIDHistory
from app.repositories.base import BaseRepository
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class PortalIDService:
    """Service for portal ID management and generation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.portal_config_repo = BaseRepository(PortalConfig, db)
        self.portal_history_repo = BaseRepository(PortalIDHistory, db)
    
    def generate_portal_id(self, customer_id: int, partner_id: Optional[int] = None, service_type: str = "internet") -> str:
        """
        Generate portal ID for a customer using configured prefix
        Format: [PREFIX][CUSTOMER_ID]
        Example: Customer ID 4 with prefix "1000" -> Portal ID "10004"
        """
        try:
            # Get portal configuration
            prefix = self.get_portal_prefix(partner_id, service_type)
            
            # Generate portal ID
            portal_id = f"{prefix}{customer_id}"
            
            logger.info(f"Generated portal ID {portal_id} for customer {customer_id}")
            return portal_id
            
        except Exception as e:
            logger.error(f"Error generating portal ID for customer {customer_id}: {e}")
            # Fallback to default prefix
            return f"1000{customer_id}"
    
    def extract_customer_id_from_portal_id(self, portal_id: str) -> Optional[int]:
        """
        Extract customer ID from portal ID by removing the prefix
        """
        try:
            # Get all possible prefixes to try
            configs = self.portal_config_repo.get_all()
            
            for config in configs:
                if portal_id.startswith(config.prefix):
                    customer_id_str = portal_id[len(config.prefix):]
                    try:
                        customer_id = int(customer_id_str)
                        logger.debug(f"Extracted customer ID {customer_id} from portal ID {portal_id}")
                        return customer_id
                    except ValueError:
                        continue
            
            # Try default prefix "1000" as fallback
            if portal_id.startswith("1000"):
                customer_id_str = portal_id[4:]  # Remove "1000" prefix
                try:
                    customer_id = int(customer_id_str)
                    logger.debug(f"Extracted customer ID {customer_id} from portal ID {portal_id} using default prefix")
                    return customer_id
                except ValueError:
                    pass
            
            logger.warning(f"Could not extract customer ID from portal ID: {portal_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting customer ID from portal ID {portal_id}: {e}")
            return None
    
    def get_portal_prefix(self, partner_id: Optional[int] = None, service_type: str = "internet") -> str:
        """
        Get portal prefix for a partner and service type
        """
        try:
            # Try to find specific configuration
            filters = {
                "service_type": service_type,
                "is_active": True
            }
            
            if partner_id:
                filters["partner_id"] = partner_id
            
            configs = self.portal_config_repo.get_all(filters=filters)
            
            # Find the best match
            for config in configs:
                if partner_id and config.partner_id == partner_id:
                    return config.prefix
                elif config.is_default:
                    return config.prefix
            
            # If no specific config found, try default
            default_configs = self.portal_config_repo.get_all(filters={
                "is_default": True,
                "is_active": True
            })
            
            if default_configs:
                return default_configs[0].prefix
            
            # Ultimate fallback
            logger.warning(f"No portal config found for partner {partner_id}, service {service_type}. Using default prefix.")
            return "1000"
            
        except Exception as e:
            logger.error(f"Error getting portal prefix: {e}")
            return "1000"
    
    def validate_portal_id_format(self, portal_id: str) -> bool:
        """
        Validate portal ID format
        """
        try:
            if not portal_id or len(portal_id) < 5:  # Minimum: prefix + customer ID
                return False
            
            # Check if we can extract a valid customer ID
            customer_id = self.extract_customer_id_from_portal_id(portal_id)
            return customer_id is not None and customer_id > 0
            
        except Exception as e:
            logger.error(f"Error validating portal ID format {portal_id}: {e}")
            return False
    
    def is_portal_id_available(self, portal_id: str) -> bool:
        """
        Check if portal ID is available (not in use)
        This would typically check against the customer database
        """
        try:
            customer_id = self.extract_customer_id_from_portal_id(portal_id)
            if not customer_id:
                return False
            
            # In a real implementation, we would check if this customer_id exists
            # For now, we'll assume it's available if we can extract a valid ID
            return True
            
        except Exception as e:
            logger.error(f"Error checking portal ID availability {portal_id}: {e}")
            return False
    
    def create_portal_config(self, partner_id: Optional[int], prefix: str, service_type: str = "internet", 
                           is_default: bool = False, description: Optional[str] = None) -> PortalConfig:
        """
        Create a new portal configuration
        """
        try:
            config_data = {
                "partner_id": partner_id,
                "prefix": prefix,
                "service_type": service_type,
                "is_default": is_default,
                "description": description,
                "is_active": True
            }
            
            config = self.portal_config_repo.create(config_data)
            logger.info(f"Created portal config: partner={partner_id}, prefix={prefix}, service={service_type}")
            return config
            
        except Exception as e:
            logger.error(f"Error creating portal config: {e}")
            raise
    
    def get_portal_configs(self, partner_id: Optional[int] = None, service_type: Optional[str] = None) -> List[PortalConfig]:
        """
        Get portal configurations with optional filtering
        """
        try:
            filters = {"is_active": True}
            
            if partner_id:
                filters["partner_id"] = partner_id
            if service_type:
                filters["service_type"] = service_type
            
            return self.portal_config_repo.get_all(filters=filters)
            
        except Exception as e:
            logger.error(f"Error getting portal configs: {e}")
            return []
    
    def log_portal_id_change(self, old_portal_id: Optional[str], new_portal_id: str, 
                           changed_by: Optional[int] = None, reason: Optional[str] = None) -> PortalIDHistory:
        """
        Log portal ID change for auditing
        """
        try:
            history_data = {
                "old_portal_id": old_portal_id,
                "new_portal_id": new_portal_id,
                "changed_by": changed_by,
                "change_reason": reason
            }
            
            history = self.portal_history_repo.create(history_data)
            logger.info(f"Logged portal ID change: {old_portal_id} -> {new_portal_id}")
            return history
            
        except Exception as e:
            logger.error(f"Error logging portal ID change: {e}")
            raise
