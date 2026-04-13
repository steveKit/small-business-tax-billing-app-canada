"""Invoice API endpoints."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus
from app.models.business_settings import BusinessSettings
from app.models.tax import SalesTaxRate
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceStatusUpdate,
    InvoiceResponse, InvoiceListResponse, ClientSummary, PaymentSummary,
)
from app.services.invoice_pdf import InvoicePDFService

router = APIRouter(prefix="/v1/invoices", tags=["Invoices"])


# Legal invoice status transitions via PATCH /v1/invoices/{id}/status.
# PAID is intentionally excluded — the only way into PAID is via payment
# records that satisfy the invoice total (see routers/payments.py), and
# the only way out is by deleting payments until the sum drops below total.
# DRAFT is excluded as a target — invoices move forward through the state
# machine, never backward.
# CANCELLED is terminal — no transitions out.
ALLOWED_STATUS_TRANSITIONS: dict[InvoiceStatus, set[InvoiceStatus]] = {
    InvoiceStatus.DRAFT: {InvoiceStatus.PENDING, InvoiceStatus.CANCELLED},
    InvoiceStatus.PENDING: {InvoiceStatus.CANCELLED},
}


async def generate_invoice_number(db: AsyncSession, year: int) -> str:
    result = await db.execute(select(func.count(Invoice.id)).where(Invoice.year_billed == year))
    count = result.scalar() or 0
    return f"INV-{year}-{count + 1:04d}"


def build_invoice_response(invoice: Invoice) -> InvoiceResponse:
    amount_paid = sum(p.amount for p in invoice.payments) if invoice.payments else Decimal("0.00")
    return InvoiceResponse(
        id=invoice.id, client_id=invoice.client_id, invoice_number=invoice.invoice_number,
        description=invoice.description, billed_date=invoice.billed_date, due_date=invoice.due_date,
        year_billed=invoice.year_billed, subtotal=invoice.subtotal, tax_rate=invoice.tax_rate,
        tax_type=invoice.tax_type, tax_amount=invoice.tax_amount, total=invoice.total,
        status=invoice.status, notes=invoice.notes, created_at=invoice.created_at, updated_at=invoice.updated_at,
        client=ClientSummary(id=invoice.client.id, name=invoice.client.name, email=invoice.client.email) if invoice.client else None,
        payments=[PaymentSummary(id=p.id, amount=p.amount, payment_date=p.payment_date, payment_method=p.payment_method.value) for p in invoice.payments],
        amount_paid=amount_paid, amount_due=invoice.total - amount_paid,
    )


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    year: Optional[int] = Query(None), client_id: Optional[UUID] = Query(None),
    status: Optional[InvoiceStatus] = Query(None), db: AsyncSession = Depends(get_db),
):
    query = select(Invoice).options(selectinload(Invoice.client), selectinload(Invoice.payments))
    if year: query = query.where(Invoice.year_billed == year)
    if client_id: query = query.where(Invoice.client_id == client_id)
    if status: query = query.where(Invoice.status == status)
    query = query.order_by(Invoice.billed_date.desc())
    result = await db.execute(query)
    invoices = result.scalars().all()
    return InvoiceListResponse(items=[build_invoice_response(inv) for inv in invoices], total=len(invoices))


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(invoice_data: InvoiceCreate, db: AsyncSession = Depends(get_db)):
    client_result = await db.execute(select(Client).where(Client.id == invoice_data.client_id))
    client = client_result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client with ID {invoice_data.client_id} not found")
    
    settings_result = await db.execute(select(BusinessSettings).limit(1))
    settings = settings_result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=400, detail="Business settings not configured")
    
    year = invoice_data.billed_date.year
    tax_result = await db.execute(select(SalesTaxRate).where(SalesTaxRate.province == settings.province, SalesTaxRate.year == year))
    sales_tax = tax_result.scalar_one_or_none()
    if not sales_tax:
        raise HTTPException(status_code=400, detail=f"Sales tax rate not found for {settings.province} in {year}")
    
    invoice_number = await generate_invoice_number(db, year)
    tax_rate = sales_tax.total_rate
    tax_amount = (invoice_data.subtotal * tax_rate).quantize(Decimal("0.01"))
    total = invoice_data.subtotal + tax_amount
    
    invoice = Invoice(
        client_id=invoice_data.client_id, invoice_number=invoice_number, description=invoice_data.description,
        billed_date=invoice_data.billed_date, due_date=invoice_data.due_date, subtotal=invoice_data.subtotal,
        tax_rate=tax_rate, tax_type=sales_tax.tax_type, tax_amount=tax_amount, total=total,
        status=InvoiceStatus.DRAFT, notes=invoice_data.notes,
    )
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)
    
    return InvoiceResponse(
        id=invoice.id, client_id=invoice.client_id, invoice_number=invoice.invoice_number,
        description=invoice.description, billed_date=invoice.billed_date, due_date=invoice.due_date,
        year_billed=invoice.year_billed, subtotal=invoice.subtotal, tax_rate=invoice.tax_rate,
        tax_type=invoice.tax_type, tax_amount=invoice.tax_amount, total=invoice.total,
        status=invoice.status, notes=invoice.notes, created_at=invoice.created_at, updated_at=invoice.updated_at,
        client=ClientSummary(id=client.id, name=client.name, email=client.email),
        payments=[], amount_paid=Decimal("0.00"), amount_due=invoice.total,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).options(selectinload(Invoice.client), selectinload(Invoice.payments)).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice with ID {invoice_id} not found")
    return build_invoice_response(invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: UUID, invoice_data: InvoiceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).options(selectinload(Invoice.client), selectinload(Invoice.payments)).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice with ID {invoice_id} not found")
    if invoice.status == InvoiceStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot update a cancelled invoice")
    
    update_data = invoice_data.model_dump(exclude_unset=True)
    if "subtotal" in update_data:
        update_data["tax_amount"] = (update_data["subtotal"] * invoice.tax_rate).quantize(Decimal("0.01"))
        update_data["total"] = update_data["subtotal"] + update_data["tax_amount"]
    
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    await db.flush()
    await db.refresh(invoice)
    return build_invoice_response(invoice)


@router.patch("/{invoice_id}/status", response_model=InvoiceResponse)
async def update_invoice_status(invoice_id: UUID, status_update: InvoiceStatusUpdate, db: AsyncSession = Depends(get_db)):
    """Update an invoice's status via a legal state-machine transition.

    Error contract:
    - 422: target is not in InvoiceStatusUpdate's Literal (rejected at
      request parsing — callers sending 'paid' or 'draft' land here).
    - 400 with PAID-specific detail: caller bypassed the schema and
      sent PAID at the handler level. Defense-in-depth; not reachable
      from a normal HTTP client but guards against programmatic misuse.
    - 400 with generic detail: target is syntactically valid but not
      reachable from the current status per ALLOWED_STATUS_TRANSITIONS
      (e.g., PENDING→PENDING, or anything out of CANCELLED/PAID state).
    - 404: invoice not found.

    The 422/400 split is intentional defense-in-depth between the
    pydantic schema and the handler whitelist. API clients should treat
    both as "illegal transition". Unifying to a single error shape is
    deferred to Milestone 2 when test infra lands.
    """
    result = await db.execute(select(Invoice).options(selectinload(Invoice.client), selectinload(Invoice.payments)).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice with ID {invoice_id} not found")

    target = status_update.status
    allowed = ALLOWED_STATUS_TRANSITIONS.get(invoice.status, set())
    if target not in allowed:
        if target == InvoiceStatus.PAID:
            raise HTTPException(
                status_code=400,
                detail="Invoice status cannot be set to PAID manually — record a payment instead.",
            )
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition invoice from {invoice.status.value} to {status_update.status.value}.",
        )

    invoice.status = target
    await db.flush()
    await db.refresh(invoice)
    return build_invoice_response(invoice)


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).options(selectinload(Invoice.client)).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice with ID {invoice_id} not found")
    
    settings_result = await db.execute(select(BusinessSettings).limit(1))
    settings = settings_result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=400, detail="Business settings not configured")
    
    pdf_service = InvoicePDFService()
    pdf_bytes = pdf_service.generate_pdf(invoice, invoice.client, settings)
    filename = pdf_service.get_filename(invoice)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
