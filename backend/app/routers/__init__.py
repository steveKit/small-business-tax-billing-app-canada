"""API routers."""
from app.routers.clients import router as clients_router
from app.routers.invoices import router as invoices_router
from app.routers.payments import router as payments_router
from app.routers.tax import router as tax_router
from app.routers.settings import router as settings_router
from app.routers.backup import router as backup_router

__all__ = [
    "clients_router",
    "invoices_router",
    "payments_router",
    "tax_router",
    "settings_router",
    "backup_router",
]
