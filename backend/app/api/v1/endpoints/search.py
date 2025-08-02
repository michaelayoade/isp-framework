"""Global search endpoint for ISP Framework layout top bar."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.core.database import get_db
from app.api.dependencies import get_current_admin_user
from app.core.permissions import require_permission
from app.models.auth.base import Administrator
from app.models.customer import Customer
from app.schemas.search import GlobalSearchResponse, SearchResult

router = APIRouter()


@router.get("/global", response_model=GlobalSearchResponse)
@require_permission("dashboard.view")
async def global_search(
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    categories: Optional[List[str]] = Query(None, description="Filter by categories: customers"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results per category"),
    db: Session = Depends(get_db),
    current_user: Administrator = Depends(get_current_admin_user)
):
    """
    Global search across ISP Framework entities for layout top bar.
    
    Currently supports:
    - Customers (name, email, phone, portal_id)
    
    Additional categories (services, devices, tickets, billing) will be added in future updates.
    """
    try:
        results = {}
        total_results = 0
        
        # Determine which categories to search (currently only customers)
        search_categories = categories or ["customers"]
        
        # Search Customers
        if "customers" in search_categories:
            customer_results = _search_customers(db, q, limit)
            if customer_results:
                results["customers"] = customer_results
                total_results += len(customer_results)
        
        return GlobalSearchResponse(
            query=q,
            total_results=total_results,
            categories=list(results.keys()),
            results=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


def _search_customers(db: Session, query: str, limit: int) -> List[SearchResult]:
    """Search customers by name, email, phone, portal_id."""
    search_term = f"%{query.lower()}%"
    
    customers = db.query(Customer).filter(
        or_(
            func.lower(Customer.name).like(search_term),
            func.lower(Customer.email).like(search_term),
            func.lower(Customer.phone).like(search_term),
            func.lower(Customer.portal_id).like(search_term)
        )
    ).limit(limit).all()
    
    results = []
    for customer in customers:
        results.append(SearchResult(
            id=customer.id,
            title=customer.name,
            subtitle=customer.email,
            description=f"Customer ID: {customer.portal_id} | Phone: {customer.phone or 'N/A'}",
            category="customers",
            url=f"/customers/{customer.id}",
            metadata={
                "portal_id": customer.portal_id,
                "status_id": customer.status_id,
                "created_at": customer.created_at.isoformat() if customer.created_at else None
            }
        ))
    
    return results






