"""Canonical Pydantic models for Corporate Invoice Extraction and Validation."""

from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    NATIVE_PDF = "native_pdf"
    SCANNED_PDF = "scanned_pdf"
    IMAGE = "image"
    MANUAL_ENTRY = "manual_entry"


class ProcessingStatus(str, Enum):
    APPROVED = "approved"                     # Auto-approved (STP)
    PENDING_REVIEW = "pending_review"         # Sent to Human-in-the-Loop review
    REJECTED = "rejected"                     # Discarded due to severe issues
    MANUALLY_APPROVED = "manually_approved"   # Auditor cleared exception


class LineItem(BaseModel):
    description: str
    quantity: float = Field(default=1.0, ge=0)
    unit_price: float = Field(default=0.0, ge=0)
    total: float = Field(default=0.0, ge=0)


class PartyInfo(BaseModel):
    name: str
    tax_id: Optional[str] = None  # NIF, CNPJ, or Tax ID
    address: Optional[str] = None
    email: Optional[str] = None


class FinancialSummary(BaseModel):
    subtotal: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = "EUR"


class InvoiceData(BaseModel):
    invoice_number: str
    document_type: DocumentType = DocumentType.NATIVE_PDF
    issuer: PartyInfo
    recipient: PartyInfo
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    financials: FinancialSummary
    line_items: List[LineItem] = Field(default_factory=list)
    raw_text_snippet: Optional[str] = None


class ValidationRuleResult(BaseModel):
    rule_name: str
    passed: bool
    severity: str = "ERROR"  # ERROR, WARNING, INFO
    message: str


class ValidationReport(BaseModel):
    is_valid: bool
    status: ProcessingStatus
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)
    rule_results: List[ValidationRuleResult] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    invoice_id: str
    filename: str
    invoice_data: InvoiceData
    validation: ValidationReport
