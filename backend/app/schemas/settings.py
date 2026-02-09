"""Business settings schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BusinessSettingsBase(BaseModel):
    """Base business settings schema."""
    
    business_name: str = Field(..., min_length=1, max_length=255)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    province: str = Field(..., max_length=50, description="Province code (e.g., ON, BC)")
    postal_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    hst_number: Optional[str] = Field(None, max_length=50, description="GST/HST registration number")
    payment_terms: str = Field(default="Net 30", max_length=100)
    payment_instructions: Optional[str] = Field(None, description="Payment instructions for invoices")


class BusinessSettingsUpdate(BaseModel):
    """Schema for updating business settings."""
    
    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    hst_number: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[str] = Field(None, max_length=100)
    payment_instructions: Optional[str] = None
    backup_path: Optional[str] = Field(None, max_length=500)
    auto_backup_enabled: Optional[bool] = None
    backup_retention_count: Optional[int] = Field(None, ge=1, le=365)


class BusinessSettingsResponse(BusinessSettingsBase):
    """Schema for business settings response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    backup_path: Optional[str]
    auto_backup_enabled: bool
    backup_retention_count: int
    created_at: datetime
    updated_at: datetime


# Province options for dropdown
PROVINCE_OPTIONS = [
    {"code": "AB", "name": "Alberta"},
    {"code": "BC", "name": "British Columbia"},
    {"code": "MB", "name": "Manitoba"},
    {"code": "NB", "name": "New Brunswick"},
    {"code": "NL", "name": "Newfoundland and Labrador"},
    {"code": "NS", "name": "Nova Scotia"},
    {"code": "NT", "name": "Northwest Territories"},
    {"code": "NU", "name": "Nunavut"},
    {"code": "ON", "name": "Ontario"},
    {"code": "PE", "name": "Prince Edward Island"},
    {"code": "QC", "name": "Quebec"},
    {"code": "SK", "name": "Saskatchewan"},
    {"code": "YT", "name": "Yukon"},
]
