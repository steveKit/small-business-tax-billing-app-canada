"""Frontend views."""
from views.dashboard import DashboardView
from views.clients import ClientsView
from views.invoices import InvoicesView
from views.payments import PaymentsView
from views.settings import SettingsView

__all__ = [
    "DashboardView",
    "ClientsView",
    "InvoicesView",
    "PaymentsView",
    "SettingsView",
]
