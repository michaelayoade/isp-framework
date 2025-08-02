"""
Bank Account Schemas

Pydantic schemas for bank account API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class BankAccountOwnerTypeEnum(str, Enum):
    """Bank account owner type enum."""
    PLATFORM = "PLATFORM"
    RESELLER = "RESELLER"


class BankAccountCreateRequest(BaseModel):
    """Schema for creating a bank account."""
    owner_type: BankAccountOwnerTypeEnum
    owner_id: Optional[int] = Field(None, description="Required for reseller accounts")
    bank_name: str = Field(..., min_length=1, max_length=100)
    account_number: str = Field(..., min_length=1, max_length=50)
    account_name: str = Field(..., min_length=1, max_length=100)
    bank_code: Optional[str] = Field(None, max_length=20)
    branch_code: Optional[str] = Field(None, max_length=20)
    branch_name: Optional[str] = Field(None, max_length=100)
    currency: str = Field("USD", max_length=3)
    country: str = Field("NG", max_length=2)
    alias: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    active: bool = Field(True)
    
    @validator('owner_id')
    def validate_owner_id(cls, v, values):
        """Validate owner_id based on owner_type."""
        owner_type = values.get('owner_type')
        if owner_type == BankAccountOwnerTypeEnum.RESELLER and v is None:
            raise ValueError('owner_id is required for reseller accounts')
        if owner_type == BankAccountOwnerTypeEnum.PLATFORM and v is not None:
            raise ValueError('owner_id should not be set for platform accounts')
        return v


class BankAccountUpdateRequest(BaseModel):
    """Schema for updating a bank account."""
    bank_name: Optional[str] = Field(None, min_length=1, max_length=100)
    account_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bank_code: Optional[str] = Field(None, max_length=20)
    branch_code: Optional[str] = Field(None, max_length=20)
    branch_name: Optional[str] = Field(None, max_length=100)
    currency: Optional[str] = Field(None, max_length=3)
    country: Optional[str] = Field(None, max_length=2)
    alias: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    active: Optional[bool] = None


class BankAccountVerifyRequest(BaseModel):
    """Schema for verifying a bank account."""
    verification_notes: Optional[str] = Field(None, max_length=500)


class BankAccountResponse(BaseModel):
    """Schema for bank account response."""
    id: int
    owner_type: BankAccountOwnerTypeEnum
    owner_id: Optional[int]
    bank_name: str
    account_number: str
    account_name: str
    bank_code: Optional[str]
    branch_code: Optional[str]
    branch_name: Optional[str]
    currency: str
    country: str
    alias: Optional[str]
    description: Optional[str]
    active: bool
    verified: bool
    verification_date: Optional[datetime]
    verification_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    masked_account_number: str
    display_name: str
    
    class Config:
        from_attributes = True


class BankAccountListResponse(BaseModel):
    """Schema for bank account list response."""
    accounts: List[BankAccountResponse]
    total: int
    limit: int
    offset: int


class BankAccountStatsResponse(BaseModel):
    """Schema for bank account statistics response."""
    total_accounts: Optional[int] = None
    platform_accounts: Optional[int] = None
    reseller_accounts: Optional[int] = None
    verified_accounts: Optional[int] = None
    unverified_accounts: Optional[int] = None


class BankAccountListRequest(BaseModel):
    """Schema for bank account list query parameters."""
    owner_type: Optional[BankAccountOwnerTypeEnum] = None
    active_only: bool = Field(False)
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
