"""Generates synthetic test PDF invoices for demonstration and benchmarking."""

import io
from fpdf import FPDF


def create_sample_invoice_pdf(
    invoice_number: str = "FAT-2025-1042",
    issuer_name: str = "Tech Cloud Solutions Lda",
    issuer_tax: str = "509123457",  # Valid PT NIF format (checksum 7)
    recipient_name: str = "Enterprise Global Corp",
    recipient_tax: str = "501987654",
    issue_date: str = "2025-03-01",
    due_date: str = "2025-03-31",
    items: list = None,
    tax_rate: float = 0.23,
    currency: str = "EUR",
    deliberate_error: str = None,
) -> bytes:
    """Creates a well-formed or deliberately perturbed PDF invoice.

    deliberate_error options:
        - "ARITHMETIC_ERROR": corrupts subtotal
        - "DATES_ERROR": due date earlier than issue date
        - "INVALID_TAX": invalid NIF/tax format
    """
    if items is None:
        items = [
            ("DevOps Cloud Architecture Consulting", 10.0, 120.00),
            ("Kubernetes Cluster Maintenance & Security", 1.0, 450.00),
            ("Automated CI/CD Pipeline Setup", 2.0, 300.00),
        ]

    if deliberate_error == "DATES_ERROR":
        due_date = "2025-02-15"  # Earlier than issue_date 2025-03-01
    if deliberate_error == "INVALID_TAX":
        issuer_tax = "509123458"  # Fails PT NIF checksum (expected 7, received 8)

    subtotal = sum(q * p for _, q, p in items)
    if deliberate_error == "ARITHMETIC_ERROR":
        subtotal += 500.00  # Diverges from sum of items

    tax_amount = subtotal * tax_rate
    grand_total = subtotal + tax_amount

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "FATURA COMERCIAL / INVOICE", ln=True, align="C")
    pdf.ln(5)

    # Document details & Parties
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(100, 6, f"EMISSOR: {issuer_name}", ln=False)
    pdf.cell(90, 6, f"DOC: {invoice_number}", ln=True, align="R")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(100, 6, f"NIF/NIPC: {issuer_tax}", ln=False)
    pdf.cell(90, 6, f"EMISSÃO: {issue_date}", ln=True, align="R")

    pdf.cell(100, 6, f"CLIENTE: {recipient_name}", ln=False)
    pdf.cell(90, 6, f"VENCIMENTO: {due_date}", ln=True, align="R")

    if recipient_tax:
        pdf.cell(100, 6, f"NIF CLIENTE: {recipient_tax}", ln=True)

    pdf.ln(10)

    # Table Header
    pdf.set_fill_color(230, 235, 245)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 8, "Descrição", border=1, fill=True)
    pdf.cell(25, 8, "Qtd", border=1, align="C", fill=True)
    pdf.cell(35, 8, f"Preço ({currency})", border=1, align="R", fill=True)
    pdf.cell(35, 8, f"Total ({currency})", border=1, align="R", fill=True)
    pdf.ln()

    # Items
    pdf.set_font("Helvetica", "", 10)
    for desc, qty, price in items:
        line_total = qty * price
        pdf.cell(95, 7, desc, border=1)
        pdf.cell(25, 7, f"{qty:.1f}", border=1, align="C")
        pdf.cell(35, 7, f"{price:.2f}", border=1, align="R")
        pdf.cell(35, 7, f"{line_total:.2f}", border=1, align="R")
        pdf.ln()

    pdf.ln(6)

    # Financial Summary
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(120, 6, "", ln=False)
    pdf.cell(35, 6, "Subtotal:", align="R")
    pdf.cell(35, 6, f"{subtotal:.2f} {currency}", align="R", ln=True)

    pdf.cell(120, 6, "", ln=False)
    pdf.cell(35, 6, f"IVA ({int(tax_rate*100)}%):", align="R")
    pdf.cell(35, 6, f"{tax_amount:.2f} {currency}", align="R", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(120, 8, "", ln=False)
    pdf.cell(35, 8, "TOTAL GERAL:", align="R")
    pdf.cell(35, 8, f"{grand_total:.2f} {currency}", align="R", ln=True)

    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "Processado por Sistema Integrado de Faturação Eletrónica Certificada.", align="C")

    # In fpdf2, output() returns bytes directly
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes)
