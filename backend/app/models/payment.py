"""Payment model."""
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class PaymentMethod(str, enum.Enum):
    """Payment method enum."""
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    E_TRANSFER = "e_transfer"
    OTHER = "other"


class Payment(Base, UUIDMixin):
    """Payment record linked to an invoice."""
    
    __tablename__ = "payments"
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method", create_type=False),
        default=PaymentMethod.BANK_TRANSFER,
        nullable=False,
    )
    reference_number: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for backup/restore."""
        return {
            "id": str(self.id),
            "invoice_id": str(self.invoice_id),
            "amount": str(self.amount),
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment_method": self.payment_method.value,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
