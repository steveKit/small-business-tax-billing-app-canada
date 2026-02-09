"""Invoice PDF generation service."""
import io
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.models.invoice import Invoice
from app.models.client import Client
from app.models.business_settings import BusinessSettings


class InvoicePDFService:
    """Service for generating invoice PDFs."""
    
    def __init__(self, template_dir: str = "app/templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
        )
    
    def format_currency(self, amount: Decimal) -> str:
        """Format amount as currency."""
        return f"${amount:,.2f}"
    
    def format_date(self, d: date) -> str:
        """Format date for display."""
        return d.strftime("%B %d, %Y")
    
    def generate_pdf(
        self,
        invoice: Invoice,
        client: Client,
        settings: BusinessSettings,
    ) -> bytes:
        """Generate PDF for an invoice."""
        # Get template
        template = self.env.get_template("invoice.html")
        
        # Prepare context
        context = {
            # Business info
            "business_name": settings.business_name,
            "business_address_line1": settings.address_line1 or "",
            "business_address_line2": settings.address_line2 or "",
            "business_city": settings.city or "",
            "business_province": settings.province,
            "business_postal_code": settings.postal_code or "",
            "business_phone": settings.phone or "",
            "business_email": settings.email or "",
            "hst_number": settings.hst_number or "",
            
            # Client info
            "client_name": client.name,
            "client_contact": client.contact_name or "",
            "client_address_line1": client.address_line1 or "",
            "client_address_line2": client.address_line2 or "",
            "client_city": client.city or "",
            "client_province": client.province or "",
            "client_postal_code": client.postal_code or "",
            "client_email": client.email or "",
            
            # Invoice details
            "invoice_number": invoice.invoice_number,
            "invoice_date": self.format_date(invoice.billed_date),
            "due_date": self.format_date(invoice.due_date),
            "description": invoice.description,
            "subtotal": self.format_currency(invoice.subtotal),
            "tax_type": invoice.tax_type,
            "tax_rate_display": f"{float(invoice.tax_rate * 100):.1f}%",
            "tax_amount": self.format_currency(invoice.tax_amount),
            "total": self.format_currency(invoice.total),
            
            # Payment info
            "payment_terms": settings.payment_terms,
            "payment_instructions": settings.payment_instructions or "",
        }
        
        # Render HTML
        html_content = template.render(**context)
        
        # Generate PDF
        pdf_file = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_file)
        pdf_file.seek(0)
        
        return pdf_file.read()
    
    def get_filename(self, invoice: Invoice) -> str:
        """Generate filename for invoice PDF."""
        return f"Invoice-{invoice.invoice_number}.pdf"
