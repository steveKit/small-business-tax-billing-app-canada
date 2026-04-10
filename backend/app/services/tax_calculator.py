"""Tax calculation service."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice, InvoiceStatus
from app.models.tax import FederalTaxBracket, ProvincialTaxBracket, SalesTaxRate, TaxYear
from app.models.business_settings import BusinessSettings
from app.schemas.tax import (
    IncomeTaxCalculation,
    TaxSummaryResponse,
    TaxBracketResponse,
    SalesTaxRateResponse,
    TaxRatesResponse,
)


class TaxCalculatorService:
    """Service for calculating tax obligations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_sales_tax_rate(self, province: str, year: int) -> Optional[SalesTaxRate]:
        """Get sales tax rate for a province and year."""
        result = await self.db.execute(
            select(SalesTaxRate).where(
                SalesTaxRate.province == province,
                SalesTaxRate.year == year,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_federal_brackets(self, year: int) -> list[FederalTaxBracket]:
        """Get federal tax brackets for a year."""
        result = await self.db.execute(
            select(FederalTaxBracket)
            .where(FederalTaxBracket.year == year)
            .order_by(FederalTaxBracket.min_income)
        )
        return list(result.scalars().all())
    
    async def get_provincial_brackets(self, province: str, year: int) -> list[ProvincialTaxBracket]:
        """Get provincial tax brackets for a province and year."""
        result = await self.db.execute(
            select(ProvincialTaxBracket)
            .where(
                ProvincialTaxBracket.province == province,
                ProvincialTaxBracket.year == year,
            )
            .order_by(ProvincialTaxBracket.min_income)
        )
        return list(result.scalars().all())
    
    async def get_tax_year_settings(self, year: int) -> Optional[TaxYear]:
        """Get tax year settings."""
        result = await self.db.execute(
            select(TaxYear).where(TaxYear.year == year)
        )
        return result.scalar_one_or_none()
    
    def calculate_bracket_tax(
        self,
        income: Decimal,
        brackets: list[FederalTaxBracket] | list[ProvincialTaxBracket],
    ) -> Decimal:
        """Calculate tax based on progressive tax brackets."""
        total_tax = Decimal("0.00")
        
        for bracket in brackets:
            if income <= bracket.min_income:
                break
            
            bracket_min = bracket.min_income
            bracket_max = bracket.max_income if bracket.max_income else income
            
            taxable_in_bracket = min(income, bracket_max) - bracket_min
            if taxable_in_bracket > 0:
                total_tax += taxable_in_bracket * bracket.rate
        
        return total_tax.quantize(Decimal("0.01"))
    
    async def calculate_income_tax(
        self,
        year: int,
        province: str,
        ytd_income: Decimal,
        presumed_annual_income: Optional[Decimal] = None,
    ) -> IncomeTaxCalculation:
        """Calculate income tax obligation."""
        federal_brackets = await self.get_federal_brackets(year)
        provincial_brackets = await self.get_provincial_brackets(province, year)
        
        if presumed_annual_income is None:
            tax_year = await self.get_tax_year_settings(year)
            presumed_annual_income = tax_year.presumed_annual_income if tax_year else Decimal("0.00")
        
        current_month = datetime.now().month
        annualized_ytd = ytd_income * Decimal("12") / Decimal(str(current_month))
        projected_annual_income = max(presumed_annual_income, annualized_ytd)
        
        federal_tax = self.calculate_bracket_tax(projected_annual_income, federal_brackets)
        provincial_tax = self.calculate_bracket_tax(projected_annual_income, provincial_brackets)
        total_income_tax = federal_tax + provincial_tax
        
        effective_rate = float(total_income_tax / projected_annual_income * 100) if projected_annual_income > 0 else 0.0
        
        if projected_annual_income > 0:
            ytd_holdback = total_income_tax * (ytd_income / projected_annual_income)
        else:
            ytd_holdback = Decimal("0.00")
        
        return IncomeTaxCalculation(
            presumed_annual_income=presumed_annual_income,
            ytd_income=ytd_income,
            projected_annual_income=projected_annual_income.quantize(Decimal("0.01")),
            federal_tax=federal_tax,
            provincial_tax=provincial_tax,
            total_income_tax=total_income_tax,
            effective_rate=round(effective_rate, 2),
            ytd_income_tax_holdback=ytd_holdback.quantize(Decimal("0.01")),
        )
    
    async def get_tax_summary(self, year: int) -> TaxSummaryResponse:
        """Get complete tax summary for a year."""
        settings_result = await self.db.execute(select(BusinessSettings).limit(1))
        settings = settings_result.scalar_one_or_none()
        province = settings.province if settings else "ON"
        
        paid_result = await self.db.execute(
            select(
                func.count(Invoice.id).label("count"),
                func.coalesce(func.sum(Invoice.subtotal), 0).label("subtotal"),
                func.coalesce(func.sum(Invoice.tax_amount), 0).label("tax_amount"),
            ).where(
                Invoice.year_billed == year,
                Invoice.status == InvoiceStatus.PAID,
            )
        )
        paid_row = paid_result.one()
        
        pending_result = await self.db.execute(
            select(
                func.count(Invoice.id).label("count"),
                func.coalesce(func.sum(Invoice.subtotal), 0).label("subtotal"),
                func.coalesce(func.sum(Invoice.tax_amount), 0).label("tax_amount"),
            ).where(
                Invoice.year_billed == year,
                Invoice.status == InvoiceStatus.PENDING,
            )
        )
        pending_row = pending_result.one()
        
        ytd_income = Decimal(str(paid_row.subtotal))
        income_tax_calc = await self.calculate_income_tax(year, province, ytd_income)
        
        hst_holdback = Decimal(str(paid_row.tax_amount))
        total_tax_reserve = hst_holdback + income_tax_calc.ytd_income_tax_holdback
        
        return TaxSummaryResponse(
            year=year,
            province=province,
            total_revenue_paid=Decimal(str(paid_row.subtotal)),
            total_revenue_pending=Decimal(str(pending_row.subtotal)),
            total_hst_collected_paid=Decimal(str(paid_row.tax_amount)),
            total_hst_collected_pending=Decimal(str(pending_row.tax_amount)),
            hst_holdback=hst_holdback,
            income_tax_calculation=income_tax_calc,
            income_tax_holdback=income_tax_calc.ytd_income_tax_holdback,
            total_tax_reserve=total_tax_reserve,
            paid_invoice_count=paid_row.count,
            pending_invoice_count=pending_row.count,
            calculated_at=datetime.now(timezone.utc),
        )
    
    async def get_tax_rates(self, year: int, province: str) -> TaxRatesResponse:
        """Get all tax rates for a year and province."""
        federal_brackets = await self.get_federal_brackets(year)
        provincial_brackets = await self.get_provincial_brackets(province, year)
        sales_tax = await self.get_sales_tax_rate(province, year)
        
        return TaxRatesResponse(
            year=year,
            province=province,
            federal_brackets=[
                TaxBracketResponse(
                    id=b.id,
                    year=b.year,
                    min_income=b.min_income,
                    max_income=b.max_income,
                    rate=b.rate,
                    rate_percentage=float(b.rate * 100),
                )
                for b in federal_brackets
            ],
            provincial_brackets=[
                TaxBracketResponse(
                    id=b.id,
                    year=b.year,
                    province=b.province,
                    min_income=b.min_income,
                    max_income=b.max_income,
                    rate=b.rate,
                    rate_percentage=float(b.rate * 100),
                )
                for b in provincial_brackets
            ],
            sales_tax=SalesTaxRateResponse(
                id=sales_tax.id,
                province=sales_tax.province,
                year=sales_tax.year,
                gst_rate=sales_tax.gst_rate,
                pst_rate=sales_tax.pst_rate,
                hst_rate=sales_tax.hst_rate,
                qst_rate=sales_tax.qst_rate,
                tax_type=sales_tax.tax_type,
                total_rate=sales_tax.total_rate,
                total_rate_percentage=float(sales_tax.total_rate * 100),
            ) if sales_tax else None,
        )
