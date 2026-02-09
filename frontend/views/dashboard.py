"""Dashboard view - Tax Reserve Summary."""
from datetime import datetime
from decimal import Decimal

import flet as ft

from services.api_client import APIClient


class DashboardView:
    """Dashboard view showing tax summary."""
    
    def __init__(self, api_client: APIClient, page: ft.Page):
        self.api = api_client
        self.page = page
        self.year = datetime.now().year
    
    def format_currency(self, amount) -> str:
        """Format amount as currency."""
        try:
            return f"${float(amount):,.2f}"
        except (ValueError, TypeError):
            return "$0.00"
    
    def build(self) -> ft.Control:
        """Build the dashboard view."""
        
        def load_data():
            """Load tax summary data."""
            try:
                data = self.api.get_tax_summary(self.year)
                update_ui(data)
            except Exception as e:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error loading data: {str(e)}"),
                    bgcolor=ft.colors.RED_400,
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        def update_ui(data: dict):
            """Update UI with data."""
            # Revenue card
            revenue_paid.value = self.format_currency(data.get("total_revenue_paid", 0))
            revenue_pending.value = self.format_currency(data.get("total_revenue_pending", 0))
            
            # HST card
            hst_collected.value = self.format_currency(data.get("total_hst_collected_paid", 0))
            hst_holdback.value = self.format_currency(data.get("hst_holdback", 0))
            
            # Income tax card
            income_calc = data.get("income_tax_calculation", {})
            income_tax_holdback.value = self.format_currency(data.get("income_tax_holdback", 0))
            effective_rate.value = f"{income_calc.get('effective_rate', 0):.1f}%"
            projected_income.value = self.format_currency(income_calc.get("projected_annual_income", 0))
            
            # Total reserve card
            total_reserve.value = self.format_currency(data.get("total_tax_reserve", 0))
            
            # Invoice counts
            paid_count.value = str(data.get("paid_invoice_count", 0))
            pending_count.value = str(data.get("pending_invoice_count", 0))
            
            self.page.update()
        
        def change_year(delta: int):
            """Change the selected year."""
            self.year += delta
            year_text.value = str(self.year)
            load_data()
        
        # Year selector
        year_text = ft.Text(str(self.year), size=24, weight=ft.FontWeight.BOLD)
        
        # Revenue card values
        revenue_paid = ft.Text("$0.00", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700)
        revenue_pending = ft.Text("$0.00", size=16, color=ft.colors.ORANGE_700)
        
        # HST card values
        hst_collected = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD)
        hst_holdback = ft.Text("$0.00", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)
        
        # Income tax card values
        income_tax_holdback = ft.Text("$0.00", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE_700)
        effective_rate = ft.Text("0%", size=16)
        projected_income = ft.Text("$0.00", size=16)
        
        # Total reserve
        total_reserve = ft.Text("$0.00", size=36, weight=ft.FontWeight.BOLD, color=ft.colors.RED_700)
        
        # Invoice counts
        paid_count = ft.Text("0", size=24, weight=ft.FontWeight.BOLD)
        pending_count = ft.Text("0", size=24, weight=ft.FontWeight.BOLD)
        
        # Build layout
        content = ft.Column(
            [
                # Header
                ft.Row(
                    [
                        ft.Text("Tax Reserve Dashboard", size=32, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.icons.CHEVRON_LEFT,
                                    on_click=lambda _: change_year(-1),
                                ),
                                year_text,
                                ft.IconButton(
                                    icon=ft.icons.CHEVRON_RIGHT,
                                    on_click=lambda _: change_year(1),
                                ),
                            ],
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                
                # Main stats row
                ft.Row(
                    [
                        # Revenue Card
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Revenue (Paid)", size=14, color=ft.colors.GREY_600),
                                        revenue_paid,
                                        ft.Row(
                                            [
                                                ft.Text("Pending: ", size=12, color=ft.colors.GREY_500),
                                                revenue_pending,
                                            ],
                                        ),
                                    ],
                                ),
                                padding=20,
                            ),
                            expand=True,
                        ),
                        
                        # HST Card
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("HST Holdback", size=14, color=ft.colors.GREY_600),
                                        hst_holdback,
                                        ft.Row(
                                            [
                                                ft.Text("Collected: ", size=12, color=ft.colors.GREY_500),
                                                hst_collected,
                                            ],
                                        ),
                                    ],
                                ),
                                padding=20,
                            ),
                            expand=True,
                        ),
                        
                        # Income Tax Card
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Income Tax Holdback", size=14, color=ft.colors.GREY_600),
                                        income_tax_holdback,
                                        ft.Row(
                                            [
                                                ft.Text("Effective Rate: ", size=12, color=ft.colors.GREY_500),
                                                effective_rate,
                                            ],
                                        ),
                                        ft.Row(
                                            [
                                                ft.Text("Projected Income: ", size=12, color=ft.colors.GREY_500),
                                                projected_income,
                                            ],
                                        ),
                                    ],
                                ),
                                padding=20,
                            ),
                            expand=True,
                        ),
                    ],
                    spacing=20,
                ),
                
                # Total Reserve Card
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "TOTAL TAX RESERVE",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.GREY_700,
                                ),
                                ft.Text(
                                    "Amount to set aside for taxes",
                                    size=12,
                                    color=ft.colors.GREY_500,
                                ),
                                total_reserve,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=30,
                        alignment=ft.alignment.center,
                    ),
                    color=ft.colors.RED_50,
                ),
                
                # Invoice counts row
                ft.Row(
                    [
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN_500, size=40),
                                        paid_count,
                                        ft.Text("Paid Invoices", size=12, color=ft.colors.GREY_600),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                padding=20,
                            ),
                            expand=True,
                        ),
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon(ft.icons.PENDING, color=ft.colors.ORANGE_500, size=40),
                                        pending_count,
                                        ft.Text("Pending Invoices", size=12, color=ft.colors.GREY_600),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                padding=20,
                            ),
                            expand=True,
                        ),
                    ],
                    spacing=20,
                ),
            ],
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # Load data on build
        load_data()
        
        return content
