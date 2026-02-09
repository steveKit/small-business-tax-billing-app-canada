"""Tax-related models."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class TaxYear(Base, UUIDMixin):
    """Tax year settings including presumed annual income."""
    
    __tablename__ = "tax_years"
    
    year: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    presumed_annual_income: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "year": self.year,
            "presumed_annual_income": str(self.presumed_annual_income),
            "notes": self.notes,
        }


class FederalTaxBracket(Base, UUIDMixin):
    """Federal income tax brackets."""
    
    __tablename__ = "federal_tax_brackets"
    
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    min_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    max_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))  # NULL = no limit
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "year": self.year,
            "min_income": str(self.min_income),
            "max_income": str(self.max_income) if self.max_income else None,
            "rate": str(self.rate),
        }


class ProvincialTaxBracket(Base, UUIDMixin):
    """Provincial income tax brackets."""
    
    __tablename__ = "provincial_tax_brackets"
    
    province: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    min_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    max_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))  # NULL = no limit
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "province": self.province,
            "year": self.year,
            "min_income": str(self.min_income),
            "max_income": str(self.max_income) if self.max_income else None,
            "rate": str(self.rate),
        }


class SalesTaxRate(Base, UUIDMixin):
    """Sales tax rates (HST/GST/PST) by province and year."""
    
    __tablename__ = "sales_tax_rates"
    
    province: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0500"))
    pst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"))
    hst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"))
    qst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"))
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False)  # HST, GST+PST, GST+QST, GST
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    @property
    def total_rate(self) -> Decimal:
        """Get the total sales tax rate."""
        if self.tax_type == "HST":
            return self.hst_rate
        elif self.tax_type == "GST+PST":
            return self.gst_rate + self.pst_rate
        elif self.tax_type == "GST+QST":
            return self.gst_rate + self.qst_rate
        else:  # GST only
            return self.gst_rate
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "province": self.province,
            "year": self.year,
            "gst_rate": str(self.gst_rate),
            "pst_rate": str(self.pst_rate),
            "hst_rate": str(self.hst_rate),
            "qst_rate": str(self.qst_rate),
            "tax_type": self.tax_type,
            "total_rate": str(self.total_rate),
        }
