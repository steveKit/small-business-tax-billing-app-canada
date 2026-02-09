"""Backup and restore API endpoints."""
from fastapi import APIRouter, HTTPException, Response, UploadFile, File

from app.services.backup_service import BackupService

router = APIRouter(prefix="/v1/backup", tags=["Backup"])


@router.get("/download")
async def download_backup():
    """Create and download a PostgreSQL database backup."""
    try:
        service = BackupService()
        sql_bytes, filename = service.create_backup()
        
        return Response(
            content=sql_bytes,
            media_type="application/sql",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.post("/restore")
async def restore_backup(file: UploadFile = File(...)):
    """Restore database from an uploaded SQL backup file."""
    if not file.filename.endswith(".sql"):
        raise HTTPException(status_code=400, detail="File must be a .sql backup file")
    
    try:
        sql_content = await file.read()
        service = BackupService()
        result = service.restore_backup(sql_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
