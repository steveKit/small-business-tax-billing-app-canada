"""Payments view."""
from datetime import date

import flet as ft

from services.api_client import APIClient


class PaymentsView:
    """Payments management view."""
    
    def __init__(self, api_client: APIClient, page: ft.Page):
        self.api = api_client
        self.page = page
        self.payments = []
        self.invoices = []
    
    def format_currency(self, amount) -> str:
        """Format amount as currency."""
        try:
            return f"${float(amount):,.2f}"
        except (ValueError, TypeError):
            return "$0.00"
    
    def build(self) -> ft.Control:
        """Build the payments view."""
        
        # Data table
        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Invoice")),
                ft.DataColumn(ft.Text("Amount")),
                ft.DataColumn(ft.Text("Method")),
                ft.DataColumn(ft.Text("Reference")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[],
        )
        
        def load_data():
            """Load payments and invoices."""
            try:
                pay_result = self.api.get_payments()
                self.payments = pay_result.get("items", [])
                
                inv_result = self.api.get_invoices(status="pending")
                self.invoices = inv_result.get("items", [])
                
                update_table()
                update_invoice_dropdown()
            except Exception as e:
                show_error(f"Error loading data: {str(e)}")
        
        def update_table():
            """Update the data table."""
            data_table.rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(p.get("payment_date", ""))),
                        ft.DataCell(ft.Text(p.get("invoice", {}).get("invoice_number", "") if p.get("invoice") else "-")),
                        ft.DataCell(ft.Text(self.format_currency(p.get("amount", 0)))),
                        ft.DataCell(ft.Text(p.get("payment_method", "").replace("_", " ").title())),
                        ft.DataCell(ft.Text(p.get("reference_number", "") or "-")),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                icon_size=20,
                                tooltip="Delete",
                                on_click=lambda _, pid=p["id"]: delete_payment(pid),
                            )
                        ),
                    ],
                )
                for p in self.payments
            ]
            self.page.update()
        
        def update_invoice_dropdown():
            """Update invoice dropdown options."""
            invoice_dropdown.options = [
                ft.dropdown.Option(
                    key=inv["id"],
                    text=f"{inv['invoice_number']} - {self.format_currency(inv['amount_due'])} due"
                )
                for inv in self.invoices
                if float(inv.get("amount_due", 0)) > 0
            ]
            self.page.update()
        
        def show_error(message: str):
            """Show error snackbar."""
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.colors.RED_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        def show_success(message: str):
            """Show success snackbar."""
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.colors.GREEN_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        # Form fields
        invoice_dropdown = ft.Dropdown(label="Invoice *", expand=True, options=[])
        amount_field = ft.TextField(
            label="Amount *",
            prefix_text="$",
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
        )
        payment_date_field = ft.TextField(
            label="Payment Date *",
            value=date.today().isoformat(),
            expand=True,
        )
        method_dropdown = ft.Dropdown(
            label="Payment Method",
            value="e_transfer",
            options=[
                ft.dropdown.Option("e_transfer", "E-Transfer"),
                ft.dropdown.Option("bank_transfer", "Bank Transfer"),
                ft.dropdown.Option("cheque", "Cheque"),
                ft.dropdown.Option("cash", "Cash"),
                ft.dropdown.Option("credit_card", "Credit Card"),
                ft.dropdown.Option("other", "Other"),
            ],
            expand=True,
        )
        reference_field = ft.TextField(label="Reference Number", expand=True)
        notes_field = ft.TextField(label="Notes", multiline=True, min_lines=2, expand=True)
        
        def clear_form():
            """Clear form fields."""
            invoice_dropdown.value = None
            amount_field.value = ""
            payment_date_field.value = date.today().isoformat()
            method_dropdown.value = "e_transfer"
            reference_field.value = ""
            notes_field.value = ""
        
        def open_add_dialog(e):
            """Open dialog to add new payment."""
            clear_form()
            load_data()  # Refresh invoices
            dialog.open = True
            self.page.update()
        
        def save_payment(e):
            """Save payment."""
            if not invoice_dropdown.value:
                show_error("Invoice is required")
                return
            if not amount_field.value:
                show_error("Amount is required")
                return
            
            try:
                amount = float(amount_field.value.replace(",", ""))
            except ValueError:
                show_error("Invalid amount")
                return
            
            data = {
                "invoice_id": invoice_dropdown.value,
                "amount": amount,
                "payment_date": payment_date_field.value,
                "payment_method": method_dropdown.value,
                "reference_number": reference_field.value or None,
                "notes": notes_field.value or None,
            }
            
            try:
                self.api.create_payment(data)
                show_success("Payment recorded successfully")
                dialog.open = False
                load_data()
            except Exception as ex:
                show_error(f"Error recording payment: {str(ex)}")
        
        def delete_payment(payment_id: str):
            """Delete a payment."""
            try:
                self.api.delete_payment(payment_id)
                show_success("Payment deleted successfully")
                load_data()
            except Exception as ex:
                show_error(f"Error deleting payment: {str(ex)}")
        
        def close_dialog(e):
            """Close dialog."""
            dialog.open = False
            self.page.update()
        
        # Dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Record Payment"),
            content=ft.Container(
                content=ft.Column(
                    [
                        invoice_dropdown,
                        ft.Row([amount_field, payment_date_field]),
                        ft.Row([method_dropdown, reference_field]),
                        notes_field,
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Record", on_click=save_payment),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        
        # Build layout
        content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Payments", size=32, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Record Payment",
                            icon=ft.icons.ADD,
                            on_click=open_add_dialog,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                ft.Container(
                    content=data_table,
                    expand=True,
                ),
            ],
            expand=True,
        )
        
        # Load data
        load_data()
        
        return content
