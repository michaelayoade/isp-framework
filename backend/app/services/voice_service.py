"""Voice Service Management Service Layer."""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.services.instances import CustomerVoiceService as VoiceService
from app.schemas.voice_services import (
    VoiceServiceCreate, VoiceServiceUpdate, VoiceServiceProvisioningRequest
)
from app.core.exceptions import NotFoundError, ValidationError
from app.services.webhook_integration_service import WebhookTriggers

logger = logging.getLogger(__name__)


class VoiceServiceService:
    """Service layer for voice service management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.webhook_triggers = WebhookTriggers(db)
    
    def create_voice_service(self, customer_id: int, service_data: VoiceServiceCreate) -> VoiceService:
        """Create a new voice service for a customer."""
        try:
            # Validate customer exists
            from app.models.customer import Customer
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")
            
            # Create voice service
            voice_service_dict = service_data.dict()
            voice_service_dict['customer_id'] = customer_id
            voice_service_dict['status'] = 'pending_activation'
            
            voice_service = VoiceService(**voice_service_dict)
            self.db.add(voice_service)
            self.db.commit()
            self.db.refresh(voice_service)
            
            # Trigger webhook
            self.webhook_triggers.service_created({
                'service_id': voice_service.id,
                'customer_id': customer_id,
                'service_type': 'voice',
                'plan_id': voice_service.plan_id,
                'monthly_fee': float(voice_service.monthly_fee) if voice_service.monthly_fee else 0
            })
            
            logger.info(f"Created voice service {voice_service.id} for customer {customer_id}")
            return voice_service
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating voice service for customer {customer_id}: {e}")
            raise
    
    def get_voice_service(self, service_id: int) -> Optional[VoiceService]:
        """Get voice service by ID."""
        return self.db.query(VoiceService).filter(VoiceService.id == service_id).first()
    
    def get_customer_voice_services(self, customer_id: int) -> List[VoiceService]:
        """Get all voice services for a customer."""
        return self.db.query(VoiceService).filter(
            VoiceService.customer_id == customer_id
        ).all()
    
    def update_voice_service(self, service_id: int, update_data: VoiceServiceUpdate) -> Optional[VoiceService]:
        """Update voice service."""
        try:
            voice_service = self.get_voice_service(service_id)
            if not voice_service:
                raise NotFoundError(f"Voice service with ID {service_id} not found")
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(voice_service, key, value)
            
            self.db.commit()
            self.db.refresh(voice_service)
            
            # Trigger webhook
            self.webhook_triggers.service_updated({
                'service_id': voice_service.id,
                'customer_id': voice_service.customer_id,
                'service_type': 'voice',
                'changes': list(update_dict.keys())
            })
            
            logger.info(f"Updated voice service {service_id}")
            return voice_service
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating voice service {service_id}: {e}")
            raise
    
    def delete_voice_service(self, service_id: int) -> bool:
        """Delete voice service."""
        try:
            voice_service = self.get_voice_service(service_id)
            if not voice_service:
                raise NotFoundError(f"Voice service with ID {service_id} not found")
            
            customer_id = voice_service.customer_id
            
            self.db.delete(voice_service)
            self.db.commit()
            
            # Trigger webhook
            self.webhook_triggers.service_deleted({
                'service_id': service_id,
                'customer_id': customer_id,
                'service_type': 'voice'
            })
            
            logger.info(f"Deleted voice service {service_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting voice service {service_id}: {e}")
            raise
    
    def provision_voice_service(self, service_id: int, provisioning_data: VoiceServiceProvisioningRequest) -> Dict[str, Any]:
        """Provision voice service with telephony configuration."""
        try:
            voice_service = self.get_voice_service(service_id)
            if not voice_service:
                raise NotFoundError(f"Voice service with ID {service_id} not found")
            
            if voice_service.status != 'pending_activation':
                raise ValidationError(f"Voice service {service_id} is not in pending_activation status")
            
            # Simulate provisioning logic
            provisioning_result = {
                'service_id': service_id,
                'phone_number': provisioning_data.phone_number,
                'sip_username': f"user_{service_id}",
                'sip_password': f"pass_{service_id}",
                'sip_domain': 'voice.ispframework.com',
                'status': 'provisioned'
            }
            
            # Update service status
            voice_service.status = 'active'
            voice_service.phone_number = provisioning_data.phone_number
            self.db.commit()
            
            # Trigger webhook
            self.webhook_triggers.service_provisioned({
                'service_id': service_id,
                'customer_id': voice_service.customer_id,
                'service_type': 'voice',
                'provisioning_data': provisioning_result
            })
            
            logger.info(f"Provisioned voice service {service_id}")
            return provisioning_result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error provisioning voice service {service_id}: {e}")
            raise
    
    def suspend_voice_service(self, service_id: int, reason: str = None) -> VoiceService:
        """Suspend voice service."""
        try:
            voice_service = self.get_voice_service(service_id)
            if not voice_service:
                raise NotFoundError(f"Voice service with ID {service_id} not found")
            
            voice_service.status = 'suspended'
            if reason:
                voice_service.suspension_reason = reason
            
            self.db.commit()
            self.db.refresh(voice_service)
            
            # Trigger webhook
            self.webhook_triggers.service_suspended({
                'service_id': service_id,
                'customer_id': voice_service.customer_id,
                'service_type': 'voice',
                'reason': reason
            })
            
            logger.info(f"Suspended voice service {service_id}")
            return voice_service
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error suspending voice service {service_id}: {e}")
            raise
    
    def reactivate_voice_service(self, service_id: int) -> VoiceService:
        """Reactivate suspended voice service."""
        try:
            voice_service = self.get_voice_service(service_id)
            if not voice_service:
                raise NotFoundError(f"Voice service with ID {service_id} not found")
            
            if voice_service.status != 'suspended':
                raise ValidationError(f"Voice service {service_id} is not suspended")
            
            voice_service.status = 'active'
            voice_service.suspension_reason = None
            
            self.db.commit()
            self.db.refresh(voice_service)
            
            # Trigger webhook
            self.webhook_triggers.service_reactivated({
                'service_id': service_id,
                'customer_id': voice_service.customer_id,
                'service_type': 'voice'
            })
            
            logger.info(f"Reactivated voice service {service_id}")
            return voice_service
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reactivating voice service {service_id}: {e}")
            raise
    
    def get_voice_service_statistics(self, customer_id: int = None) -> Dict[str, Any]:
        """Get voice service statistics."""
        try:
            query = self.db.query(VoiceService)
            
            if customer_id:
                query = query.filter(VoiceService.customer_id == customer_id)
            
            total_services = query.count()
            active_services = query.filter(VoiceService.status == 'active').count()
            suspended_services = query.filter(VoiceService.status == 'suspended').count()
            pending_services = query.filter(VoiceService.status == 'pending_activation').count()
            
            return {
                'total_services': total_services,
                'active_services': active_services,
                'suspended_services': suspended_services,
                'pending_services': pending_services,
                'activation_rate': (active_services / total_services * 100) if total_services > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting voice service statistics: {e}")
            raise
