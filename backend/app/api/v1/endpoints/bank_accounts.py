"""
Bank Account Endpoints

FastAPI endpoints for managing bank accounts with RBAC protection.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....core.exceptions import NotFoundError, ValidationError, DuplicateError, PermissionDeniedError
from ....core.rbac_decorators import require_permission
from ....api.v1.dependencies import get_current_admin
from ....services.bank_account_service import BankAccountService
from ....schemas.bank_account import (
    BankAccountCreateRequest,
    BankAccountUpdateRequest,
    BankAccountVerifyRequest,
    BankAccountResponse,
    BankAccountListResponse,
    BankAccountStatsResponse,
    BankAccountOwnerTypeEnum
)


logger = logging.getLogger(__name__)
router = APIRouter()


def get_bank_account_service(db: Session = Depends(get_db)) -> BankAccountService:
    """Get bank account service instance."""
    return BankAccountService(db)


def get_user_context(current_admin=Depends(get_current_admin)):
    """Get user context for RBAC."""
    # For now, all authenticated users are treated as admin
    # This can be extended later with proper role checking
    return {"user_type": "admin", "user_id": current_admin.id}


@router.post("/", response_model=BankAccountResponse)
@require_permission("billing.manage")
async def create_bank_account(
    account_data: BankAccountCreateRequest,
    service: BankAccountService = Depends(get_bank_account_service),
    user_context: dict = Depends(get_user_context),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new bank account.
    
    Requires: billing.manage permission
    """
    try:
        account = service.create_bank_account(
            account_data.dict(),
            current_user_type=user_context["user_type"],
            current_user_id=user_context["user_id"]
        )
        return BankAccountResponse.from_orm(account)
    except (ValidationError, DuplicateError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating bank account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=BankAccountListResponse)
@require_permission("billing.view")
async def list_bank_accounts(
    owner_type: Optional[BankAccountOwnerTypeEnum] = Query(None),
    active_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: BankAccountService = Depends(get_bank_account_service),
    user_context: dict = Depends(get_user_context),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List bank accounts with filtering.
    
    Requires: billing.view permission
    """
    try:
        accounts = service.list_bank_accounts(
            owner_type=owner_type.value if owner_type else None,
            active_only=active_only,
            current_user_type=user_context["user_type"],
            current_user_id=user_context["user_id"],
            limit=limit,
            offset=offset
        )
        
        # Get total count for pagination
        total_accounts = service.list_bank_accounts(
            owner_type=owner_type.value if owner_type else None,
            active_only=active_only,
            current_user_type=user_context["user_type"],
            current_user_id=user_context["user_id"],
            limit=1000,  # Large number to get total
            offset=0
        )
        
        return BankAccountListResponse(
            accounts=[BankAccountResponse.from_orm(account) for account in accounts],
            total=len(total_accounts),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error listing bank accounts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{account_id}", response_model=BankAccountResponse)
@require_permission("billing.view")
async def get_bank_account(
    account_id: int,
    service: BankAccountService = Depends(get_bank_account_service),
    user_context: dict = Depends(get_user_context),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get bank account by ID.
    
    Requires: billing.view permission
    """
    try:
        account = service.get_bank_account(
            account_id,
            current_user_type=user_context["user_type"],
            current_user_id=user_context["user_id"]
        )
        return BankAccountResponse.from_orm(account)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting bank account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{account_id}", response_model=BankAccountResponse)
@require_permission("billing.manage")
async def update_bank_account(
    account_id: int,
    update_data: BankAccountUpdateRequest,
    service: BankAccountService = Depends(get_bank_account_service),
    user_context: dict = Depends(get_user_context),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update bank account.
    
    Requires: billing.manage permission
    """
    try:
        account = service.update_bank_account(
            account_id,
            update_data.dict(exclude_unset=True),
            current_user_type=user_context["user_type"],
            current_user_id=user_context["user_id"]
        )
        return BankAccountResponse.from_orm(account)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValidationError, DuplicateError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating bank account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{account_id}")
@require_permission("billing.manage")
async def delete_bank_account(
    account_id: int,
    service: BankAccountService = Depends(get_bank_account_service),
    user_context: dict = Depends(get_user_context),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete bank account (soft delete).
    
    Requires: billing.manage permission
    """
    try:
        service.delete_bank_account(
            account_id,
            current_user_type=user_context["user_type"],
            current_user_id=user_context["user_id"]
        )
        return {"message": "Bank account deactivated successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting bank account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{account_id}/verify", response_model=BankAccountResponse)
@require_permission("billing.admin")
async def verify_bank_account(
    account_id: int,
    verify_data: BankAccountVerifyRequest,
    service: BankAccountService = Depends(get_bank_account_service),
    user_context: dict = Depends(get_user_context),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Verify bank account (admin only).
    
    Requires: billing.admin permission
    """
    try:
        account = service.verify_bank_account(
            account_id,
            verification_notes=verify_data.verification_notes,
            current_user_type=user_context["user_type"]
        )
        return BankAccountResponse.from_orm(account)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying bank account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/platform/collection-accounts", response_model=List[BankAccountResponse])
async def get_platform_collection_accounts(
    active_only: bool = Query(True),
    service: BankAccountService = Depends(get_bank_account_service)
):
    """
    Get platform collection accounts for customer payments.
    
    Public endpoint for customer payment forms.
    """
    try:
        accounts = service.get_platform_collection_accounts(active_only=active_only)
        return [BankAccountResponse.from_orm(account) for account in accounts]
    except Exception as e:
        logger.error(f"Error getting platform collection accounts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reseller/{reseller_id}/payout-accounts", response_model=List[BankAccountResponse])
@require_permission("billing.view")
async def get_reseller_payout_accounts(
    reseller_id: int,
    active_only: bool = Query(True),
    service: BankAccountService = Depends(get_bank_account_service),
    user_context: dict = Depends(get_user_context),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get reseller payout accounts.
    
    Requires: billing.view permission
    """
    try:
        # RBAC: Resellers can only view their own accounts
        if (user_context["user_type"] == "reseller" and 
            user_context["user_id"] != reseller_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        accounts = service.get_reseller_payout_accounts(
            reseller_id=reseller_id,
            active_only=active_only
        )
        return [BankAccountResponse.from_orm(account) for account in accounts]
    except Exception as e:
        logger.error(f"Error getting reseller payout accounts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics", response_model=BankAccountStatsResponse)
@require_permission("billing.view")
async def get_bank_account_statistics(
    service: BankAccountService = Depends(get_bank_account_service),
    user_context: dict = Depends(get_user_context),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get bank account statistics.
    
    Requires: billing.view permission
    """
    try:
        stats = service.get_bank_account_statistics(
            current_user_type=user_context["user_type"],
            current_user_id=user_context["user_id"]
        )
        return BankAccountStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting bank account statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
