"""Settings view with tax rate editing and database backup."""
from datetime import datetime
import flet as ft
from services.api_client import APIClient


class SettingsView:
    """Settings management view."""
    
    def __init__(self, api_client: APIClient, page: ft.Page):
        self.api = api_client
        self.page = page
        self.settings = {}
        self.provinces = []
        self.current_year = datetime.now().year
        self.tax_rates = {}
        self.editing_bracket = None
        self.bracket_type = None
    
    def build(self) -> ft.Control:
        # Business Info fields
        business_name = ft.TextField(label="Business Name *", expand=True)
        address_line1 = ft.TextField(label="Address Line 1", expand=True)
        address_line2 = ft.TextField(label="Address Line 2", expand=True)
        city = ft.TextField(label="City", expand=True)
        province_dropdown = ft.Dropdown(label="Province *", expand=True, options=[])
        postal_code = ft.TextField(label="Postal Code", width=150)
        phone = ft.TextField(label="Phone", expand=True)
        email = ft.TextField(label="Email", expand=True)
        hst_number = ft.TextField(label="GST/HST Number", expand=True)
        payment_terms = ft.TextField(label="Payment Terms", value="Net 30", expand=True)
        payment_instructions = ft.TextField(label="Payment Instructions", expand=True, multiline=True, min_lines=2, max_lines=4)
        
        # Tax Settings
        tax_year_dropdown = ft.Dropdown(label="Tax Year", width=150,
            options=[ft.dropdown.Option(str(self.current_year - 1)), ft.dropdown.Option(str(self.current_year))],
            value=str(self.current_year))
        presumed_income_field = ft.TextField(label="Presumed Annual Income ($)", value="80000.00", width=200)
        
        federal_brackets_column = ft.Column(spacing=5)
        provincial_brackets_column = ft.Column(spacing=5)
        sales_tax_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
        
        min_income_field = ft.TextField(label="Min Income", keyboard_type=ft.KeyboardType.NUMBER)
        max_income_field = ft.TextField(label="Max Income (leave empty for no max)", keyboard_type=ft.KeyboardType.NUMBER)
        rate_field = ft.TextField(label="Rate (e.g., 0.15 for 15%)", keyboard_type=ft.KeyboardType.NUMBER)
        
        # File picker for restore
        file_picker = ft.FilePicker(on_result=lambda e: handle_restore_file(e))
        
        def close_dialog(e=None): self.page.close(edit_dialog)
        
        edit_dialog = ft.AlertDialog(modal=True, title=ft.Text("Edit Tax Bracket"),
            content=ft.Column([min_income_field, max_income_field, rate_field], tight=True, spacing=10, width=300),
            actions=[ft.TextButton("Close", on_click=close_dialog)])
        
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
                self.provinces = self.api.get_provinces()
                province_dropdown.options = [ft.dropdown.Option(p["code"], f"{p['code']} - {p['name']}") for p in self.provinces]
                self.settings = self.api.get_settings()
                populate_form()
                load_tax_rates(int(tax_year_dropdown.value))
                self.page.update()
            except Exception as e:
                show_error(f"Error loading settings: {str(e)}")
        
        def load_tax_rates(year):
            try:
                self.tax_rates = self.api.get_tax_rates(year)
                try:
                    settings = self.api.get_tax_year_settings(year)
                    presumed_income_field.value = str(settings.get("presumed_annual_income", 80000.00))
                except: presumed_income_field.value = "80000.00"
                update_tax_display()
            except Exception as e:
                show_error(f"Error loading tax rates: {str(e)}")
        
        def save_bracket(e):
            try:
                min_inc = float(min_income_field.value or 0)
                max_inc = float(max_income_field.value) if max_income_field.value else None
                rate = float(rate_field.value or 0)
                year = int(tax_year_dropdown.value)
                province = self.settings.get("province", "ON")
                
                if self.editing_bracket and self.editing_bracket.get("id"):
                    data = {"min_income": min_inc, "rate": rate}
                    if max_inc: data["max_income"] = max_inc
                    if self.bracket_type == "federal": self.api.update_federal_bracket(self.editing_bracket["id"], data)
                    else: self.api.update_provincial_bracket(self.editing_bracket["id"], data)
                    show_success("Tax bracket updated")
                else:
                    data = {"year": year, "min_income": min_inc, "max_income": max_inc, "rate": rate}
                    if self.bracket_type == "federal": self.api.create_federal_bracket(data)
                    else: data["province"] = province; self.api.create_provincial_bracket(data)
                    show_success("Tax bracket added")
                close_dialog()
                load_tax_rates(year)
            except Exception as ex: show_error(f"Error saving bracket: {str(ex)}")
        
        def delete_bracket(e):
            try:
                if self.editing_bracket and self.editing_bracket.get("id"):
                    if self.bracket_type == "federal": self.api.delete_federal_bracket(self.editing_bracket["id"])
                    else: self.api.delete_provincial_bracket(self.editing_bracket["id"])
                    show_success("Tax bracket deleted")
                    close_dialog()
                    load_tax_rates(int(tax_year_dropdown.value))
            except Exception as ex: show_error(f"Error deleting bracket: {str(ex)}")
        
        def open_edit_dialog(bracket, bracket_type):
            self.editing_bracket = bracket
            self.bracket_type = bracket_type
            min_income_field.value = str(bracket.get("min_income", 0))
            max_val = bracket.get("max_income")
            max_income_field.value = str(max_val) if max_val else ""
            rate_field.value = str(bracket.get("rate", 0))
            edit_dialog.title = ft.Text(f"Edit {bracket_type.title()} Tax Bracket")
            edit_dialog.actions = [ft.TextButton("Cancel", on_click=close_dialog), ft.ElevatedButton("Save", on_click=save_bracket),
                ft.TextButton("Delete", on_click=delete_bracket, style=ft.ButtonStyle(color=ft.colors.RED))]
            self.page.open(edit_dialog)
        
        def open_add_dialog(bracket_type):
            self.editing_bracket = None
            self.bracket_type = bracket_type
            min_income_field.value = max_income_field.value = rate_field.value = ""
            edit_dialog.title = ft.Text(f"Add {bracket_type.title()} Tax Bracket")
            edit_dialog.actions = [ft.TextButton("Cancel", on_click=close_dialog), ft.ElevatedButton("Add", on_click=save_bracket)]
            self.page.open(edit_dialog)
        
        def update_tax_display():
            federal_brackets_column.controls.clear()
            provincial_brackets_column.controls.clear()
            province = self.settings.get("province", "ON")
            year = int(tax_year_dropdown.value)
            
            federal_brackets_column.controls.append(ft.Row([ft.Text(f"Federal Income Tax Brackets ({year})", size=14, weight=ft.FontWeight.BOLD),
                ft.IconButton(icon=ft.icons.ADD, tooltip="Add bracket", on_click=lambda e: open_add_dialog("federal"))]))
            for bracket in self.tax_rates.get("federal_brackets", []):
                rate_val = bracket.get("rate_percentage", float(bracket.get("rate", 0)) * 100)
                min_inc = float(bracket.get("min_income", 0))
                max_inc = bracket.get("max_income")
                max_str = f"${float(max_inc):,.0f}" if max_inc else "∞"
                federal_brackets_column.controls.append(ft.Row([ft.Text(f"{rate_val:.2f}%", width=70, weight=ft.FontWeight.W_500),
                    ft.Text(f"${min_inc:,.0f} - {max_str}", expand=True, color=ft.colors.GREY_700),
                    ft.IconButton(icon=ft.icons.EDIT, tooltip="Edit", icon_size=18, on_click=lambda e, b=bracket: open_edit_dialog(b, "federal"))]))
            
            prov_name = next((p["name"] for p in self.provinces if p["code"] == province), province)
            provincial_brackets_column.controls.append(ft.Row([ft.Text(f"{prov_name} Provincial Tax Brackets ({year})", size=14, weight=ft.FontWeight.BOLD),
                ft.IconButton(icon=ft.icons.ADD, tooltip="Add bracket", on_click=lambda e: open_add_dialog("provincial"))]))
            for bracket in self.tax_rates.get("provincial_brackets", []):
                rate_val = bracket.get("rate_percentage", float(bracket.get("rate", 0)) * 100)
                min_inc = float(bracket.get("min_income", 0))
                max_inc = bracket.get("max_income")
                max_str = f"${float(max_inc):,.0f}" if max_inc else "∞"
                provincial_brackets_column.controls.append(ft.Row([ft.Text(f"{rate_val:.2f}%", width=70, weight=ft.FontWeight.W_500),
                    ft.Text(f"${min_inc:,.0f} - {max_str}", expand=True, color=ft.colors.GREY_700),
                    ft.IconButton(icon=ft.icons.EDIT, tooltip="Edit", icon_size=18, on_click=lambda e, b=bracket: open_edit_dialog(b, "provincial"))]))
            
            sales_tax = self.tax_rates.get("sales_tax")
            if sales_tax:
                total_rate = float(sales_tax.get("total_rate_percentage", 0) or 0)
                sales_tax_text.value = f"{sales_tax.get('tax_type', 'HST')}: {total_rate:.1f}%"
            else: sales_tax_text.value = "Sales tax rate not found"
            self.page.update()
        
        tax_year_dropdown.on_change = lambda e: load_tax_rates(int(tax_year_dropdown.value))
        
        def populate_form():
            business_name.value = self.settings.get("business_name", "")
            address_line1.value = self.settings.get("address_line1") or ""
            address_line2.value = self.settings.get("address_line2") or ""
            city.value = self.settings.get("city") or ""
            province_dropdown.value = self.settings.get("province", "ON")
            postal_code.value = self.settings.get("postal_code") or ""
            phone.value = self.settings.get("phone") or ""
            email.value = self.settings.get("email") or ""
            hst_number.value = self.settings.get("hst_number") or ""
            payment_terms.value = self.settings.get("payment_terms", "Net 30")
            payment_instructions.value = self.settings.get("payment_instructions") or ""
        
        def save_settings(e):
            if not business_name.value: show_error("Business name is required"); return
            try:
                data = {
                    "business_name": business_name.value,
                    "address_line1": address_line1.value or None,
                    "address_line2": address_line2.value or None,
                    "city": city.value or None,
                    "province": province_dropdown.value,
                    "postal_code": postal_code.value or None,
                    "phone": phone.value or None,
                    "email": email.value or None,
                    "hst_number": hst_number.value or None,
                    "payment_terms": payment_terms.value,
                    "payment_instructions": payment_instructions.value or None,
                }
                self.api.update_settings(data)
                self.settings = self.api.get_settings()
                show_success("Settings saved successfully")
                load_tax_rates(int(tax_year_dropdown.value))
            except Exception as ex: show_error(f"Error saving settings: {str(ex)}")
        
        def save_presumed_income(e):
            try:
                income = float(presumed_income_field.value.replace(",", ""))
                year = int(tax_year_dropdown.value)
                self.api.update_tax_year_settings(year, {"year": year, "presumed_annual_income": income, "notes": "Updated via UI"})
                show_success(f"Presumed income for {year} saved: ${income:,.2f}")
            except ValueError: show_error("Please enter a valid income amount")
            except Exception as ex: show_error(f"Error saving presumed income: {str(ex)}")
        
        def download_backup(e):
            # Open backup download URL in browser
            backup_url = "http://localhost:8000/v1/backup/download"
            self.page.launch_url(backup_url)
            show_success("Backup download started")
        
        def handle_restore_file(e: ft.FilePickerResultEvent):
            if e.files and len(e.files) > 0:
                file = e.files[0]
                if file.path:
                    try:
                        with open(file.path, "rb") as f:
                            content = f.read()
                        self.api.restore_backup(content, file.name)
                        show_success("Database restored successfully! Refreshing...")
                        load_data()
                    except Exception as ex:
                        show_error(f"Restore failed: {str(ex)}")
        
        def open_restore_dialog(e):
            file_picker.pick_files(allowed_extensions=["sql"], dialog_title="Select backup file to restore")
        
        content = ft.Column([
            file_picker,
            ft.Text("Settings", size=32, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Card(content=ft.Container(content=ft.Column([
                ft.Text("Business Information", size=18, weight=ft.FontWeight.BOLD),
                business_name,
                ft.Row([address_line1, address_line2]),
                ft.Row([city, province_dropdown, postal_code]),
                ft.Row([phone, email]),
                ft.Row([hst_number, payment_terms]),
                payment_instructions,
            ], spacing=10), padding=20)),
            ft.Card(content=ft.Container(content=ft.Column([
                ft.Row([ft.Text("Tax Rates", size=18, weight=ft.FontWeight.BOLD), ft.Container(expand=True), tax_year_dropdown]),
                ft.Divider(height=10),
                ft.Row([presumed_income_field, ft.ElevatedButton("Save", icon=ft.icons.SAVE, on_click=save_presumed_income),
                        ft.Text("(Used for income tax withholding)", color=ft.colors.GREY_600, size=12)]),
                ft.Divider(height=20),
                ft.Text("Sales Tax Rate", size=14, weight=ft.FontWeight.BOLD), sales_tax_text,
                ft.Divider(height=20),
                federal_brackets_column,
                ft.Divider(height=20),
                provincial_brackets_column,
            ], spacing=10), padding=20)),
            ft.Card(content=ft.Container(content=ft.Column([
                ft.Text("Database Backup & Restore", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Create a full PostgreSQL backup of your data, or restore from a previous backup.", size=12, color=ft.colors.GREY_600),
                ft.Row([
                    ft.ElevatedButton("Download Backup", icon=ft.icons.BACKUP, on_click=download_backup),
                    ft.OutlinedButton("Restore from Backup", icon=ft.icons.RESTORE, on_click=open_restore_dialog),
                ], spacing=10),
                ft.Text("⚠️ Restoring will replace all current data with the backup data.", size=11, color=ft.colors.ORANGE_700),
            ], spacing=10), padding=20)),
            ft.Container(content=ft.ElevatedButton("Save Settings", icon=ft.icons.SAVE, on_click=save_settings), alignment=ft.alignment.center_right),
        ], spacing=20, scroll=ft.ScrollMode.AUTO)
        
        load_data()
        return content
