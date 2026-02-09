"""Business settings API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.business_settings import BusinessSettings
from app.schemas.settings import (
    BusinessSettingsUpdate,
    BusinessSettingsResponse,
    PROVINCE_OPTIONS,
)

router = APIRouter(prefix="/v1/settings", tags=["Settings"])


@router.get("", response_model=BusinessSettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
):
    """Get business settings."""
    result = await db.execute(select(BusinessSettings).limit(1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business settings not found. Please configure settings first.",
        )
    
    return BusinessSettingsResponse.model_validate(settings)


@router.put("", response_model=BusinessSettingsResponse)
async def update_settings(
    settings_data: BusinessSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update business settings."""
    result = await db.execute(select(BusinessSettings).limit(1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create new settings if none exist
        settings = BusinessSettings(
            business_name=settings_data.business_name or "My Business",
            province=settings_data.province or "ON",
        )
        db.add(settings)
    
    # Update only provided fields
    update_data = settings_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(settings, field, value)
    
    await db.flush()
    await db.refresh(settings)
    
    return BusinessSettingsResponse.model_validate(settings)


@router.get("/provinces")
async def get_provinces():
    """Get list of provinces for dropdown."""
    return {"provinces": PROVINCE_OPTIONS}
