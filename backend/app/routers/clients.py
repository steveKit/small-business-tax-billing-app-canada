"""Client API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.client import Client
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse,
)
from app.services.backup_service import BackupService

router = APIRouter(prefix="/v1/clients", tags=["Clients"])


@router.get("", response_model=ClientListResponse)
async def list_clients(
    active_only: bool = Query(True, description="Filter to active clients only"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: AsyncSession = Depends(get_db),
):
    """List all clients."""
    query = select(Client)
    
    if active_only:
        query = query.where(Client.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Client.name.ilike(search_term)) | (Client.email.ilike(search_term))
        )
    
    query = query.order_by(Client.name)
    
    result = await db.execute(query)
    clients = result.scalars().all()
    
    return ClientListResponse(
        items=[ClientResponse.model_validate(c) for c in clients],
        total=len(clients),
    )


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new client."""
    client = Client(**client_data.model_dump())
    db.add(client)
    await db.flush()
    await db.refresh(client)
    
    # Trigger auto-backup
    backup_service = BackupService(db)
    await backup_service.create_backup(backup_type="auto")
    
    return ClientResponse.model_validate(client)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a client by ID."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found",
        )
    
    return ClientResponse.model_validate(client)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a client."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found",
        )
    
    # Update only provided fields
    update_data = client_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    await db.flush()
    await db.refresh(client)
    
    # Trigger auto-backup
    backup_service = BackupService(db)
    await backup_service.create_backup(backup_type="auto")
    
    return ClientResponse.model_validate(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a client (soft delete - sets is_active to False)."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found",
        )
    
    # Soft delete
    client.is_active = False
    await db.flush()
    
    # Trigger auto-backup
    backup_service = BackupService(db)
    await backup_service.create_backup(backup_type="auto")
