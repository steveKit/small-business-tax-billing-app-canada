"""Clients view."""
import flet as ft

from services.api_client import APIClient


class ClientsView:
    """Clients management view."""
    
    def __init__(self, api_client: APIClient, page: ft.Page):
        self.api = api_client
        self.page = page
        self.clients = []
    
    def build(self) -> ft.Control:
        """Build the clients view."""
        
        # Data table
        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Contact")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Phone")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[],
        )
        
        def load_clients():
            """Load clients from API."""
            try:
                result = self.api.get_clients()
                self.clients = result.get("items", [])
                update_table()
            except Exception as e:
                show_error(f"Error loading clients: {str(e)}")
        
        def update_table():
            """Update the data table."""
            data_table.rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(c.get("name", ""))),
                        ft.DataCell(ft.Text(c.get("contact_name", "") or "-")),
                        ft.DataCell(ft.Text(c.get("email", "") or "-")),
                        ft.DataCell(ft.Text(c.get("phone", "") or "-")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    icon_size=20,
                                    tooltip="Edit",
                                    on_click=lambda _, cid=c["id"]: open_edit_dialog(cid),
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_size=20,
                                    tooltip="Delete",
                                    on_click=lambda _, cid=c["id"]: delete_client(cid),
                                ),
                            ])
                        ),
                    ],
                )
                for c in self.clients
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
        name_field = ft.TextField(label="Client Name *", expand=True)
        contact_field = ft.TextField(label="Contact Name", expand=True)
        email_field = ft.TextField(label="Email", expand=True)
        phone_field = ft.TextField(label="Phone", expand=True)
        address1_field = ft.TextField(label="Address Line 1", expand=True)
        city_field = ft.TextField(label="City", expand=True)
        province_field = ft.TextField(label="Province", expand=True)
        postal_field = ft.TextField(label="Postal Code", expand=True)
        notes_field = ft.TextField(label="Notes", multiline=True, min_lines=2, expand=True)
        
        editing_id = None
        
        def clear_form():
            """Clear form fields."""
            nonlocal editing_id
            editing_id = None
            name_field.value = ""
            contact_field.value = ""
            email_field.value = ""
            phone_field.value = ""
            address1_field.value = ""
            city_field.value = ""
            province_field.value = ""
            postal_field.value = ""
            notes_field.value = ""
        
        def open_add_dialog(e):
            """Open dialog to add new client."""
            clear_form()
            dialog.title = ft.Text("Add Client")
            dialog.open = True
            self.page.update()
        
        def open_edit_dialog(client_id: str):
            """Open dialog to edit client."""
            nonlocal editing_id
            client = next((c for c in self.clients if c["id"] == client_id), None)
            if client:
                editing_id = client_id
                name_field.value = client.get("name", "")
                contact_field.value = client.get("contact_name", "") or ""
                email_field.value = client.get("email", "") or ""
                phone_field.value = client.get("phone", "") or ""
                address1_field.value = client.get("address_line1", "") or ""
                city_field.value = client.get("city", "") or ""
                province_field.value = client.get("province", "") or ""
                postal_field.value = client.get("postal_code", "") or ""
                notes_field.value = client.get("notes", "") or ""
                dialog.title = ft.Text("Edit Client")
                dialog.open = True
                self.page.update()
        
        def save_client(e):
            """Save client."""
            if not name_field.value:
                show_error("Client name is required")
                return
            
            data = {
                "name": name_field.value,
                "contact_name": contact_field.value or None,
                "email": email_field.value or None,
                "phone": phone_field.value or None,
                "address_line1": address1_field.value or None,
                "city": city_field.value or None,
                "province": province_field.value or None,
                "postal_code": postal_field.value or None,
                "notes": notes_field.value or None,
            }
            
            try:
                if editing_id:
                    self.api.update_client(editing_id, data)
                    show_success("Client updated successfully")
                else:
                    self.api.create_client(data)
                    show_success("Client created successfully")
                
                dialog.open = False
                load_clients()
            except Exception as ex:
                show_error(f"Error saving client: {str(ex)}")
        
        def delete_client(client_id: str):
            """Delete a client."""
            try:
                self.api.delete_client(client_id)
                show_success("Client deleted successfully")
                load_clients()
            except Exception as ex:
                show_error(f"Error deleting client: {str(ex)}")
        
        def close_dialog(e):
            """Close dialog."""
            dialog.open = False
            self.page.update()
        
        # Dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Client"),
            content=ft.Container(
                content=ft.Column(
                    [
                        name_field,
                        contact_field,
                        ft.Row([email_field, phone_field]),
                        address1_field,
                        ft.Row([city_field, province_field, postal_field]),
                        notes_field,
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Save", on_click=save_client),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        
        # Build layout
        content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Clients", size=32, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Add Client",
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
        load_clients()
        
        return content
