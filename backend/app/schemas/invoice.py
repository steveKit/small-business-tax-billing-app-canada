"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.models.invoice import InvoiceStatus


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    
    client_id: UUID = Field(..., description="Client UUID")
    description: str = Field(..., min_length=1, description="Description of work")
    billed_date: date = Field(..., description="Invoice date")
    due_date: date = Field(..., description="Payment due date")
    subtotal: Decimal = Field(..., ge=0, decimal_places=2, description="Subtotal before tax")
    notes: Optional[str] = Field(None, description="Additional notes")


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    
    # Tax rate and type will be automatically calculated from business settings
    pass


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    
    description: Optional[str] = Field(None, min_length=1)
    billed_date: Optional[date] = None
    due_date: Optional[date] = None
    subtotal: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    notes: Optional[str] = None


class InvoiceStatusUpdate(BaseModel):
    """Schema for updating invoice status.

    Only PENDING (send a draft) and CANCELLED are accepted as targets here.
    PAID is reachable only by recording a payment that satisfies the total
    (see routers/payments.py). DRAFT is forward-only — invoices never move
    backward through the state machine.
    """

    status: Literal[InvoiceStatus.PENDING, InvoiceStatus.CANCELLED] = Field(
        ..., description="New invoice status (PENDING to send, CANCELLED to cancel)"
    )


class PaymentSummary(BaseModel):
    """Summary of payments for an invoice."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    amount: Decimal
    payment_date: date
    payment_method: str


class ClientSummary(BaseModel):
    """Summary of client info for invoice response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    email: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    client_id: UUID
    invoice_number: str
    description: str
    billed_date: date
    due_date: date
    year_billed: int
    subtotal: Decimal
    tax_rate: Decimal
    tax_type: str
    tax_amount: Decimal
    total: Decimal
    status: InvoiceStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    client: Optional[ClientSummary] = None
    payments: list[PaymentSummary] = []
    amount_paid: Decimal = Decimal("0.00")
    amount_due: Decimal = Decimal("0.00")


class InvoiceListResponse(BaseModel):
    """Schema for list of invoices response."""
    
    items: list[InvoiceResponse]
    total: int


class InvoicePDFResponse(BaseModel):
    """Schema for invoice PDF response metadata."""
    
    invoice_id: UUID
    invoice_number: str
    filename: str
    content_type: str = "application/pdf"
