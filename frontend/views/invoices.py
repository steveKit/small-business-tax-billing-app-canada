"""Invoices view with edit functionality."""
from datetime import date, timedelta
import flet as ft
from services.api_client import APIClient


class InvoicesView:
    """Invoices management view."""
    
    def __init__(self, api_client: APIClient, page: ft.Page):
        self.api = api_client
        self.page = page
        self.invoices = []
        self.clients = []
        self.editing_invoice = None
    
    def format_currency(self, amount) -> str:
        try: return f"${float(amount):,.2f}"
        except: return "$0.00"
    
    def build(self) -> ft.Control:
        current_year = date.today().year

        # File picker for PDF save-as (TASK-014 — replaces launch_url)
        pdf_file_picker = ft.FilePicker()

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Invoice #")),
                ft.DataColumn(ft.Text("Client")),
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Tax Year")),
                ft.DataColumn(ft.Text("Total")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[],
        )
        
        client_dropdown = ft.Dropdown(label="Client *", expand=True, options=[])
        description_field = ft.TextField(label="Description of Work *", multiline=True, min_lines=3, expand=True)
        subtotal_field = ft.TextField(label="Subtotal *", prefix_text="$", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        billed_date_field = ft.TextField(label="Invoice Date *", value=date.today().isoformat(), expand=True)
        due_date_field = ft.TextField(label="Due Date *", value=(date.today() + timedelta(days=30)).isoformat(), expand=True)
        tax_year_dropdown = ft.Dropdown(
            label="Tax Year *", width=120,
            options=[ft.dropdown.Option(str(y)) for y in range(current_year - 1, current_year + 2)],
            value=str(current_year),
        )
        notes_field = ft.TextField(label="Notes", multiline=True, min_lines=2, expand=True)
        dialog_title = ft.Text("Create Invoice")
        
        def close_dialog(e=None):
            self.page.close(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=dialog_title,
            content=ft.Container(
                content=ft.Column([
                    client_dropdown, description_field, subtotal_field,
                    ft.Row([billed_date_field, due_date_field, tax_year_dropdown]),
                    notes_field,
                    ft.Text("Tax will be automatically calculated based on your province settings.", size=12, color=ft.colors.GREY_500, italic=True),
                ], spacing=10, tight=True),
                width=650,
            ),
            actions=[ft.TextButton("Cancel", on_click=close_dialog), ft.ElevatedButton("Save", on_click=lambda e: save_invoice())],
        )
        
        def show_error(msg):
            self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=ft.colors.RED_400)
            self.page.snack_bar.open = True
            self.page.update()
        
        def show_success(msg):
            self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=ft.colors.GREEN_400)
            self.page.snack_bar.open = True
            self.page.update()
        
        def load_data():
            try:
                inv_result = self.api.get_invoices()
                self.invoices = inv_result.get("items", [])
                client_result = self.api.get_clients()
                self.clients = client_result.get("items", [])
                update_table()
                update_client_dropdown()
            except Exception as e:
                show_error(f"Error loading data: {str(e)}")
        
        def update_table():
            data_table.rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(inv.get("invoice_number", ""))),
                    ft.DataCell(ft.Text(inv.get("client", {}).get("name", "") if inv.get("client") else "-")),
                    ft.DataCell(ft.Text(inv.get("billed_date", ""))),
                    ft.DataCell(ft.Text(str(inv.get("year_billed", "")))),
                    ft.DataCell(ft.Text(self.format_currency(inv.get("total", 0)))),
                    ft.DataCell(get_status_chip(inv.get("status", "draft"))),
                    ft.DataCell(ft.Row([
                        ft.IconButton(icon=ft.icons.EDIT, icon_size=20, tooltip="Edit", on_click=lambda _, i=inv: open_edit_dialog(i)),
                        ft.IconButton(icon=ft.icons.PICTURE_AS_PDF, icon_size=20, tooltip="Download PDF", on_click=lambda _, iid=inv["id"]: download_pdf(iid)),
                        ft.IconButton(icon=ft.icons.SEND, icon_size=20, tooltip="Mark as Pending", on_click=lambda _, iid=inv["id"]: update_status(iid, "pending")) if inv.get("status") == "draft" else ft.Container(),
                    ], tight=True)),
                ])
                for inv in self.invoices
            ]
            self.page.update()
        
        def get_status_chip(status: str) -> ft.Control:
            colors = {"draft": ft.colors.GREY_400, "pending": ft.colors.ORANGE_400, "paid": ft.colors.GREEN_400, "cancelled": ft.colors.RED_400}
            return ft.Container(content=ft.Text(status.upper(), size=10, color=ft.colors.WHITE), bgcolor=colors.get(status, ft.colors.GREY_400), padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=4)
        
        def update_client_dropdown():
            client_dropdown.options = [ft.dropdown.Option(key=c["id"], text=c["name"]) for c in self.clients]
            self.page.update()
        
        def clear_form():
            client_dropdown.value = None
            description_field.value = ""
            subtotal_field.value = ""
            billed_date_field.value = date.today().isoformat()
            due_date_field.value = (date.today() + timedelta(days=30)).isoformat()
            tax_year_dropdown.value = str(current_year)
            notes_field.value = ""
        
        def open_add_dialog(e):
            self.editing_invoice = None
            clear_form()
            dialog_title.value = "Create Invoice"
            dialog.actions = [ft.TextButton("Cancel", on_click=close_dialog), ft.ElevatedButton("Create", on_click=lambda e: save_invoice())]
            self.page.open(dialog)
        
        def open_edit_dialog(invoice):
            self.editing_invoice = invoice
            dialog_title.value = f"Edit Invoice {invoice.get('invoice_number', '')}"
            client_dropdown.value = invoice.get("client_id")
            description_field.value = invoice.get("description", "")
            subtotal_field.value = str(invoice.get("subtotal", ""))
            billed_date_field.value = invoice.get("billed_date", "")
            due_date_field.value = invoice.get("due_date", "")
            tax_year_dropdown.value = str(invoice.get("year_billed", current_year))
            notes_field.value = invoice.get("notes") or ""
            dialog.actions = [ft.TextButton("Cancel", on_click=close_dialog), ft.ElevatedButton("Save", on_click=lambda e: save_invoice())]
            self.page.open(dialog)
        
        def save_invoice():
            if not description_field.value:
                show_error("Description is required"); return
            if not subtotal_field.value:
                show_error("Subtotal is required"); return
            
            try:
                subtotal = float(subtotal_field.value.replace(",", ""))
            except ValueError:
                show_error("Invalid subtotal amount"); return
            
            data = {
                "description": description_field.value,
                "subtotal": subtotal,
                "billed_date": billed_date_field.value,
                "due_date": due_date_field.value,
                "notes": notes_field.value or None,
            }
            
            try:
                if self.editing_invoice:
                    self.api.update_invoice(self.editing_invoice["id"], data)
                    show_success("Invoice updated successfully")
                else:
                    if not client_dropdown.value:
                        show_error("Client is required"); return
                    data["client_id"] = client_dropdown.value
                    self.api.create_invoice(data)
                    show_success("Invoice created successfully")
                close_dialog()
                load_data()
            except Exception as ex:
                show_error(f"Error saving invoice: {str(ex)}")
        
        def update_status(invoice_id: str, status: str):
            try:
                self.api.update_invoice_status(invoice_id, status)
                show_success(f"Invoice marked as {status}")
                load_data()
            except Exception as ex:
                show_error(f"Error updating status: {str(ex)}")
        
        def download_pdf(invoice_id: str):
            # Look up invoice_number for the default filename
            invoice = next((i for i in self.invoices if i.get("id") == invoice_id), None)
            default_name = f"Invoice-{invoice.get('invoice_number', 'unknown')}.pdf" if invoice else "invoice.pdf"

            def on_save_result(e: ft.FilePickerResultEvent):
                if not e.path:
                    return  # user cancelled
                try:
                    pdf_bytes = self.api.get_invoice_pdf(invoice_id)
                    with open(e.path, "wb") as f:
                        f.write(pdf_bytes)
                    show_success(f"Saved {default_name} to {e.path}")
                except Exception as ex:
                    show_error(f"Download failed: {str(ex)}")

            pdf_file_picker.on_result = on_save_result
            pdf_file_picker.save_file(
                file_name=default_name,
                dialog_title="Save invoice PDF as…",
                allowed_extensions=["pdf"],
            )

        content = ft.Column([
            pdf_file_picker,
            ft.Row([
                ft.Text("Invoices", size=32, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("Create Invoice", icon=ft.icons.ADD, on_click=open_add_dialog),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Container(content=data_table, expand=True),
        ], expand=True)
        
        load_data()
        return content
