"""Database backup and restore service using pg_dump/psql."""
import subprocess
from datetime import datetime
from typing import Optional

from app.config import get_settings


class BackupService:
    """Service for PostgreSQL backup and restore operations."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def _get_db_params(self) -> dict:
        """Extract database connection parameters."""
        # Parse DATABASE_URL: postgresql+asyncpg://user:pass@host:port/dbname
        url = self.settings.database_url
        # Remove the asyncpg part for pg_dump
        url = url.replace("postgresql+asyncpg://", "")
        
        # Parse: user:pass@host:port/dbname
        user_pass, host_db = url.split("@")
        user, password = user_pass.split(":")
        host_port, dbname = host_db.split("/")
        host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")
        
        return {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "dbname": dbname,
        }
    
    def create_backup(self) -> tuple[bytes, str]:
        """Create a PostgreSQL dump and return (sql_bytes, filename)."""
        params = self._get_db_params()
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"tax-billing-backup-{timestamp}.sql"
        
        # Run pg_dump
        env = {"PGPASSWORD": params["password"]}
        cmd = [
            "pg_dump",
            "-h", params["host"],
            "-p", params["port"],
            "-U", params["user"],
            "-d", params["dbname"],
            "--no-owner",
            "--no-acl",
            "--clean",
            "--if-exists",
        ]
        
        result = subprocess.run(cmd, capture_output=True, env={**env})
        
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {result.stderr.decode()}")
        
        return result.stdout, filename
    
    def restore_backup(self, sql_content: bytes) -> dict:
        """Restore database from SQL backup content."""
        params = self._get_db_params()
        
        # Run psql to restore
        env = {"PGPASSWORD": params["password"]}
        cmd = [
            "psql",
            "-h", params["host"],
            "-p", params["port"],
            "-U", params["user"],
            "-d", params["dbname"],
            "-q",  # Quiet mode
        ]
        
        result = subprocess.run(cmd, input=sql_content, capture_output=True, env={**env})
        
        if result.returncode != 0:
            error_msg = result.stderr.decode()
            # Filter out common non-fatal errors
            if "already exists" not in error_msg.lower():
                raise RuntimeError(f"psql restore failed: {error_msg}")
        
        return {"status": "success", "message": "Database restored successfully"}
