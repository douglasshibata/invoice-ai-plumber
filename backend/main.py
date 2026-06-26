from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from fpdf import FPDF
import io
from fastapi.responses import StreamingResponse
import json

app = FastAPI(title="Plumber Invoice AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvoiceRequest(BaseModel):
    raw_notes: str
    client_name: str
    client_email: Optional[str] = None
    plumber_name: str = "Expert Plumbing Services"

@app.post("/generate-invoice")
async def generate_invoice(request: InvoiceRequest):
    # In a real app, this would call OpenAI/Gemini
    # For the MVP, we use a structured template + simple logic to "AI-ify" the notes

    # Mock AI Processing
    processed_items = [
        {"description": "Emergency Leak Repair - Kitchen Sink", "quantity": 1, "unit_price": 150.0},
        {"description": "Copper Pipe Fittings and Sealant", "quantity": 3, "unit_price": 12.50},
        {"description": "Labor - 2 Hours", "quantity": 2, "unit_price": 85.0}
    ]

    total = sum(item["quantity"] * item["unit_price"] for item in processed_items)

    invoice_data = {
        "client": request.client_name,
        "plumber": request.plumber_name,
        "items": processed_items,
        "total": total,
        "notes": f"Generated from: {request.raw_notes[:50]}..."
    }

    return invoice_data

@app.post("/export-pdf")
async def export_pdf(data: dict = Body(...)):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(40, 10, f"INVOICE: {data.get('plumber', 'Plumbing Service')}")
    pdf.ln(10)

    pdf.set_font("Arial", "", 12)
    pdf.cell(40, 10, f"Bill To: {data.get('client', 'Customer')}")
    pdf.ln(20)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, "Description", 1)
    pdf.cell(30, 10, "Qty", 1)
    pdf.cell(30, 10, "Price", 1)
    pdf.cell(30, 10, "Total", 1)
    pdf.ln()

    pdf.set_font("Arial", "", 12)
    for item in data.get("items", []):
        line_total = item['quantity'] * item['unit_price']
        pdf.cell(100, 10, item['description'], 1)
        pdf.cell(30, 10, str(item['quantity']), 1)
        pdf.cell(30, 10, f"${item['unit_price']:.2f}", 1)
        pdf.cell(30, 10, f"${line_total:.2f}", 1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(160, 10, "GRAND TOTAL", 0)
    pdf.cell(30, 10, f"${data.get('total', 0):.2f}", 0)

    pdf_output = io.BytesIO()
    pdf_str = pdf.output(dest='S')
    if isinstance(pdf_str, str):
        pdf_output.write(pdf_str.encode('latin1'))
    else:
        pdf_output.write(pdf_str)

    pdf_output.seek(0)
    return StreamingResponse(pdf_output, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=invoice.pdf"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
