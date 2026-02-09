"""Pydantic schemas for API request/response validation."""
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse,
)
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceStatusUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoicePDFResponse,
)
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
)
from app.schemas.tax import (
    TaxSummaryResponse,
    TaxRatesResponse,
    TaxYearSettings,
    SalesTaxRateResponse,
)
from app.schemas.settings import (
    BusinessSettingsUpdate,
    BusinessSettingsResponse,
)
from app.schemas.backup import (
    BackupResponse,
    BackupListResponse,
    RestoreRequest,
    RestoreResponse,
)
from app.schemas.common import (
    APIResponse,
    ErrorResponse,
    PaginationParams,
)

__all__ = [
    # Client
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "ClientListResponse",
    # Invoice
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceStatusUpdate",
    "InvoiceResponse",
    "InvoiceListResponse",
    "InvoicePDFResponse",
    # Payment
    "PaymentCreate",
    "PaymentResponse",
    "PaymentListResponse",
    # Tax
    "TaxSummaryResponse",
    "TaxRatesResponse",
    "TaxYearSettings",
    "SalesTaxRateResponse",
    # Settings
    "BusinessSettingsUpdate",
    "BusinessSettingsResponse",
    # Backup
    "BackupResponse",
    "BackupListResponse",
    "RestoreRequest",
    "RestoreResponse",
    # Common
    "APIResponse",
    "ErrorResponse",
    "PaginationParams",
]
