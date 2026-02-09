"""Tax-related schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaxBracketBase(BaseModel):
    """Base schema for tax bracket."""
    
    min_income: Decimal = Field(..., ge=0)
    max_income: Optional[Decimal] = None
    rate: Decimal = Field(..., ge=0, le=1)


class FederalBracketCreate(TaxBracketBase):
    """Schema for creating a federal tax bracket."""
    
    year: int


class ProvincialBracketCreate(TaxBracketBase):
    """Schema for creating a provincial tax bracket."""
    
    year: int
    province: str


class TaxBracketUpdate(BaseModel):
    """Schema for updating a tax bracket."""
    
    min_income: Optional[Decimal] = None
    max_income: Optional[Decimal] = None
    rate: Optional[Decimal] = None


class TaxBracketResponse(BaseModel):
    """Schema for tax bracket response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[UUID] = None
    year: Optional[int] = None
    province: Optional[str] = None
    min_income: Decimal
    max_income: Optional[Decimal]
    rate: Decimal
    rate_percentage: float = Field(..., description="Rate as percentage (e.g., 15.0)")


class SalesTaxRateBase(BaseModel):
    """Base schema for sales tax rate."""
    
    gst_rate: Decimal = Field(default=Decimal("0.05"), ge=0, le=1)
    pst_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    hst_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    qst_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    tax_type: str = "HST"


class SalesTaxRateCreate(SalesTaxRateBase):
    """Schema for creating a sales tax rate."""
    
    province: str
    year: int


class SalesTaxRateUpdate(BaseModel):
    """Schema for updating a sales tax rate."""
    
    gst_rate: Optional[Decimal] = None
    pst_rate: Optional[Decimal] = None
    hst_rate: Optional[Decimal] = None
    qst_rate: Optional[Decimal] = None
    tax_type: Optional[str] = None


class SalesTaxRateResponse(BaseModel):
    """Schema for sales tax rate response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[UUID] = None
    province: str
    year: int
    gst_rate: Decimal
    pst_rate: Decimal
    hst_rate: Decimal
    qst_rate: Decimal
    tax_type: str
    total_rate: Decimal
    total_rate_percentage: float = Field(..., description="Total rate as percentage")


class TaxRatesResponse(BaseModel):
    """Schema for all tax rates for a year/province."""
    
    year: int
    province: str
    federal_brackets: list[TaxBracketResponse]
    provincial_brackets: list[TaxBracketResponse]
    sales_tax: Optional[SalesTaxRateResponse]


class TaxYearSettings(BaseModel):
    """Schema for tax year settings."""
    
    year: int
    presumed_annual_income: Decimal = Field(..., ge=0, description="Presumed annual income for tax calculations")
    notes: Optional[str] = None


class IncomeTaxCalculation(BaseModel):
    """Schema for income tax calculation details."""
    
    presumed_annual_income: Decimal
    ytd_income: Decimal
    projected_annual_income: Decimal
    federal_tax: Decimal
    provincial_tax: Decimal
    total_income_tax: Decimal
    effective_rate: float = Field(..., description="Effective tax rate as percentage")
    ytd_income_tax_holdback: Decimal


class TaxSummaryResponse(BaseModel):
    """Schema for tax summary/dashboard response."""
    
    year: int
    province: str
    
    # Revenue summary
    total_revenue_paid: Decimal = Field(..., description="Total subtotal from paid invoices")
    total_revenue_pending: Decimal = Field(..., description="Total subtotal from pending invoices")
    
    # HST/Sales tax
    total_hst_collected_paid: Decimal = Field(..., description="Total tax collected from paid invoices")
    total_hst_collected_pending: Decimal = Field(..., description="Total tax collected from pending invoices")
    hst_holdback: Decimal = Field(..., description="100% of HST collected on paid invoices")
    
    # Income tax
    income_tax_calculation: IncomeTaxCalculation
    income_tax_holdback: Decimal = Field(..., description="Estimated income tax to set aside")
    
    # Totals
    total_tax_reserve: Decimal = Field(..., description="Total amount to set aside for taxes")
    
    # Invoice counts
    paid_invoice_count: int
    pending_invoice_count: int
    
    # Timestamps
    calculated_at: datetime


class CopyTaxYearRequest(BaseModel):
    """Schema for copying tax rates from one year to another."""
    
    source_year: int
    target_year: int
    province: Optional[str] = None  # If None, copy all provinces
