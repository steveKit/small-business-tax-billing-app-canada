"""Tax API endpoints."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.business_settings import BusinessSettings
from app.models.tax import TaxYear, FederalTaxBracket, ProvincialTaxBracket, SalesTaxRate
from app.schemas.tax import (
    TaxSummaryResponse,
    TaxRatesResponse,
    TaxYearSettings,
    TaxBracketResponse,
    FederalBracketCreate,
    ProvincialBracketCreate,
    TaxBracketUpdate,
    SalesTaxRateResponse,
    SalesTaxRateCreate,
    SalesTaxRateUpdate,
)
from app.services.tax_calculator import TaxCalculatorService

router = APIRouter(prefix="/v1/tax", tags=["Tax"])


@router.get("/summary", response_model=TaxSummaryResponse)
async def get_tax_summary(
    year: Optional[int] = Query(None, description="Tax year (defaults to current year)"),
    db: AsyncSession = Depends(get_db),
):
    """Get tax summary/dashboard for a year."""
    if year is None:
        year = datetime.now().year
    
    tax_service = TaxCalculatorService(db)
    return await tax_service.get_tax_summary(year)


@router.get("/rates/{year}", response_model=TaxRatesResponse)
async def get_tax_rates(
    year: int,
    province: Optional[str] = Query(None, description="Province code"),
    db: AsyncSession = Depends(get_db),
):
    """Get all tax rates for a year and province."""
    if province is None:
        settings_result = await db.execute(select(BusinessSettings).limit(1))
        settings = settings_result.scalar_one_or_none()
        province = settings.province if settings else "ON"
    
    tax_service = TaxCalculatorService(db)
    return await tax_service.get_tax_rates(year, province)


@router.get("/year-settings/{year}", response_model=TaxYearSettings)
async def get_tax_year_settings(year: int, db: AsyncSession = Depends(get_db)):
    """Get tax year settings."""
    result = await db.execute(select(TaxYear).where(TaxYear.year == year))
    tax_year = result.scalar_one_or_none()
    
    if not tax_year:
        raise HTTPException(status_code=404, detail=f"Tax year settings for {year} not found")
    
    return TaxYearSettings(year=tax_year.year, presumed_annual_income=tax_year.presumed_annual_income, notes=tax_year.notes)


@router.put("/year-settings/{year}", response_model=TaxYearSettings)
async def update_tax_year_settings(year: int, settings: TaxYearSettings, db: AsyncSession = Depends(get_db)):
    """Update or create tax year settings."""
    result = await db.execute(select(TaxYear).where(TaxYear.year == year))
    tax_year = result.scalar_one_or_none()
    
    if tax_year:
        tax_year.presumed_annual_income = settings.presumed_annual_income
        tax_year.notes = settings.notes
    else:
        tax_year = TaxYear(year=year, presumed_annual_income=settings.presumed_annual_income, notes=settings.notes)
        db.add(tax_year)
    
    await db.flush()
    await db.refresh(tax_year)
    return TaxYearSettings(year=tax_year.year, presumed_annual_income=tax_year.presumed_annual_income, notes=tax_year.notes)


# ==================== Federal Brackets CRUD ====================

@router.post("/federal-brackets", response_model=TaxBracketResponse, status_code=201)
async def create_federal_bracket(data: FederalBracketCreate, db: AsyncSession = Depends(get_db)):
    """Create a new federal tax bracket."""
    bracket = FederalTaxBracket(year=data.year, min_income=data.min_income, max_income=data.max_income, rate=data.rate)
    db.add(bracket)
    await db.flush()
    await db.refresh(bracket)
    return TaxBracketResponse(id=bracket.id, year=bracket.year, min_income=bracket.min_income, max_income=bracket.max_income, rate=bracket.rate, rate_percentage=float(bracket.rate * 100))


@router.put("/federal-brackets/{bracket_id}", response_model=TaxBracketResponse)
async def update_federal_bracket(bracket_id: UUID, data: TaxBracketUpdate, db: AsyncSession = Depends(get_db)):
    """Update a federal tax bracket."""
    result = await db.execute(select(FederalTaxBracket).where(FederalTaxBracket.id == bracket_id))
    bracket = result.scalar_one_or_none()
    if not bracket:
        raise HTTPException(status_code=404, detail="Federal bracket not found")
    
    if data.min_income is not None:
        bracket.min_income = data.min_income
    if data.max_income is not None:
        bracket.max_income = data.max_income
    if data.rate is not None:
        bracket.rate = data.rate
    
    await db.flush()
    await db.refresh(bracket)
    return TaxBracketResponse(id=bracket.id, year=bracket.year, min_income=bracket.min_income, max_income=bracket.max_income, rate=bracket.rate, rate_percentage=float(bracket.rate * 100))


@router.delete("/federal-brackets/{bracket_id}", status_code=204)
async def delete_federal_bracket(bracket_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a federal tax bracket."""
    result = await db.execute(select(FederalTaxBracket).where(FederalTaxBracket.id == bracket_id))
    bracket = result.scalar_one_or_none()
    if not bracket:
        raise HTTPException(status_code=404, detail="Federal bracket not found")
    await db.delete(bracket)
    await db.flush()


# ==================== Provincial Brackets CRUD ====================

@router.post("/provincial-brackets", response_model=TaxBracketResponse, status_code=201)
async def create_provincial_bracket(data: ProvincialBracketCreate, db: AsyncSession = Depends(get_db)):
    """Create a new provincial tax bracket."""
    bracket = ProvincialTaxBracket(province=data.province, year=data.year, min_income=data.min_income, max_income=data.max_income, rate=data.rate)
    db.add(bracket)
    await db.flush()
    await db.refresh(bracket)
    return TaxBracketResponse(id=bracket.id, year=bracket.year, province=bracket.province, min_income=bracket.min_income, max_income=bracket.max_income, rate=bracket.rate, rate_percentage=float(bracket.rate * 100))


@router.put("/provincial-brackets/{bracket_id}", response_model=TaxBracketResponse)
async def update_provincial_bracket(bracket_id: UUID, data: TaxBracketUpdate, db: AsyncSession = Depends(get_db)):
    """Update a provincial tax bracket."""
    result = await db.execute(select(ProvincialTaxBracket).where(ProvincialTaxBracket.id == bracket_id))
    bracket = result.scalar_one_or_none()
    if not bracket:
        raise HTTPException(status_code=404, detail="Provincial bracket not found")
    
    if data.min_income is not None:
        bracket.min_income = data.min_income
    if data.max_income is not None:
        bracket.max_income = data.max_income
    if data.rate is not None:
        bracket.rate = data.rate
    
    await db.flush()
    await db.refresh(bracket)
    return TaxBracketResponse(id=bracket.id, year=bracket.year, province=bracket.province, min_income=bracket.min_income, max_income=bracket.max_income, rate=bracket.rate, rate_percentage=float(bracket.rate * 100))


@router.delete("/provincial-brackets/{bracket_id}", status_code=204)
async def delete_provincial_bracket(bracket_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a provincial tax bracket."""
    result = await db.execute(select(ProvincialTaxBracket).where(ProvincialTaxBracket.id == bracket_id))
    bracket = result.scalar_one_or_none()
    if not bracket:
        raise HTTPException(status_code=404, detail="Provincial bracket not found")
    await db.delete(bracket)
    await db.flush()


# ==================== Sales Tax Rate CRUD ====================

@router.post("/sales-rates", response_model=SalesTaxRateResponse, status_code=201)
async def create_sales_rate(data: SalesTaxRateCreate, db: AsyncSession = Depends(get_db)):
    """Create a new sales tax rate."""
    rate = SalesTaxRate(province=data.province, year=data.year, gst_rate=data.gst_rate, pst_rate=data.pst_rate, hst_rate=data.hst_rate, qst_rate=data.qst_rate, tax_type=data.tax_type)
    db.add(rate)
    await db.flush()
    await db.refresh(rate)
    return SalesTaxRateResponse(id=rate.id, province=rate.province, year=rate.year, gst_rate=rate.gst_rate, pst_rate=rate.pst_rate, hst_rate=rate.hst_rate, qst_rate=rate.qst_rate, tax_type=rate.tax_type, total_rate=rate.total_rate, total_rate_percentage=float(rate.total_rate * 100))


@router.put("/sales-rates/{rate_id}", response_model=SalesTaxRateResponse)
async def update_sales_rate(rate_id: UUID, data: SalesTaxRateUpdate, db: AsyncSession = Depends(get_db)):
    """Update a sales tax rate."""
    result = await db.execute(select(SalesTaxRate).where(SalesTaxRate.id == rate_id))
    rate = result.scalar_one_or_none()
    if not rate:
        raise HTTPException(status_code=404, detail="Sales rate not found")
    
    if data.gst_rate is not None:
        rate.gst_rate = data.gst_rate
    if data.pst_rate is not None:
        rate.pst_rate = data.pst_rate
    if data.hst_rate is not None:
        rate.hst_rate = data.hst_rate
    if data.qst_rate is not None:
        rate.qst_rate = data.qst_rate
    if data.tax_type is not None:
        rate.tax_type = data.tax_type
    
    await db.flush()
    await db.refresh(rate)
    return SalesTaxRateResponse(id=rate.id, province=rate.province, year=rate.year, gst_rate=rate.gst_rate, pst_rate=rate.pst_rate, hst_rate=rate.hst_rate, qst_rate=rate.qst_rate, tax_type=rate.tax_type, total_rate=rate.total_rate, total_rate_percentage=float(rate.total_rate * 100))
