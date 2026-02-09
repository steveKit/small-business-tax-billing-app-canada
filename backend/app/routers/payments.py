"""Payment API endpoints."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
    InvoiceSummary,
)
from app.services.backup_service import BackupService

router = APIRouter(prefix="/v1/payments", tags=["Payments"])


@router.get("", response_model=PaymentListResponse)
async def list_payments(
    invoice_id: Optional[UUID] = Query(None, description="Filter by invoice"),
    year: Optional[int] = Query(None, description="Filter by payment year"),
    db: AsyncSession = Depends(get_db),
):
    """List all payments."""
    query = select(Payment).options(selectinload(Payment.invoice))
    
    if invoice_id:
        query = query.where(Payment.invoice_id == invoice_id)
    
    if year:
        from sqlalchemy import extract
        query = query.where(extract("year", Payment.payment_date) == year)
    
    query = query.order_by(Payment.payment_date.desc())
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    items = []
    for payment in payments:
        items.append(PaymentResponse(
            id=payment.id,
            invoice_id=payment.invoice_id,
            amount=payment.amount,
            payment_date=payment.payment_date,
            payment_method=payment.payment_method,
            reference_number=payment.reference_number,
            notes=payment.notes,
            created_at=payment.created_at,
            invoice=InvoiceSummary(
                id=payment.invoice.id,
                invoice_number=payment.invoice.invoice_number,
                total=payment.invoice.total,
                status=payment.invoice.status.value,
            ) if payment.invoice else None,
        ))
    
    return PaymentListResponse(items=items, total=len(items))


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Record a new payment."""
    # Verify invoice exists and get it with payments
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.payments))
        .where(Invoice.id == payment_data.invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {payment_data.invoice_id} not found",
        )
    
    # Check invoice status
    if invoice.status == InvoiceStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add payment to a cancelled invoice",
        )
    
    if invoice.status == InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add payment to a draft invoice. Please send the invoice first.",
        )
    
    # Calculate current amount paid
    current_paid = sum(p.amount for p in invoice.payments)
    remaining = invoice.total - current_paid
    
    # Check if payment exceeds remaining amount
    if payment_data.amount > remaining:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount ${payment_data.amount} exceeds remaining balance ${remaining}",
        )
    
    # Create payment
    payment = Payment(**payment_data.model_dump())
    db.add(payment)
    await db.flush()
    
    # Update invoice status if fully paid
    new_paid = current_paid + payment_data.amount
    if new_paid >= invoice.total:
        invoice.status = InvoiceStatus.PAID
    
    await db.refresh(payment)
    
    # Trigger auto-backup
    backup_service = BackupService(db)
    await backup_service.create_backup(backup_type="auto")
    
    return PaymentResponse(
        id=payment.id,
        invoice_id=payment.invoice_id,
        amount=payment.amount,
        payment_date=payment.payment_date,
        payment_method=payment.payment_method,
        reference_number=payment.reference_number,
        notes=payment.notes,
        created_at=payment.created_at,
        invoice=InvoiceSummary(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            total=invoice.total,
            status=invoice.status.value,
        ),
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a payment by ID."""
    result = await db.execute(
        select(Payment)
        .options(selectinload(Payment.invoice))
        .where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found",
        )
    
    return PaymentResponse(
        id=payment.id,
        invoice_id=payment.invoice_id,
        amount=payment.amount,
        payment_date=payment.payment_date,
        payment_method=payment.payment_method,
        reference_number=payment.reference_number,
        notes=payment.notes,
        created_at=payment.created_at,
        invoice=InvoiceSummary(
            id=payment.invoice.id,
            invoice_number=payment.invoice.invoice_number,
            total=payment.invoice.total,
            status=payment.invoice.status.value,
        ) if payment.invoice else None,
    )


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a payment."""
    result = await db.execute(
        select(Payment)
        .options(selectinload(Payment.invoice))
        .where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found",
        )
    
    # Get invoice to update status
    invoice = payment.invoice
    
    # Delete the payment
    await db.delete(payment)
    await db.flush()
    
    # Recalculate invoice status
    if invoice:
        remaining_result = await db.execute(
            select(Payment).where(Payment.invoice_id == invoice.id)
        )
        remaining_payments = remaining_result.scalars().all()
        total_paid = sum(p.amount for p in remaining_payments)
        
        if total_paid < invoice.total and invoice.status == InvoiceStatus.PAID:
            invoice.status = InvoiceStatus.PENDING
    
    # Trigger auto-backup
    backup_service = BackupService(db)
    await backup_service.create_backup(backup_type="auto")
