"""
Comprehensive Ticketing System API Endpoints
Support, Technical, Incident, Field Work, SLA, Escalation, Knowledge Base
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.auth.base import Administrator
from app.schemas.ticketing import (
    TicketCreate, TicketUpdate, TicketResponse, TicketStatusUpdate, 
    TicketAssignment, TicketSearchFilters, TicketStatisticsResponse,
    PaginatedTicketResponse, TicketMessageCreate, TicketMessageResponse, 
    PaginatedMessageResponse, TicketEscalationCreate, TicketEscalationResponse,
    FieldWorkOrderCreate, FieldWorkOrderUpdate, FieldWorkOrderResponse,
    TicketTimeEntryCreate, TicketTimeEntryResponse, SLAPolicyCreate, 
    SLAPolicyResponse, KnowledgeBaseArticleCreate, KnowledgeBaseArticleResponse,
    NetworkIncidentCreate, NetworkIncidentResponse, TicketTemplateCreate, 
    TicketTemplateResponse, TicketTypeEnum, TicketPriorityEnum, TicketStatusEnum, 
    TicketSourceEnum, EscalationReasonEnum, FieldWorkStatusEnum
)
from app.services.ticketing_service import (
    TicketService, TicketMessageService, TicketEscalationService,
    FieldWorkService, KnowledgeBaseService
)
from app.models.ticketing import (
    Ticket, TicketMessage, TicketEscalation, FieldWorkOrder,
    TicketTimeEntry, SLAPolicy, KnowledgeBaseArticle,
    NetworkIncident, TicketTemplate
)

router = APIRouter()

# ============================================================================
# TICKET MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Create new support ticket"""
    try:
        ticket_service = TicketService(db)
        ticket = ticket_service.create_ticket(
            ticket_data.dict(), 
            created_by=current_admin.id
        )
        return ticket
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tickets", response_model=PaginatedTicketResponse)
async def search_tickets(
    customer_id: Optional[int] = Query(None),
    assigned_to: Optional[int] = Query(None),
    status: Optional[TicketStatusEnum] = Query(None),
    priority: Optional[TicketPriorityEnum] = Query(None),
    ticket_type: Optional[TicketTypeEnum] = Query(None),
    category: Optional[str] = Query(None),
    overdue: Optional[bool] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    search_text: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Search tickets with filters and pagination"""
    try:
        filters = {
            'customer_id': customer_id,
            'assigned_to': assigned_to,
            'status': status.value if status else None,
            'priority': priority.value if priority else None,
            'ticket_type': ticket_type.value if ticket_type else None,
            'category': category,
            'overdue': overdue,
            'created_after': created_after,
            'created_before': created_before,
            'search_text': search_text
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        
        ticket_service = TicketService(db)
        tickets, total = ticket_service.search_tickets(filters, page, per_page)
        
        return {
            "tickets": tickets,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get ticket by ID"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Update existing ticket"""
    try:
        ticket_service = TicketService(db)
        update_data = {k: v for k, v in ticket_update.dict().items() if v is not None}
        ticket = ticket_service.update_ticket(
            ticket_id, 
            update_data, 
            updated_by=current_admin.id
        )
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/tickets/{ticket_id}/status", response_model=TicketResponse)
async def change_ticket_status(
    ticket_id: int,
    status_update: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Change ticket status"""
    try:
        ticket_service = TicketService(db)
        ticket = ticket_service.change_ticket_status(
            ticket_id,
            status_update.status.value,
            status_update.reason,
            changed_by=current_admin.id
        )
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/tickets/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: int,
    assignment: TicketAssignment,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Assign ticket to agent/team"""
    try:
        ticket_service = TicketService(db)
        ticket = ticket_service.assign_ticket(
            ticket_id,
            assignment.assigned_to,
            assignment.assigned_team,
            assigned_by=current_admin.id
        )
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tickets/statistics", response_model=TicketStatisticsResponse)
async def get_ticket_statistics(
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get ticket statistics and metrics"""
    try:
        filters = {}
        if created_after:
            filters['created_after'] = created_after
        if created_before:
            filters['created_before'] = created_before
        
        ticket_service = TicketService(db)
        stats = ticket_service.get_ticket_statistics(filters)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# TICKET MESSAGE ENDPOINTS
# ============================================================================

@router.post("/tickets/{ticket_id}/messages", response_model=TicketMessageResponse)
async def add_ticket_message(
    ticket_id: int,
    message_data: TicketMessageCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Add message to ticket"""
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        message_service = TicketMessageService(db)
        message_dict = message_data.dict()
        
        if not message_dict.get('author_id'):
            message_dict['author_id'] = current_admin.id
        if not message_dict.get('author_name'):
            message_dict['author_name'] = current_admin.username
        if not message_dict.get('author_email'):
            message_dict['author_email'] = current_admin.email
        
        message = message_service.add_message(ticket_id, message_dict)
        return message
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tickets/{ticket_id}/messages", response_model=PaginatedMessageResponse)
async def get_ticket_messages(
    ticket_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get messages for ticket"""
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        message_service = TicketMessageService(db)
        messages, total = message_service.get_ticket_messages(ticket_id, page, per_page)
        
        return {
            "messages": messages,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# FIELD WORK ORDER ENDPOINTS
# ============================================================================

@router.post("/tickets/{ticket_id}/field-work", response_model=FieldWorkOrderResponse)
async def create_field_work_order(
    ticket_id: int,
    work_data: FieldWorkOrderCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Create field work order for ticket"""
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        field_work_service = FieldWorkService(db)
        field_work = field_work_service.create_field_work_order(
            ticket_id, 
            work_data.dict()
        )
        return field_work
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/field-work", response_model=List[FieldWorkOrderResponse])
async def get_field_work_orders(
    status: Optional[FieldWorkStatusEnum] = Query(None),
    assigned_technician: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get field work orders with filters"""
    try:
        query = db.query(FieldWorkOrder)
        
        if status:
            query = query.filter(FieldWorkOrder.status == status.value)
        if assigned_technician:
            query = query.filter(FieldWorkOrder.assigned_technician == assigned_technician)
        
        field_work_orders = query.order_by(
            FieldWorkOrder.scheduled_date.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        return field_work_orders
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# KNOWLEDGE BASE ENDPOINTS
# ============================================================================

@router.post("/knowledge-base/articles", response_model=KnowledgeBaseArticleResponse)
async def create_knowledge_article(
    article_data: KnowledgeBaseArticleCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Create knowledge base article"""
    try:
        kb_service = KnowledgeBaseService(db)
        article = kb_service.create_article(
            article_data.dict(), 
            author_id=current_admin.id
        )
        return article
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knowledge-base/articles", response_model=List[KnowledgeBaseArticleResponse])
async def search_knowledge_articles(
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Search knowledge base articles"""
    try:
        filters = {}
        if category:
            filters['category'] = category
        if is_public is not None:
            filters['is_public'] = is_public
        
        kb_service = KnowledgeBaseService(db)
        articles, total = kb_service.search_articles(
            query or "", 
            filters, 
            page, 
            per_page
        )
        return articles
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knowledge-base/articles/{article_id}", response_model=KnowledgeBaseArticleResponse)
async def get_knowledge_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get knowledge base article by ID"""
    article = db.query(KnowledgeBaseArticle).filter(
        KnowledgeBaseArticle.id == article_id
    ).first()
    if not article:
        raise HTTPException(status_code=404, detail="Knowledge base article not found")
    
    article.view_count += 1
    db.commit()
    
    return article


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard/overview")
async def get_ticketing_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin_user)
):
    """Get ticketing system dashboard overview"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        ticket_service = TicketService(db)
        stats = ticket_service.get_ticket_statistics({
            'created_after': start_date
        })
        
        recent_tickets, _ = ticket_service.search_tickets(
            {'created_after': start_date}, 
            page=1, 
            per_page=10
        )
        
        overdue_tickets, _ = ticket_service.search_tickets(
            {'overdue': True}, 
            page=1, 
            per_page=10
        )
        
        return {
            'period_days': days,
            'ticket_statistics': stats,
            'recent_tickets': recent_tickets,
            'overdue_tickets': overdue_tickets,
            'generated_at': datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# ============================================================================
# Backward Compatibility Redirects (Temporary - Remove after 6 months)
# ============================================================================

from fastapi.responses import RedirectResponse

# Redirect old /tickets/* paths to new /support/tickets/* paths
@router.get("/tickets/{path:path}")
async def redirect_old_tickets_get(path: str):
    """Temporary redirect for old /tickets/* paths"""
    new_path = f"/api/v1/support/tickets/{path}"
    return RedirectResponse(url=new_path, status_code=307)

@router.post("/tickets/{path:path}")
async def redirect_old_tickets_post(path: str):
    """Temporary redirect for old /tickets/* paths"""
    new_path = f"/api/v1/support/tickets/{path}"
    return RedirectResponse(url=new_path, status_code=307)

@router.put("/tickets/{path:path}")
async def redirect_old_tickets_put(path: str):
    """Temporary redirect for old /tickets/* paths"""
    new_path = f"/api/v1/support/tickets/{path}"
    return RedirectResponse(url=new_path, status_code=307)

@router.patch("/tickets/{path:path}")
async def redirect_old_tickets_patch(path: str):
    """Temporary redirect for old /tickets/* paths"""
    new_path = f"/api/v1/support/tickets/{path}"
    return RedirectResponse(url=new_path, status_code=307)

@router.delete("/tickets/{path:path}")
async def redirect_old_tickets_delete(path: str):
    """Temporary redirect for old /tickets/* paths"""
    new_path = f"/api/v1/support/tickets/{path}"
    return RedirectResponse(url=new_path, status_code=307)

