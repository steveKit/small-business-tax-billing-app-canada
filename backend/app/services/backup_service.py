"""Database backup and restore service using pg_dump/psql."""
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.backup import BackupLog


class BackupService:
    """Service for PostgreSQL backup and restore operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()

    def _get_db_params(self) -> dict:
        """Extract database connection parameters from DATABASE_URL."""
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

    async def create_backup(
        self,
        backup_type: Literal["auto", "manual"] = "manual",
    ) -> tuple[bytes, str]:
        """Create a PostgreSQL dump, persist to disk, log it, and return (sql_bytes, filename)."""
        params = self._get_db_params()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
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

        sql_bytes = result.stdout

        # Write dump to disk under settings.default_backup_path
        backup_dir = Path(self.settings.default_backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)
        file_path = (backup_dir / filename).resolve()
        file_path.write_bytes(sql_bytes)

        # Record the backup in backup_logs
        log_entry = BackupLog(
            filename=filename,
            file_path=str(file_path),
            file_size_bytes=len(sql_bytes),
            backup_type=backup_type,
        )
        self.db.add(log_entry)
        await self.db.flush()
        await self.db.commit()

        return sql_bytes, filename

    async def restore_backup(self, sql_content: bytes) -> dict:
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
