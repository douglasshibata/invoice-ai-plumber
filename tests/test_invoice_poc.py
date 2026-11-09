"""Automated tests for Backoffice Financeiro Invoice Processing PoC."""

import io
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from extractor import InvoiceExtractor
from main import app, PROCESSED_INVOICES
from models import ProcessingStatus
from sample_generator import create_sample_invoice_pdf
from validator import InvoiceValidator


@pytest.fixture(autouse=True)
def clear_db():
    PROCESSED_INVOICES.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_sample_generator_valid():
    """Tests synthetic PDF generation and basic integrity."""
    pdf_bytes = create_sample_invoice_pdf()
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_extractor_and_validator_valid_pdf():
    """Tests end-to-end extraction and STP approval of a valid invoice."""
    pdf_bytes = create_sample_invoice_pdf(
        invoice_number="FAT-2025-9988",
        issuer_name="Cloud Hosting Lda",
        issuer_tax="509123457",  # Valid checksum
        recipient_name="Enterprise Systems S.A.",
        issue_date="2025-03-01",
        due_date="2025-03-31",
    )

    invoice_data, confidence = InvoiceExtractor.extract_from_bytes(pdf_bytes, "valid_test.pdf")
    assert invoice_data.invoice_number == "FAT-2025-9988"
    assert invoice_data.issuer.name == "Cloud Hosting Lda"
    assert invoice_data.financials.total_amount > 0

    report = InvoiceValidator.validate(invoice_data, confidence)
    assert report.is_valid is True
    assert report.status == ProcessingStatus.APPROVED
    assert report.confidence_score >= 0.85


def test_validator_detects_arithmetic_divergence():
    """Tests that mismatched line items or totals route invoice to pending_review."""
    pdf_bytes = create_sample_invoice_pdf(deliberate_error="ARITHMETIC_ERROR")
    invoice_data, confidence = InvoiceExtractor.extract_from_bytes(pdf_bytes, "arithmetic_err.pdf")
    report = InvoiceValidator.validate(invoice_data, confidence)

    # Arithmetic mismatch should fail the ARITHMETIC_CONSISTENCY rule
    rule_map = {r.rule_name: r.passed for r in report.rule_results}
    assert rule_map.get("ARITHMETIC_CONSISTENCY") is False
    assert report.status == ProcessingStatus.PENDING_REVIEW


def test_validator_detects_invalid_dates():
    """Tests that due date prior to issue date is caught by compliance validator."""
    pdf_bytes = create_sample_invoice_pdf(deliberate_error="DATES_ERROR")
    invoice_data, confidence = InvoiceExtractor.extract_from_bytes(pdf_bytes, "dates_err.pdf")
    report = InvoiceValidator.validate(invoice_data, confidence)

    rule_map = {r.rule_name: r.passed for r in report.rule_results}
    assert rule_map.get("DATES_CHRONOLOGY") is False
    assert report.status == ProcessingStatus.PENDING_REVIEW


def test_validator_nif_and_cnpj_algorithms():
    """Unit tests for Portuguese NIF and Brazilian CNPJ checksums."""
    # Portuguese NIF (509123457 is valid, 509123458 fails check digit)
    assert InvoiceValidator.validate_nif_pt("509123457") is True
    assert InvoiceValidator.validate_nif_pt("509123458") is False
    assert InvoiceValidator.validate_nif_pt("invalid") is False

    # Brazilian CNPJ
    # Valid CNPJ: 11.222.333/0001-81
    assert InvoiceValidator.validate_cnpj_br("11222333000181") is True
    assert InvoiceValidator.validate_cnpj_br("11111111111111") is False


def test_api_upload_and_metrics(client):
    """Tests FastAPI upload endpoint and live metrics calculation."""
    pdf_bytes = create_sample_invoice_pdf(invoice_number="FAT-API-101")
    response = client.post(
        "/api/v1/invoices/upload",
        files={"file": ("fat_api_101.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["invoice_data"]["invoice_number"] == "FAT-API-101"
    inv_id = res_data["invoice_id"]

    # Check metrics
    metrics_res = client.get("/api/v1/invoices/metrics")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["total_invoices_processed"] == 1
    assert metrics["stp_auto_approved"] == 1
    assert metrics["stp_rate_percentage"] == 100.0


def test_api_hitl_audit_approval(client):
    """Tests human auditor exception resolution via /api/v1/invoices/audit-approve."""
    pdf_bytes = create_sample_invoice_pdf(deliberate_error="ARITHMETIC_ERROR")
    upload_res = client.post(
        "/api/v1/invoices/upload",
        files={"file": ("error_inv.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    inv_id = upload_res.json()["invoice_id"]
    assert upload_res.json()["validation"]["status"] == "pending_review"

    # Human auditor approves the exception
    audit_res = client.post(
        "/api/v1/invoices/audit-approve",
        json={"invoice_id": inv_id, "auditor_notes": "Correção autorizada pelo financeiro"},
    )
    assert audit_res.status_code == 200
    assert audit_res.json()["validation"]["status"] == "manually_approved"
    assert audit_res.json()["validation"]["is_valid"] is True


def test_legacy_endpoints_backward_compatibility(client):
    """Ensures legacy plumber endpoints remain operational."""
    res = client.post("/generate-invoice", json={"raw_notes": "Pipe repair 2 hours", "client_name": "John Doe"})
    assert res.status_code == 200
    assert res.json()["client"] == "John Doe"
    assert res.json()["total"] > 0
