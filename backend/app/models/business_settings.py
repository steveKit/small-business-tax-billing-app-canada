"""Business settings model."""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class BusinessSettings(Base, UUIDMixin, TimestampMixin):
    """Business settings for invoices and tax calculations."""
    
    __tablename__ = "business_settings"
    
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    province: Mapped[str] = mapped_column(String(50), nullable=False, default="ON")
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    hst_number: Mapped[Optional[str]] = mapped_column(String(50))
    payment_terms: Mapped[str] = mapped_column(String(100), default="Net 30")
    payment_instructions: Mapped[Optional[str]] = mapped_column(Text)
    backup_path: Mapped[Optional[str]] = mapped_column(String(500))
    auto_backup_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    backup_retention_count: Mapped[int] = mapped_column(Integer, default=30)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for backup/restore."""
        return {
            "id": str(self.id),
            "business_name": self.business_name,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "province": self.province,
            "postal_code": self.postal_code,
            "phone": self.phone,
            "email": self.email,
            "hst_number": self.hst_number,
            "payment_terms": self.payment_terms,
            "payment_instructions": self.payment_instructions,
            "backup_path": self.backup_path,
            "auto_backup_enabled": self.auto_backup_enabled,
            "backup_retention_count": self.backup_retention_count,
        }
