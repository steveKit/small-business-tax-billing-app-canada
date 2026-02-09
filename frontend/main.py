"""Tax Billing Application - Flet Frontend."""
import os

import flet as ft

from views.dashboard import DashboardView
from views.clients import ClientsView
from views.invoices import InvoicesView
from views.payments import PaymentsView
from views.settings import SettingsView
from services.api_client import APIClient


def main(page: ft.Page):
    """Main application entry point."""
    # Configure page
    page.title = "Tax Billing"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 800
    page.window.min_height = 600
    
    # Initialize API client
    api_url = os.getenv("API_URL", "http://localhost:8000")
    api_client = APIClient(api_url)
    
    # Navigation rail
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.DASHBOARD_OUTLINED,
                selected_icon=ft.icons.DASHBOARD,
                label="Dashboard",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.PEOPLE_OUTLINED,
                selected_icon=ft.icons.PEOPLE,
                label="Clients",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.RECEIPT_LONG_OUTLINED,
                selected_icon=ft.icons.RECEIPT_LONG,
                label="Invoices",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.PAYMENTS_OUTLINED,
                selected_icon=ft.icons.PAYMENTS,
                label="Payments",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
                label="Settings",
            ),
        ],
        on_change=lambda e: navigate(e.control.selected_index),
    )
    
    # Content area
    content_area = ft.Container(
        expand=True,
        padding=20,
    )
    
    # Views
    views = {
        0: DashboardView(api_client, page),
        1: ClientsView(api_client, page),
        2: InvoicesView(api_client, page),
        3: PaymentsView(api_client, page),
        4: SettingsView(api_client, page),
    }
    
    def navigate(index: int):
        """Navigate to a view."""
        content_area.content = views[index].build()
        page.update()
    
    # Initial layout
    page.add(
        ft.Row(
            [
                nav_rail,
                ft.VerticalDivider(width=1),
                content_area,
            ],
            expand=True,
        )
    )
    
    # Load initial view
    navigate(0)


if __name__ == "__main__":
    # Use FLET_WEB=1 for web browser mode (useful in WSL or headless environments)
    if os.getenv("FLET_WEB", "0") == "1":
        ft.app(target=main, port=8080, view=ft.AppView.WEB_BROWSER)
    else:
        ft.app(target=main)
