"""Backup and restore schemas."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BackupData(BaseModel):
    """Schema for backup data content."""
    
    business_settings: dict[str, Any]
    clients: list[dict[str, Any]]
    invoices: list[dict[str, Any]]
    payments: list[dict[str, Any]]
    tax_years: list[dict[str, Any]]


class BackupMetadata(BaseModel):
    """Schema for backup metadata."""
    
    backup_version: str = "1.0"
    app_version: str
    created_at: datetime
    record_counts: dict[str, int]


class BackupResponse(BaseModel):
    """Schema for backup response."""
    
    id: UUID
    filename: str
    file_path: str
    file_size_bytes: Optional[int]
    backup_type: str
    created_at: datetime


class BackupListResponse(BaseModel):
    """Schema for list of backups response."""
    
    items: list[BackupResponse]
    total: int


class RestoreRequest(BaseModel):
    """Schema for restore request."""
    
    backup_data: dict[str, Any] = Field(..., description="The backup JSON data to restore")
    merge: bool = Field(default=False, description="If true, merge with existing data; if false, replace")


class RestoreResponse(BaseModel):
    """Schema for restore response."""
    
    success: bool
    message: str
    records_restored: dict[str, int]
    backup_created_before_restore: Optional[str] = None


class BackupStatusResponse(BaseModel):
    """Schema for backup status response."""
    
    last_backup: Optional[BackupResponse]
    auto_backup_enabled: bool
    backup_path: Optional[str]
    total_backups: int
