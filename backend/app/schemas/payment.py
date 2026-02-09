"""Payment schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod


class PaymentBase(BaseModel):
    """Base payment schema."""
    
    invoice_id: UUID = Field(..., description="Invoice UUID")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Payment amount")
    payment_date: date = Field(..., description="Date payment was received")
    payment_method: PaymentMethod = Field(
        default=PaymentMethod.BANK_TRANSFER,
        description="Payment method",
    )
    reference_number: Optional[str] = Field(None, max_length=100, description="Reference/check number")
    notes: Optional[str] = Field(None, description="Additional notes")


class PaymentCreate(PaymentBase):
    """Schema for creating a payment."""
    pass


class InvoiceSummary(BaseModel):
    """Summary of invoice info for payment response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_number: str
    total: Decimal
    status: str


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    amount: Decimal
    payment_date: date
    payment_method: PaymentMethod
    reference_number: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    # Include invoice summary
    invoice: Optional[InvoiceSummary] = None


class PaymentListResponse(BaseModel):
    """Schema for list of payments response."""
    
    items: list[PaymentResponse]
    total: int
