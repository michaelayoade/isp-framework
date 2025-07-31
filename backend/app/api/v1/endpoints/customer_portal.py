"""
Customer Portal API Endpoints
Complete self-service portal for ISP customers
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_customer
from app.models.customer.base import Customer
from app.services.customer_portal_service import (
    CustomerPortalSessionService,
    CustomerPortalPaymentService, 
    CustomerPortalServiceRequestService,
    CustomerPortalDashboardService,
    CustomerPortalNotificationService
)
from app.schemas.customer_portal import (
    CustomerPortalSessionResponse, CustomerPortalDashboardResponse,
    CustomerPortalPaymentResponse, CustomerPortalInvoiceResponse,
    CustomerPortalServiceRequestResponse, CustomerPortalUsageResponse,
    CustomerPortalNotificationResponse, CustomerPortalPreferencesResponse,
    CustomerPortalFAQResponse, CustomerPortalActivityResponse,
    CustomerPortalLoginRequest, CustomerPortalPaymentRequest,
    CustomerPortalServiceRequest, CustomerPortalPreferencesUpdate,
    CustomerPortalLogoutRequest, CustomerPortalServiceRequestCreate
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Portal Authentication Endpoints
@router.post("/auth/login", response_model=CustomerPortalSessionResponse)
async def portal_login(
    login_data: CustomerPortalLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Customer portal login with session management"""
    try:
        # Authenticate customer (mock implementation)
        customer = db.query(Customer).filter_by(portal_id=login_data.portal_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid portal ID or password"
            )
        
        # Create portal session
        session_service = CustomerPortalSessionService(db)
        session_data = {
            'session_type': 'web',
            'ip_address': request.client.host,
            'user_agent': request.headers.get('user-agent'),
            'login_method': 'password',
            'device_info': {
                'browser': request.headers.get('user-agent', '').split('/')[0],
                'platform': 'web'
            }
        }
        
        session = session_service.create_session(customer.id, session_data)
        
        return CustomerPortalSessionResponse(
            session_token=session.session_token,
            customer_id=customer.id,
            customer_name=customer.name,
            expires_at=session.expires_at,
            session_type=session.session_type
        )
        
    except Exception as e:
        logger.error(f"Portal login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/auth/logout")
async def portal_logout(
    logout_data: CustomerPortalLogoutRequest,
    db: Session = Depends(get_db)
):
    """Customer portal logout"""
    try:
        session_service = CustomerPortalSessionService(db)
        success = session_service.logout_session(logout_data.session_token)
        
        if success:
            return {"message": "Logged out successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
            
    except Exception as e:
        logger.error(f"Portal logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


# Dashboard Endpoints
@router.get("/dashboard", response_model=CustomerPortalDashboardResponse)
async def get_dashboard(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer portal dashboard data"""
    try:
        dashboard_service = CustomerPortalDashboardService(db)
        dashboard_data = dashboard_service.get_dashboard_data(current_customer.id)
        
        return CustomerPortalDashboardResponse(**dashboard_data)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard"
        )


# Billing & Payment Endpoints
@router.post("/billing/payments", response_model=CustomerPortalPaymentResponse)
async def process_payment(
    payment_data: CustomerPortalPaymentRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Process customer payment through portal"""
    try:
        payment_service = CustomerPortalPaymentService(db)
        payment = payment_service.process_payment(
            current_customer.id, 
            payment_data.dict()
        )
        
        return CustomerPortalPaymentResponse(
            id=payment.id,
            payment_reference=payment.payment_reference,
            amount=payment.payment_amount,
            currency=payment.currency,
            status=payment.status,
            payment_method=payment.payment_method,
            processed_at=payment.processed_at,
            external_payment_id=payment.external_payment_id,
            processor_fee=payment.processor_fee,
            net_amount=payment.net_amount
        )
        
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment processing failed"
        )


@router.get("/billing/payments", response_model=List[CustomerPortalPaymentResponse])
async def get_payment_history(
    limit: int = 20,
    offset: int = 0,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer payment history"""
    try:
        payment_service = CustomerPortalPaymentService(db)
        payments = payment_service.get_payment_history(
            current_customer.id, 
            limit=limit, 
            offset=offset
        )
        
        return [
            CustomerPortalPaymentResponse(
                id=payment.id,
                payment_reference=payment.payment_reference,
                amount=payment.payment_amount,
                currency=payment.currency,
                status=payment.status,
                payment_method=payment.payment_method,
                processed_at=payment.processed_at,
                external_payment_id=payment.external_payment_id,
                processor_fee=payment.processor_fee,
                net_amount=payment.net_amount
            )
            for payment in payments
        ]
        
    except Exception as e:
        logger.error(f"Payment history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment history"
        )


@router.get("/billing/invoices", response_model=List[CustomerPortalInvoiceResponse])
async def get_invoices(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer invoices"""
    try:
        # Mock implementation - would integrate with actual billing service
        invoices = []
        
        return invoices
        
    except Exception as e:
        logger.error(f"Invoice retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoices"
        )


# Service Management Endpoints
@router.post("/services/requests", response_model=CustomerPortalServiceRequestResponse)
async def create_service_request(
    request_data: CustomerPortalServiceRequestCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Create new service change request"""
    try:
        service_request_service = CustomerPortalServiceRequestService(db)
        service_request = service_request_service.create_service_request(
            current_customer.id,
            request_data.dict()
        )
        
        return CustomerPortalServiceRequestResponse(
            id=service_request.id,
            request_type=service_request.request_type,
            request_title=service_request.request_title,
            request_description=service_request.request_description,
            status=service_request.status,
            urgency=service_request.urgency,
            preferred_date=service_request.preferred_date,
            estimated_monthly_change=service_request.estimated_monthly_change,
            one_time_fees=service_request.one_time_fees,
            requires_technician=service_request.requires_technician,
            created_at=service_request.created_at,
            updated_at=service_request.updated_at
        )
        
    except Exception as e:
        logger.error(f"Service request creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create service request"
        )


@router.get("/services/requests", response_model=List[CustomerPortalServiceRequestResponse])
async def get_service_requests(
    status: Optional[str] = None,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer service requests"""
    try:
        service_request_service = CustomerPortalServiceRequestService(db)
        requests = service_request_service.get_customer_service_requests(
            current_customer.id,
            status=status
        )
        
        return [
            CustomerPortalServiceRequestResponse(
                id=request.id,
                request_type=request.request_type,
                request_title=request.request_title,
                request_description=request.request_description,
                status=request.status,
                urgency=request.urgency,
                preferred_date=request.preferred_date,
                estimated_monthly_change=request.estimated_monthly_change,
                one_time_fees=request.one_time_fees,
                requires_technician=request.requires_technician,
                created_at=request.created_at,
                updated_at=request.updated_at
            )
            for request in requests
        ]
        
    except Exception as e:
        logger.error(f"Service requests retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service requests"
        )


@router.get("/services/{service_id}/upgrade-options")
async def get_upgrade_options(
    service_id: int,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get available service upgrade options"""
    try:
        service_request_service = CustomerPortalServiceRequestService(db)
        upgrade_options = service_request_service.get_available_upgrades(
            current_customer.id,
            service_id
        )
        
        return {"upgrade_options": upgrade_options}
        
    except Exception as e:
        logger.error(f"Upgrade options error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upgrade options"
        )


@router.get("/services/usage", response_model=List[CustomerPortalUsageResponse])
async def get_service_usage(
    service_id: Optional[int] = None,
    period: str = "current_month",
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer service usage data"""
    try:
        # Mock implementation - would integrate with actual usage tracking
        usage_data = [
            {
                "service_id": 1,
                "service_name": "Internet Service",
                "period": period,
                "data_used_gb": 45.2,
                "data_limit_gb": 100.0,
                "usage_percentage": 45.2,
                "overage_gb": 0.0,
                "overage_charges": 0.0,
                "peak_usage_date": datetime.now().date(),
                "daily_usage": []
            }
        ]
        
        return usage_data
        
    except Exception as e:
        logger.error(f"Usage data error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage data"
        )


# Notification Endpoints
@router.get("/notifications", response_model=List[CustomerPortalNotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer notifications"""
    try:
        notification_service = CustomerPortalNotificationService(db)
        notifications = notification_service.get_customer_notifications(
            current_customer.id,
            unread_only=unread_only,
            limit=limit,
            offset=offset
        )
        
        return [
            CustomerPortalNotificationResponse(
                id=notif.id,
                notification_type=notif.notification_type,
                title=notif.title,
                message=notif.message,
                priority=notif.priority,
                category=notif.category,
                is_read=notif.is_read,
                action_required=notif.action_required,
                action_url=notif.action_url,
                action_text=notif.action_text,
                created_at=notif.created_at,
                read_at=notif.read_at
            )
            for notif in notifications
        ]
        
    except Exception as e:
        logger.error(f"Notifications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    try:
        notification_service = CustomerPortalNotificationService(db)
        success = notification_service.mark_as_read(
            current_customer.id,
            notification_id
        )
        
        if success:
            return {"message": "Notification marked as read"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
            
    except Exception as e:
        logger.error(f"Mark notification read error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.delete("/notifications/{notification_id}")
async def dismiss_notification(
    notification_id: int,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Dismiss notification"""
    try:
        notification_service = CustomerPortalNotificationService(db)
        success = notification_service.dismiss_notification(
            current_customer.id,
            notification_id
        )
        
        if success:
            return {"message": "Notification dismissed"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
            
    except Exception as e:
        logger.error(f"Dismiss notification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to dismiss notification"
        )


# Account Management Endpoints
@router.get("/account/preferences", response_model=CustomerPortalPreferencesResponse)
async def get_preferences(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer portal preferences"""
    try:
        # Mock implementation - would get actual preferences
        preferences = {
            "language": "en",
            "timezone": "UTC",
            "email_notifications": True,
            "sms_notifications": False,
            "marketing_emails": True,
            "invoice_delivery": "email",
            "auto_pay_enabled": False,
            "dashboard_layout": "standard",
            "theme": "light"
        }
        
        return preferences
        
    except Exception as e:
        logger.error(f"Preferences error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences"
        )


@router.put("/account/preferences")
async def update_preferences(
    preferences: CustomerPortalPreferencesUpdate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Update customer portal preferences"""
    try:
        # Mock implementation - would update actual preferences
        return {"message": "Preferences updated successfully"}
        
    except Exception as e:
        logger.error(f"Update preferences error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


# Support Endpoints
@router.get("/support/faq", response_model=List[CustomerPortalFAQResponse])
async def get_faq(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get frequently asked questions"""
    try:
        # Mock implementation - would get actual FAQ data
        faq_items = [
            {
                "id": 1,
                "question": "How do I pay my bill online?",
                "answer": "You can pay your bill through the billing section of this portal using a credit card, debit card, or bank transfer.",
                "category": "billing",
                "helpful_count": 25,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "id": 2,
                "question": "How do I upgrade my internet speed?",
                "answer": "You can request a service upgrade through the Services section. Select your current service and choose from available upgrade options.",
                "category": "services",
                "helpful_count": 18,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        return faq_items
        
    except Exception as e:
        logger.error(f"FAQ error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve FAQ"
        )


@router.get("/account/activity", response_model=List[CustomerPortalActivityResponse])
async def get_account_activity(
    limit: int = 20,
    offset: int = 0,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer account activity log"""
    try:
        dashboard_service = CustomerPortalDashboardService(db)
        activities = dashboard_service._get_recent_activity(
            current_customer.id,
            limit=limit
        )
        
        return [
            CustomerPortalActivityResponse(
                id=activity['id'],
                activity_type=activity['type'],
                action_description=activity['description'],
                timestamp=activity['timestamp'],
                page_url=activity.get('page_url')
            )
            for activity in activities
        ]
        
    except Exception as e:
        logger.error(f"Activity log error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity log"
        )
