import io
import json
import uuid
from typing import Dict, List, Optional
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fpdf import FPDF
from pydantic import BaseModel
import uvicorn

from extractor import InvoiceExtractor
from models import (
    ExtractionResponse,
    InvoiceData,
    ProcessingStatus,
    ValidationReport,
)
from sample_generator import create_sample_invoice_pdf
from validator import InvoiceValidator

app = FastAPI(
    title="Corporate Invoice AI & Document Processing Platform (Backoffice Financeiro PoC)",
    description="Enterprise-grade invoice processing engine with pdfplumber extraction, financial integrity validation, and Human-in-the-Loop exception audit.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# In-Memory Database for PoC tracking & metrics
# -------------------------------------------------------------
PROCESSED_INVOICES: Dict[str, ExtractionResponse] = {}


class LegacyInvoiceRequest(BaseModel):
    raw_notes: str
    client_name: str
    client_email: Optional[str] = None
    plumber_name: str = "Expert Plumbing Services"


class AuditApprovalRequest(BaseModel):
    invoice_id: str
    auditor_notes: Optional[str] = "Approved by human auditor in exception queue"
    corrected_total: Optional[float] = None


# -------------------------------------------------------------
# Legacy Micro-SaaS Endpoints (Backward Compatible)
# -------------------------------------------------------------
@app.post("/generate-invoice")
async def generate_invoice(request: LegacyInvoiceRequest):
    processed_items = [
        {"description": "Emergency Leak Repair - Kitchen Sink", "quantity": 1, "unit_price": 150.0},
        {"description": "Copper Pipe Fittings and Sealant", "quantity": 3, "unit_price": 12.50},
        {"description": "Labor - 2 Hours", "quantity": 2, "unit_price": 85.0},
    ]

    total = sum(item["quantity"] * item["unit_price"] for item in processed_items)

    invoice_data = {
        "client": request.client_name,
        "plumber": request.plumber_name,
        "items": processed_items,
        "total": total,
        "notes": f"Generated from: {request.raw_notes[:50]}...",
    }

    return invoice_data


@app.post("/export-pdf")
async def export_pdf(data: dict = Body(...)):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(40, 10, f"INVOICE: {data.get('plumber', 'Plumbing Service')}")
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(40, 10, f"Bill To: {data.get('client', 'Customer')}")
    pdf.ln(20)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(100, 10, "Description", 1)
    pdf.cell(30, 10, "Qty", 1)
    pdf.cell(30, 10, "Price", 1)
    pdf.cell(30, 10, "Total", 1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 12)
    for item in data.get("items", []):
        line_total = item["quantity"] * item["unit_price"]
        pdf.cell(100, 10, str(item["description"]), 1)
        pdf.cell(30, 10, str(item["quantity"]), 1)
        pdf.cell(30, 10, f"${item['unit_price']:.2f}", 1)
        pdf.cell(30, 10, f"${line_total:.2f}", 1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(160, 10, "GRAND TOTAL", 0)
    pdf.cell(30, 10, f"${data.get('total', 0):.2f}", 0)

    pdf_bytes = bytes(pdf.output())
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=invoice.pdf"},
    )


# -------------------------------------------------------------
# Enterprise PoC Endpoints (Backoffice Financeiro)
# -------------------------------------------------------------
@app.post("/api/v1/invoices/upload", response_model=ExtractionResponse)
async def upload_invoice(file: UploadFile = File(...)):
    """Uploads a PDF invoice, parses text & tables with pdfplumber, and runs compliance rules."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    filename = file.filename or "invoice.pdf"
    invoice_data, confidence = InvoiceExtractor.extract_from_bytes(content, filename)
    validation_report = InvoiceValidator.validate(invoice_data, confidence)

    invoice_id = str(uuid.uuid4())[:8]
    record = ExtractionResponse(
        invoice_id=invoice_id,
        filename=filename,
        invoice_data=invoice_data,
        validation=validation_report,
    )
    PROCESSED_INVOICES[invoice_id] = record
    return record


@app.post("/api/v1/invoices/validate", response_model=ValidationReport)
async def validate_invoice_json(invoice: InvoiceData):
    """Directly tests validation rules against an invoice payload without PDF upload."""
    return InvoiceValidator.validate(invoice, 1.0)


@app.get("/api/v1/invoices/list", response_model=List[ExtractionResponse])
async def list_invoices():
    """Returns all processed invoices in the current session."""
    return list(PROCESSED_INVOICES.values())


@app.post("/api/v1/invoices/audit-approve", response_model=ExtractionResponse)
async def audit_approve_invoice(req: AuditApprovalRequest):
    """Human-in-the-Loop (HITL) approval endpoint for invoices flagged in the exception queue."""
    if req.invoice_id not in PROCESSED_INVOICES:
        raise HTTPException(status_code=404, detail=f"Invoice ID {req.invoice_id} not found")

    item = PROCESSED_INVOICES[req.invoice_id]
    item.validation.status = ProcessingStatus.MANUALLY_APPROVED
    item.validation.is_valid = True
    item.validation.confidence_score = 1.0
    item.validation.reasons.append(f"[AUDITOR OVERRIDE]: {req.auditor_notes}")

    if req.corrected_total is not None:
        item.invoice_data.financials.total_amount = req.corrected_total

    PROCESSED_INVOICES[req.invoice_id] = item
    return item


@app.get("/api/v1/invoices/metrics")
async def get_metrics():
    """Computes PoC KPIs: STP Rate, Exception Queue count, Total processed, Financials volume."""
    invoices = list(PROCESSED_INVOICES.values())
    total = len(invoices)
    stp_approved = sum(1 for inv in invoices if inv.validation.status == ProcessingStatus.APPROVED)
    exceptions = sum(1 for inv in invoices if inv.validation.status == ProcessingStatus.PENDING_REVIEW)
    manually_approved = sum(1 for inv in invoices if inv.validation.status == ProcessingStatus.MANUALLY_APPROVED)
    rejected = sum(1 for inv in invoices if inv.validation.status == ProcessingStatus.REJECTED)

    total_value = sum(inv.invoice_data.financials.total_amount for inv in invoices)
    stp_rate = (stp_approved / total * 100) if total > 0 else 0.0

    return {
        "total_invoices_processed": total,
        "stp_auto_approved": stp_approved,
        "stp_rate_percentage": round(stp_rate, 1),
        "exceptions_pending_review": exceptions,
        "manually_approved": manually_approved,
        "rejected": rejected,
        "total_financial_volume": round(total_value, 2),
        "avg_confidence_score": round(
            sum(inv.validation.confidence_score for inv in invoices) / total, 2
        ) if total > 0 else 0.0,
    }


@app.get("/api/v1/invoices/sample-download/{sample_type}")
async def download_sample_pdf(sample_type: str = "valid"):
    """Downloads synthetic test PDFs for live benchmarking.

    sample_type options: 'valid', 'arithmetic_error', 'dates_error', 'invalid_tax'.
    """
    error_mode = None
    if sample_type == "arithmetic_error":
        error_mode = "ARITHMETIC_ERROR"
    elif sample_type == "dates_error":
        error_mode = "DATES_ERROR"
    elif sample_type == "invalid_tax":
        error_mode = "INVALID_TAX"

    pdf_bytes = create_sample_invoice_pdf(
        invoice_number=f"FAT-2025-{sample_type.upper()[:4]}",
        deliberate_error=error_mode,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=sample_{sample_type}.pdf"},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
