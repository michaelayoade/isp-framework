"""
Bank Account Service

Service layer for managing bank accounts (platform collections and reseller payouts).
Handles CRUD operations with proper RBAC filtering.
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..core.exceptions import NotFoundError, ValidationError, DuplicateError, PermissionDeniedError
from ..models.billing.bank_accounts import BankAccount, BankAccountOwnerType


logger = logging.getLogger(__name__)


class BankAccountService:
    """Service for managing bank accounts."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_bank_account(
        self, 
        account_data: Dict[str, Any], 
        current_user_type: str = "admin",
        current_user_id: Optional[int] = None
    ) -> BankAccount:
        """
        Create a new bank account.
        
        Args:
            account_data: Bank account data
            current_user_type: Type of current user (admin, reseller)
            current_user_id: ID of current user (for reseller accounts)
            
        Returns:
            Created bank account instance
        """
        owner_type = BankAccountOwnerType(account_data["owner_type"])
        
        # RBAC: Only admins can create platform accounts
        if owner_type == BankAccountOwnerType.PLATFORM and current_user_type != "admin":
            raise PermissionDeniedError("Only administrators can create platform collection accounts")
        
        # RBAC: Resellers can only create their own accounts
        if owner_type == BankAccountOwnerType.RESELLER:
            if current_user_type == "reseller":
                account_data["owner_id"] = current_user_id
            elif current_user_type == "admin" and "owner_id" not in account_data:
                raise ValidationError("owner_id is required for reseller accounts")
        
        # Validate owner_id for reseller accounts
        if owner_type == BankAccountOwnerType.RESELLER and not account_data.get("owner_id"):
            raise ValidationError("owner_id is required for reseller accounts")
        
        # Platform accounts should not have owner_id
        if owner_type == BankAccountOwnerType.PLATFORM:
            account_data["owner_id"] = None
        
        # Check for duplicate account numbers (within same owner)
        existing = self.db.query(BankAccount).filter(
            BankAccount.account_number == account_data["account_number"],
            BankAccount.owner_type == owner_type
        )
        
        if owner_type == BankAccountOwnerType.RESELLER:
            existing = existing.filter(BankAccount.owner_id == account_data["owner_id"])
        
        if existing.first():
            raise DuplicateError(f"Bank account with number '{account_data['account_number']}' already exists")
        
        # Create bank account
        bank_account = BankAccount(
            owner_type=owner_type,
            owner_id=account_data.get("owner_id"),
            bank_name=account_data["bank_name"],
            account_number=account_data["account_number"],
            account_name=account_data["account_name"],
            bank_code=account_data.get("bank_code"),
            branch_code=account_data.get("branch_code"),
            branch_name=account_data.get("branch_name"),
            currency=account_data.get("currency", "USD"),
            country=account_data.get("country", "NG"),
            alias=account_data.get("alias"),
            description=account_data.get("description"),
            active=account_data.get("active", True),
            verified=account_data.get("verified", False)
        )
        
        self.db.add(bank_account)
        self.db.commit()
        self.db.refresh(bank_account)
        
        logger.info(f"Created bank account: {bank_account.alias or bank_account.account_number}")
        return bank_account
    
    def get_bank_account(
        self, 
        account_id: int,
        current_user_type: str = "admin",
        current_user_id: Optional[int] = None
    ) -> BankAccount:
        """
        Get bank account by ID with RBAC filtering.
        
        Args:
            account_id: Bank account ID
            current_user_type: Type of current user
            current_user_id: ID of current user
            
        Returns:
            Bank account instance
        """
        account = self.db.query(BankAccount).filter(BankAccount.id == account_id).first()
        if not account:
            raise NotFoundError(f"Bank account with ID {account_id} not found")
        
        # RBAC: Check access permissions
        if not self._can_access_account(account, current_user_type, current_user_id):
            raise PermissionDeniedError("Access denied to this bank account")
        
        return account
    
    def list_bank_accounts(
        self,
        owner_type: Optional[str] = None,
        active_only: bool = False,
        current_user_type: str = "admin",
        current_user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[BankAccount]:
        """
        List bank accounts with RBAC filtering.
        
        Args:
            owner_type: Filter by owner type (PLATFORM, RESELLER)
            active_only: Only return active accounts
            current_user_type: Type of current user
            current_user_id: ID of current user
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of bank account instances
        """
        query = self.db.query(BankAccount)
        
        # Apply RBAC filtering
        if current_user_type == "reseller":
            # Resellers can only see their own accounts and active platform accounts
            query = query.filter(
                (BankAccount.owner_type == BankAccountOwnerType.RESELLER) & 
                (BankAccount.owner_id == current_user_id) |
                (BankAccount.owner_type == BankAccountOwnerType.PLATFORM) & 
                (BankAccount.active == True)
            )
        elif current_user_type == "customer":
            # Customers can only see active platform accounts
            query = query.filter(
                BankAccount.owner_type == BankAccountOwnerType.PLATFORM,
                BankAccount.active == True
            )
        
        # Apply additional filters
        if owner_type:
            query = query.filter(BankAccount.owner_type == BankAccountOwnerType(owner_type))
        
        if active_only:
            query = query.filter(BankAccount.active == True)
        
        return query.offset(offset).limit(limit).all()
    
    def update_bank_account(
        self,
        account_id: int,
        update_data: Dict[str, Any],
        current_user_type: str = "admin",
        current_user_id: Optional[int] = None
    ) -> BankAccount:
        """
        Update bank account.
        
        Args:
            account_id: Bank account ID
            update_data: Data to update
            current_user_type: Type of current user
            current_user_id: ID of current user
            
        Returns:
            Updated bank account instance
        """
        account = self.get_bank_account(account_id, current_user_type, current_user_id)
        
        # RBAC: Only admins can update platform accounts
        if account.owner_type == BankAccountOwnerType.PLATFORM and current_user_type != "admin":
            raise PermissionDeniedError("Only administrators can update platform accounts")
        
        # RBAC: Resellers can only update their own accounts
        if (account.owner_type == BankAccountOwnerType.RESELLER and 
            current_user_type == "reseller" and 
            account.owner_id != current_user_id):
            raise PermissionDeniedError("Resellers can only update their own accounts")
        
        # Prevent changing owner_type and owner_id
        restricted_fields = ["owner_type", "owner_id"]
        for field in restricted_fields:
            if field in update_data:
                del update_data[field]
                logger.warning(f"Attempted to update restricted field: {field}")
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(account, field):
                setattr(account, field, value)
        
        self.db.commit()
        self.db.refresh(account)
        
        logger.info(f"Updated bank account: {account.alias or account.account_number}")
        return account
    
    def delete_bank_account(
        self,
        account_id: int,
        current_user_type: str = "admin",
        current_user_id: Optional[int] = None
    ) -> None:
        """
        Delete bank account (soft delete by deactivating).
        
        Args:
            account_id: Bank account ID
            current_user_type: Type of current user
            current_user_id: ID of current user
        """
        account = self.get_bank_account(account_id, current_user_type, current_user_id)
        
        # RBAC: Only admins can delete platform accounts
        if account.owner_type == BankAccountOwnerType.PLATFORM and current_user_type != "admin":
            raise PermissionDeniedError("Only administrators can delete platform accounts")
        
        # RBAC: Resellers can only delete their own accounts
        if (account.owner_type == BankAccountOwnerType.RESELLER and 
            current_user_type == "reseller" and 
            account.owner_id != current_user_id):
            raise PermissionDeniedError("Resellers can only delete their own accounts")
        
        account.active = False
        self.db.commit()
        
        logger.info(f"Deactivated bank account: {account.alias or account.account_number}")
    
    def verify_bank_account(
        self,
        account_id: int,
        verification_notes: Optional[str] = None,
        current_user_type: str = "admin"
    ) -> BankAccount:
        """
        Verify bank account (admin only).
        
        Args:
            account_id: Bank account ID
            verification_notes: Optional verification notes
            current_user_type: Type of current user
            
        Returns:
            Updated bank account instance
        """
        if current_user_type != "admin":
            raise PermissionDeniedError("Only administrators can verify bank accounts")
        
        account = self.get_bank_account(account_id, current_user_type)
        account.verified = True
        account.verification_notes = verification_notes
        
        from datetime import datetime, timezone
        account.verification_date = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(account)
        
        logger.info(f"Verified bank account: {account.alias or account.account_number}")
        return account
    
    def get_platform_collection_accounts(self, active_only: bool = True) -> List[BankAccount]:
        """
        Get platform collection accounts for customer payments.
        
        Args:
            active_only: Only return active accounts
            
        Returns:
            List of platform collection accounts
        """
        query = self.db.query(BankAccount).filter(
            BankAccount.owner_type == BankAccountOwnerType.PLATFORM
        )
        
        if active_only:
            query = query.filter(BankAccount.active == True)
        
        return query.all()
    
    def get_reseller_payout_accounts(
        self, 
        reseller_id: int,
        active_only: bool = True
    ) -> List[BankAccount]:
        """
        Get reseller payout accounts.
        
        Args:
            reseller_id: Reseller ID
            active_only: Only return active accounts
            
        Returns:
            List of reseller payout accounts
        """
        query = self.db.query(BankAccount).filter(
            BankAccount.owner_type == BankAccountOwnerType.RESELLER,
            BankAccount.owner_id == reseller_id
        )
        
        if active_only:
            query = query.filter(BankAccount.active == True)
        
        return query.all()
    
    def get_bank_account_statistics(
        self,
        current_user_type: str = "admin",
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get bank account statistics.
        
        Args:
            current_user_type: Type of current user
            current_user_id: ID of current user
            
        Returns:
            Bank account statistics
        """
        if current_user_type == "admin":
            # Admin can see all statistics
            total_accounts = self.db.query(BankAccount).count()
            platform_accounts = self.db.query(BankAccount).filter(
                BankAccount.owner_type == BankAccountOwnerType.PLATFORM
            ).count()
            reseller_accounts = self.db.query(BankAccount).filter(
                BankAccount.owner_type == BankAccountOwnerType.RESELLER
            ).count()
            verified_accounts = self.db.query(BankAccount).filter(
                BankAccount.verified == True
            ).count()
            
            return {
                "total_accounts": total_accounts,
                "platform_accounts": platform_accounts,
                "reseller_accounts": reseller_accounts,
                "verified_accounts": verified_accounts,
                "unverified_accounts": total_accounts - verified_accounts
            }
        
        elif current_user_type == "reseller":
            # Reseller can only see their own statistics
            reseller_accounts = self.db.query(BankAccount).filter(
                BankAccount.owner_type == BankAccountOwnerType.RESELLER,
                BankAccount.owner_id == current_user_id
            ).count()
            
            return {
                "reseller_accounts": reseller_accounts
            }
        
        else:
            return {}
    
    def _can_access_account(
        self,
        account: BankAccount,
        current_user_type: str,
        current_user_id: Optional[int]
    ) -> bool:
        """
        Check if current user can access the bank account.
        
        Args:
            account: Bank account instance
            current_user_type: Type of current user
            current_user_id: ID of current user
            
        Returns:
            True if user can access the account
        """
        if current_user_type == "admin":
            return True
        
        if current_user_type == "reseller":
            # Resellers can access their own accounts and active platform accounts
            if account.owner_type == BankAccountOwnerType.RESELLER:
                return account.owner_id == current_user_id
            elif account.owner_type == BankAccountOwnerType.PLATFORM:
                return account.active
        
        if current_user_type == "customer":
            # Customers can only access active platform accounts
            return (account.owner_type == BankAccountOwnerType.PLATFORM and 
                   account.active)
        
        return False
