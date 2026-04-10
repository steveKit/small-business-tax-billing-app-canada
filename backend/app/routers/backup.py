"""Backup and restore API endpoints."""
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.backup_service import BackupService

router = APIRouter(prefix="/v1/backup", tags=["Backup"])


@router.get("/download")
async def download_backup(db: AsyncSession = Depends(get_db)):
    """Create and download a PostgreSQL database backup."""
    try:
        service = BackupService(db)
        sql_bytes, filename = await service.create_backup(backup_type="manual")

        return Response(
            content=sql_bytes,
            media_type="application/sql",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Restore database from an uploaded SQL backup file."""
    if not file.filename.endswith(".sql"):
        raise HTTPException(status_code=400, detail="File must be a .sql backup file")

    try:
        sql_content = await file.read()
        service = BackupService(db)
        result = await service.restore_backup(sql_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
