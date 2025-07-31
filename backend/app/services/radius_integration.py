#!/usr/bin/env python3
"""
RADIUS & Service Integration Module

This module provides comprehensive integration between RADIUS authentication,
service plan enforcement, and ISP operational workflows.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.customer import Customer
from app.models.services import ServiceTemplate as ServicePlan, CustomerService
from app.models.services import CustomerInternetService as InternetService, CustomerVoiceService as VoiceService
from ..models.networking.radius import RadiusSession, CustomerOnline, CustomerStatistics
from ..models.networking.ipam import IPAllocation
from ..models.networking.routers import Router

# Create aliases for backward compatibility
IPv4IP = IPAllocation
IPv6IP = IPAllocation

from ..repositories.base import BaseRepository
from ..repositories.service_plan import ServicePlanRepository
from ..services.customer import CustomerService as CustomerServiceClass

logger = logging.getLogger(__name__)


class RadiusServiceIntegration:
    """
    Comprehensive RADIUS and Service Integration Service
    
    This service handles:
    - RADIUS authentication with service plan validation
    - Service plan enforcement and bandwidth control
    - Real-time session management and monitoring
    - IP address assignment and management
    - Usage tracking and billing integration
    - Automated service provisioning
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.customer_service = CustomerServiceClass(db)
        self.service_plan_repo = ServicePlanRepository(db)
        
        # Initialize repositories for integration
        self.radius_session_repo = BaseRepository(RadiusSession, db)
        self.customer_online_repo = BaseRepository(CustomerOnline, db)
        self.customer_stats_repo = BaseRepository(CustomerStatistics, db)
        self.ipv4_repo = BaseRepository(IPv4IP, db)
        self.ipv6_repo = BaseRepository(IPv6IP, db)
        self.router_repo = BaseRepository(Router, db)
    
    def authenticate_customer(self, portal_id: str, password: str, nas_ip: str = None) -> Dict[str, Any]:
        """
        Authenticate customer via portal ID and validate service plan
        
        Returns authentication result with service plan attributes for RADIUS
        """
        try:
            logger.info(f"Authenticating customer with portal ID: {portal_id}")
            
            # Use comprehensive customer service for authentication
            customer = self.customer_service.authenticate_by_portal_id(portal_id, password)
            
            if not customer:
                logger.warning(f"Authentication failed for portal ID: {portal_id}")
                return {
                    "authenticated": False,
                    "reason": "Invalid portal ID or password"
                }
            
            # Check customer status (allow 'active' and 'new' for RADIUS)
            if customer.status not in ["active", "new"]:
                logger.warning(f"Customer account inactive for portal ID: {portal_id}")
                return {
                    "authenticated": False,
                    "reason": f"Account status: {customer.status}"
                }
            
            # Get active service plan for customer
            service_plan = self._get_active_service_plan(customer.id)
            if not service_plan:
                logger.warning(f"No active service plan for customer: {customer.id}")
                return {
                    "authenticated": False,
                    "reason": "No active service plan"
                }
            
            # Get service plan attributes for RADIUS
            radius_attributes = self._get_radius_attributes(service_plan, customer)
            
            # Log successful authentication
            logger.info(f"Authentication successful for portal ID: {portal_id}, customer: {customer.id}")
            
            return {
                "authenticated": True,
                "customer_id": customer.id,
                "portal_id": portal_id,
                "service_plan_id": service_plan.id,
                "radius_attributes": radius_attributes,
                "customer_info": {
                    "name": customer.name,
                    "email": customer.email,
                    "status": customer.status
                }
            }
            
        except Exception as e:
            logger.error(f"Error during authentication for portal ID {portal_id}: {str(e)}")
            return {
                "authenticated": False,
                "reason": "Authentication system error"
            }
    
    def start_session(self, auth_result: Dict[str, Any], session_data: Dict[str, Any]) -> Optional[RadiusSession]:
        """
        Start a new RADIUS session with service plan enforcement
        """
        try:
            if not auth_result.get("authenticated"):
                logger.warning("Cannot start session for unauthenticated user")
                return None
            
            customer_id = auth_result["customer_id"]
            service_plan_id = auth_result["service_plan_id"]
            
            # Assign IP address
            assigned_ip = self._assign_ip_address(customer_id, service_plan_id)
            
            # Create RADIUS session
            session = RadiusSession(
                customer_id=customer_id,
                service_plan_id=service_plan_id,
                portal_id=auth_result["portal_id"],
                session_id=session_data.get("session_id"),
                nas_ip_address=session_data.get("nas_ip"),
                nas_port=session_data.get("nas_port"),
                framed_ip_address=assigned_ip,
                start_time=datetime.now(timezone.utc),
                status="active",
                bytes_in=0,
                bytes_out=0,
                packets_in=0,
                packets_out=0
            )
            
            session = self.radius_session_repo.create(session.__dict__)
            
            # Update customer online status
            self._update_customer_online_status(customer_id, session.id, "online")
            
            # Log session start
            logger.info(f"RADIUS session started for customer {customer_id}, session ID: {session.id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Error starting RADIUS session: {str(e)}")
            return None
    
    def stop_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Stop a RADIUS session and update usage statistics
        """
        try:
            # Find active session
            session = self.radius_session_repo.get_all(
                filters={"session_id": session_id, "status": "active"}
            )
            
            if not session:
                logger.warning(f"Active session not found: {session_id}")
                return False
            
            session = session[0]  # Get first result
            
            # Update session with final statistics
            session.end_time = datetime.now(timezone.utc)
            session.status = "stopped"
            session.bytes_in = session_data.get("bytes_in", session.bytes_in)
            session.bytes_out = session_data.get("bytes_out", session.bytes_out)
            session.packets_in = session_data.get("packets_in", session.packets_in)
            session.packets_out = session_data.get("packets_out", session.packets_out)
            session.termination_cause = session_data.get("termination_cause", "User-Request")
            
            # Calculate session duration
            if session.start_time and session.end_time:
                duration = session.end_time - session.start_time
                session.session_duration = int(duration.total_seconds())
            
            # Update session in database
            self.db.merge(session)
            self.db.commit()
            
            # Update customer online status
            self._update_customer_online_status(session.customer_id, session.id, "offline")
            
            # Update customer statistics
            self._update_customer_statistics(session)
            
            # Release IP address
            if session.framed_ip_address:
                self._release_ip_address(session.framed_ip_address)
            
            logger.info(f"RADIUS session stopped for customer {session.customer_id}, session ID: {session.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping RADIUS session {session_id}: {str(e)}")
            return False
    
    def update_session_accounting(self, session_id: str, accounting_data: Dict[str, Any]) -> bool:
        """
        Update session accounting data (interim updates)
        """
        try:
            # Find active session
            session = self.radius_session_repo.get_all(
                filters={"session_id": session_id, "status": "active"}
            )
            
            if not session:
                logger.warning(f"Active session not found for accounting update: {session_id}")
                return False
            
            session = session[0]  # Get first result
            
            # Update accounting data
            session.bytes_in = accounting_data.get("bytes_in", session.bytes_in)
            session.bytes_out = accounting_data.get("bytes_out", session.bytes_out)
            session.packets_in = accounting_data.get("packets_in", session.packets_in)
            session.packets_out = accounting_data.get("packets_out", session.packets_out)
            session.last_update = datetime.now(timezone.utc)
            
            # Update session in database
            self.db.merge(session)
            self.db.commit()
            
            # Check for usage limits and enforcement
            self._check_usage_limits(session)
            
            logger.debug(f"Accounting updated for session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating accounting for session {session_id}: {str(e)}")
            return False
    
    def get_customer_sessions(self, customer_id: int, active_only: bool = False) -> List[RadiusSession]:
        """
        Get all sessions for a customer
        """
        try:
            filters = {"customer_id": customer_id}
            if active_only:
                filters["status"] = "active"
            
            sessions = self.radius_session_repo.get_all(
                filters=filters,
                order_by="start_time",
                order_desc=True
            )
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting sessions for customer {customer_id}: {str(e)}")
            return []
    
    def get_service_plan_enforcement_attributes(self, service_plan_id: int) -> Dict[str, Any]:
        """
        Get RADIUS attributes for service plan enforcement
        """
        try:
            service_plan = self.service_plan_repo.get(service_plan_id)
            if not service_plan:
                return {}
            
            return self._get_radius_attributes(service_plan, None)
            
        except Exception as e:
            logger.error(f"Error getting enforcement attributes for service plan {service_plan_id}: {str(e)}")
            return {}
    
    # Private helper methods
    

    
    def _get_active_service_plan(self, customer_id: int) -> Optional[ServicePlan]:
        """
        Get the active service plan for a customer
        """
        try:
            # Get active customer service assignment
            customer_service = self.db.query(CustomerService).filter(
                and_(
                    CustomerService.customer_id == customer_id,
                    CustomerService.status == "active"
                )
            ).first()
            
            if not customer_service:
                return None
            
            # Get the service plan
            service_plan = self.service_plan_repo.get(customer_service.service_plan_id)
            return service_plan
            
        except Exception as e:
            logger.error(f"Error getting active service plan for customer {customer_id}: {str(e)}")
            return None
    
    def _get_radius_attributes(self, service_plan: ServicePlan, customer: Optional[Customer]) -> Dict[str, Any]:
        """
        Generate RADIUS attributes based on service plan
        """
        attributes = {}
        
        try:
            # Basic service plan attributes
            if service_plan.service_type == "internet":
                # Get internet service details if available
                internet_service = self.db.query(InternetService).filter(
                    InternetService.service_plan_id == service_plan.id
                ).first()
                
                if internet_service:
                    # Bandwidth attributes (in bits per second)
                    if internet_service.download_speed:
                        attributes["WISPr-Bandwidth-Max-Down"] = internet_service.download_speed * 1000  # Convert Kbps to bps
                    
                    if internet_service.upload_speed:
                        attributes["WISPr-Bandwidth-Max-Up"] = internet_service.upload_speed * 1000  # Convert Kbps to bps
                    
                    # Data limit attributes
                    if internet_service.data_limit:
                        attributes["ChilliSpot-Max-Total-Octets"] = internet_service.data_limit * 1024 * 1024  # Convert MB to bytes
                
                # Fallback to service plan basic attributes
                else:
                    # Use basic service plan attributes if no detailed internet service
                    attributes["Session-Timeout"] = 86400  # 24 hours default
                    attributes["Idle-Timeout"] = 1800  # 30 minutes idle timeout
            
            # Voice service attributes
            elif service_plan.service_type == "voice":
                voice_service = self.db.query(VoiceService).filter(
                    VoiceService.service_plan_id == service_plan.id
                ).first()
                
                if voice_service:
                    attributes["Voice-Service-Enabled"] = "1"
                    if voice_service.concurrent_calls:
                        attributes["Voice-Max-Concurrent-Calls"] = voice_service.concurrent_calls
            
            # Common attributes
            attributes["Service-Type"] = "Framed-User"
            attributes["Framed-Protocol"] = "PPP"
            
            # Add service plan identification
            attributes["ISP-Service-Plan-ID"] = service_plan.id
            attributes["ISP-Service-Plan-Name"] = service_plan.name
            
            # Customer-specific attributes
            if customer:
                attributes["ISP-Customer-ID"] = customer.id
                attributes["ISP-Customer-Name"] = customer.name
            
            logger.debug(f"Generated RADIUS attributes for service plan {service_plan.id}: {attributes}")
            
        except Exception as e:
            logger.error(f"Error generating RADIUS attributes: {str(e)}")
        
        return attributes
    
    def _assign_ip_address(self, customer_id: int, service_plan_id: int) -> Optional[str]:
        """
        Assign an IP address to a customer session
        """
        try:
            # Find available IPv4 address
            available_ip = self.db.query(IPv4IP).filter(
                and_(
                    IPv4IP.status == "available",
                    IPv4IP.ip_address.isnot(None)
                )
            ).first()
            
            if available_ip:
                # Assign IP to customer
                available_ip.status = "assigned"
                available_ip.customer_id = customer_id
                available_ip.assigned_at = datetime.now(timezone.utc)
                
                self.db.merge(available_ip)
                self.db.commit()
                
                logger.info(f"Assigned IP {available_ip.ip_address} to customer {customer_id}")
                return available_ip.ip_address
            
            logger.warning(f"No available IP addresses for customer {customer_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error assigning IP address to customer {customer_id}: {str(e)}")
            return None
    
    def _release_ip_address(self, ip_address: str) -> bool:
        """
        Release an IP address back to the pool
        """
        try:
            ip_record = self.db.query(IPv4IP).filter(
                IPv4IP.ip_address == ip_address
            ).first()
            
            if ip_record:
                ip_record.status = "available"
                ip_record.customer_id = None
                ip_record.assigned_at = None
                
                self.db.merge(ip_record)
                self.db.commit()
                
                logger.info(f"Released IP address {ip_address}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error releasing IP address {ip_address}: {str(e)}")
            return False
    
    def _update_customer_online_status(self, customer_id: int, session_id: int, status: str) -> None:
        """
        Update customer online status
        """
        try:
            # Check if customer online record exists
            online_record = self.db.query(CustomerOnline).filter(
                CustomerOnline.customer_id == customer_id
            ).first()
            
            if status == "online":
                if online_record:
                    # Update existing record
                    online_record.session_id = session_id
                    online_record.last_seen = datetime.now(timezone.utc)
                    online_record.status = "online"
                else:
                    # Create new record
                    online_record = CustomerOnline(
                        customer_id=customer_id,
                        session_id=session_id,
                        last_seen=datetime.now(timezone.utc),
                        status="online"
                    )
                    self.db.add(online_record)
            
            elif status == "offline" and online_record:
                # Update to offline
                online_record.status = "offline"
                online_record.last_seen = datetime.now(timezone.utc)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating customer online status: {str(e)}")
    
    def _update_customer_statistics(self, session: RadiusSession) -> None:
        """
        Update customer usage statistics
        """
        try:
            # Get or create customer statistics record
            stats = self.db.query(CustomerStatistics).filter(
                CustomerStatistics.customer_id == session.customer_id
            ).first()
            
            if not stats:
                stats = CustomerStatistics(
                    customer_id=session.customer_id,
                    total_sessions=0,
                    total_bytes_in=0,
                    total_bytes_out=0,
                    total_session_time=0,
                    last_session_start=None,
                    last_session_end=None
                )
                self.db.add(stats)
            
            # Update statistics
            stats.total_sessions += 1
            stats.total_bytes_in += session.bytes_in or 0
            stats.total_bytes_out += session.bytes_out or 0
            stats.total_session_time += session.session_duration or 0
            stats.last_session_start = session.start_time
            stats.last_session_end = session.end_time
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating customer statistics: {str(e)}")
    
    def _check_usage_limits(self, session: RadiusSession) -> None:
        """
        Check usage limits and enforce restrictions if necessary
        """
        try:
            # Get service plan
            service_plan = self.service_plan_repo.get(session.service_plan_id)
            if not service_plan:
                return
            
            # Get internet service details for data limits
            internet_service = self.db.query(InternetService).filter(
                InternetService.service_plan_id == service_plan.id
            ).first()
            
            if internet_service and internet_service.data_limit:
                total_usage = (session.bytes_in or 0) + (session.bytes_out or 0)
                limit_bytes = internet_service.data_limit * 1024 * 1024  # Convert MB to bytes
                
                if total_usage >= limit_bytes:
                    logger.warning(f"Customer {session.customer_id} exceeded data limit in session {session.id}")
                    # Here you could implement automatic session termination or speed throttling
                    # For now, just log the event
            
        except Exception as e:
            logger.error(f"Error checking usage limits for session {session.id}: {str(e)}")
