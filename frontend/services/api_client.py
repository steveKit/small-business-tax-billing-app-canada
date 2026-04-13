"""API client for communicating with the backend."""
from typing import Optional
import httpx


class APIClient:
    """HTTP client for the Tax Billing API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)
    
    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"
    
    # ==================== Clients ====================
    
    def get_clients(self, active_only: bool = True) -> dict:
        response = self.client.get(self._url("/v1/clients"), params={"active_only": active_only})
        response.raise_for_status()
        return response.json()
    
    def get_client(self, client_id: str) -> dict:
        response = self.client.get(self._url(f"/v1/clients/{client_id}"))
        response.raise_for_status()
        return response.json()
    
    def create_client(self, data: dict) -> dict:
        response = self.client.post(self._url("/v1/clients"), json=data)
        response.raise_for_status()
        return response.json()
    
    def update_client(self, client_id: str, data: dict) -> dict:
        response = self.client.put(self._url(f"/v1/clients/{client_id}"), json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_client(self, client_id: str) -> None:
        response = self.client.delete(self._url(f"/v1/clients/{client_id}"))
        response.raise_for_status()
    
    # ==================== Invoices ====================
    
    def get_invoices(self, year: Optional[int] = None, client_id: Optional[str] = None, status: Optional[str] = None) -> dict:
        params = {}
        if year: params["year"] = year
        if client_id: params["client_id"] = client_id
        if status: params["status"] = status
        response = self.client.get(self._url("/v1/invoices"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_invoice(self, invoice_id: str) -> dict:
        response = self.client.get(self._url(f"/v1/invoices/{invoice_id}"))
        response.raise_for_status()
        return response.json()
    
    def create_invoice(self, data: dict) -> dict:
        response = self.client.post(self._url("/v1/invoices"), json=data)
        response.raise_for_status()
        return response.json()
    
    def update_invoice(self, invoice_id: str, data: dict) -> dict:
        response = self.client.put(self._url(f"/v1/invoices/{invoice_id}"), json=data)
        response.raise_for_status()
        return response.json()
    
    def update_invoice_status(self, invoice_id: str, status: str) -> dict:
        response = self.client.patch(self._url(f"/v1/invoices/{invoice_id}/status"), json={"status": status})
        response.raise_for_status()
        return response.json()
    
    def get_invoice_pdf(self, invoice_id: str) -> bytes:
        response = self.client.get(self._url(f"/v1/invoices/{invoice_id}/pdf"))
        response.raise_for_status()
        return response.content
    
    # ==================== Payments ====================
    
    def get_payments(self, invoice_id: Optional[str] = None, year: Optional[int] = None) -> dict:
        params = {}
        if invoice_id: params["invoice_id"] = invoice_id
        if year: params["year"] = year
        response = self.client.get(self._url("/v1/payments"), params=params)
        response.raise_for_status()
        return response.json()
    
    def create_payment(self, data: dict) -> dict:
        response = self.client.post(self._url("/v1/payments"), json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_payment(self, payment_id: str) -> None:
        response = self.client.delete(self._url(f"/v1/payments/{payment_id}"))
        response.raise_for_status()
    
    # ==================== Tax ====================
    
    def get_tax_summary(self, year: Optional[int] = None) -> dict:
        params = {}
        if year: params["year"] = year
        response = self.client.get(self._url("/v1/tax/summary"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_tax_rates(self, year: int, province: Optional[str] = None) -> dict:
        params = {}
        if province: params["province"] = province
        response = self.client.get(self._url(f"/v1/tax/rates/{year}"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_tax_year_settings(self, year: int) -> dict:
        response = self.client.get(self._url(f"/v1/tax/year-settings/{year}"))
        response.raise_for_status()
        return response.json()
    
    def update_tax_year_settings(self, year: int, data: dict) -> dict:
        response = self.client.put(self._url(f"/v1/tax/year-settings/{year}"), json=data)
        response.raise_for_status()
        return response.json()
    
    def create_federal_bracket(self, data: dict) -> dict:
        response = self.client.post(self._url("/v1/tax/federal-brackets"), json=data)
        response.raise_for_status()
        return response.json()
    
    def update_federal_bracket(self, bracket_id: str, data: dict) -> dict:
        response = self.client.put(self._url(f"/v1/tax/federal-brackets/{bracket_id}"), json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_federal_bracket(self, bracket_id: str) -> None:
        response = self.client.delete(self._url(f"/v1/tax/federal-brackets/{bracket_id}"))
        response.raise_for_status()
    
    def create_provincial_bracket(self, data: dict) -> dict:
        response = self.client.post(self._url("/v1/tax/provincial-brackets"), json=data)
        response.raise_for_status()
        return response.json()
    
    def update_provincial_bracket(self, bracket_id: str, data: dict) -> dict:
        response = self.client.put(self._url(f"/v1/tax/provincial-brackets/{bracket_id}"), json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_provincial_bracket(self, bracket_id: str) -> None:
        response = self.client.delete(self._url(f"/v1/tax/provincial-brackets/{bracket_id}"))
        response.raise_for_status()
    
    # ==================== Settings ====================
    
    def get_settings(self) -> dict:
        response = self.client.get(self._url("/v1/settings"))
        response.raise_for_status()
        return response.json()
    
    def update_settings(self, data: dict) -> dict:
        response = self.client.put(self._url("/v1/settings"), json=data)
        response.raise_for_status()
        return response.json()
    
    def get_provinces(self) -> list:
        response = self.client.get(self._url("/v1/settings/provinces"))
        response.raise_for_status()
        return response.json().get("provinces", [])
    
    # ==================== Backup ====================

    def get_backup_download(self) -> tuple[bytes, str]:
        """Fetch a full database backup as bytes plus the server-suggested filename.

        The backend serves `GET /v1/backup/download` with a `Content-Disposition:
        attachment; filename="..."` header. We extract the filename from that
        header so the FilePicker dialog can suggest it as the default save name.
        Returns a `(bytes, filename)` tuple. Falls back to `"backup.sql"` if the
        header is missing or unparseable.
        """
        response = self.client.get(self._url("/v1/backup/download"))
        response.raise_for_status()

        filename = "backup.sql"
        disposition = response.headers.get("content-disposition", "")
        # Cheap parser: matches `filename="..."` with double quotes
        if 'filename="' in disposition:
            start = disposition.index('filename="') + len('filename="')
            end = disposition.index('"', start)
            filename = disposition[start:end]

        return response.content, filename

    def restore_backup(self, sql_content: bytes, filename: str) -> dict:
        """Restore database from SQL backup file."""
        files = {"file": (filename, sql_content, "application/sql")}
        response = self.client.post(self._url("/v1/backup/restore"), files=files)
        response.raise_for_status()
        return response.json()
