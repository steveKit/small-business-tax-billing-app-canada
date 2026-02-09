"""Invoice model."""
import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String, Text, Computed
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.payment import Payment


class InvoiceStatus(str, enum.Enum):
    """Invoice status enum."""
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class Invoice(Base, UUIDMixin, TimestampMixin):
    """Invoice record."""
    
    __tablename__ = "invoices"
    
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    billed_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    year_billed: Mapped[int] = mapped_column(
        Integer,
        Computed("EXTRACT(YEAR FROM billed_date)::INTEGER"),
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False)  # HST, GST+PST, etc.
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(
            InvoiceStatus,
            name="invoice_status",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=InvoiceStatus.DRAFT,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="invoices")
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="invoice",
        lazy="selectin",
    )
    
    @property
    def amount_paid(self) -> Decimal:
        """Calculate total amount paid for this invoice."""
        return sum((p.amount for p in self.payments), Decimal("0.00"))
    
    @property
    def amount_due(self) -> Decimal:
        """Calculate remaining amount due."""
        return self.total - self.amount_paid
    
    def to_dict(self) -> dict:
        """Convert to dictionary for backup/restore."""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "invoice_number": self.invoice_number,
            "description": self.description,
            "billed_date": self.billed_date.isoformat() if self.billed_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "year_billed": self.year_billed,
            "subtotal": str(self.subtotal),
            "tax_rate": str(self.tax_rate),
            "tax_type": self.tax_type,
            "tax_amount": str(self.tax_amount),
            "total": str(self.total),
            "status": self.status.value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
