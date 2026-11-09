"""Financial Integrity and Compliance Rules Validator for Invoices."""

from datetime import datetime
import re
from typing import List
from models import (
    InvoiceData,
    ProcessingStatus,
    ValidationReport,
    ValidationRuleResult,
)


class InvoiceValidator:
    """Performs deterministic financial checks, checksum validations, and confidence evaluation."""

    @staticmethod
    def validate_nif_pt(nif: str) -> bool:
        """Validates Portuguese NIF checksum (9 digits)."""
        clean = re.sub(r"[^\d]", "", nif or "")
        if len(clean) != 9:
            return False
        if clean[0] not in "1235689":
            return False

        check_sum = sum(int(clean[i]) * (9 - i) for i in range(8))
        rem = check_sum % 11
        check_digit = 0 if rem in (0, 1) else (11 - rem)
        return check_digit == int(clean[8])

    @staticmethod
    def validate_cnpj_br(cnpj: str) -> bool:
        """Validates Brazilian CNPJ checksum (14 digits)."""
        clean = re.sub(r"[^\d]", "", cnpj or "")
        if len(clean) != 14 or len(set(clean)) == 1:
            return False

        def calc_digit(slice_str, weights):
            s = sum(int(a) * w for a, w in zip(slice_str, weights))
            rem = s % 11
            return 0 if rem < 2 else 11 - rem

        w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        d1 = calc_digit(clean[:12], w1)
        w2 = [6] + w1
        d2 = calc_digit(clean[:12] + str(d1), w2)
        return clean[-2:] == f"{d1}{d2}"

    @classmethod
    def validate_tax_id(cls, tax_id: str) -> bool:
        """Checks if tax ID matches valid PT NIF or BR CNPJ pattern or basic syntax."""
        if not tax_id:
            return False
        clean = re.sub(r"[^\d]", "", tax_id)
        if len(clean) == 9:
            return cls.validate_nif_pt(clean)
        elif len(clean) == 14:
            return cls.validate_cnpj_br(clean)
        return len(clean) >= 8  # Generic international tax id fallback

    @classmethod
    def validate(cls, invoice: InvoiceData, extraction_confidence: float = 1.0) -> ValidationReport:
        """Runs full validation pipeline against an invoice."""
        results: List[ValidationRuleResult] = []
        reasons: List[str] = []

        # Rule 1: Invoice Number Presence
        has_inv_num = bool(invoice.invoice_number and invoice.invoice_number != "UNKNOWN-000")
        results.append(
            ValidationRuleResult(
                rule_name="INVOICE_NUMBER_PRESENT",
                passed=has_inv_num,
                severity="ERROR" if not has_inv_num else "INFO",
                message="Invoice number identified" if has_inv_num else "Missing or invalid invoice number.",
            )
        )
        if not has_inv_num:
            reasons.append("Invoice number could not be identified.")

        # Rule 2: Issuer Tax ID Validity
        issuer_tax = invoice.issuer.tax_id
        is_tax_valid = cls.validate_tax_id(issuer_tax) if issuer_tax else False
        results.append(
            ValidationRuleResult(
                rule_name="ISSUER_TAX_ID_VALIDITY",
                passed=is_tax_valid,
                severity="WARNING" if not is_tax_valid else "INFO",
                message=f"Issuer Tax ID ({issuer_tax}) valid" if is_tax_valid else f"Issuer Tax ID ({issuer_tax}) is missing or invalid checksum.",
            )
        )
        if not is_tax_valid:
            reasons.append(f"Issuer Tax ID ({issuer_tax or 'None'}) failed validation check.")

        # Rule 3: Date Consistency (due_date >= issue_date)
        date_rule_passed = True
        date_msg = "Dates are chronologically sound"
        if invoice.issue_date and invoice.due_date:
            try:
                def parse_dt(d_str):
                    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
                        try:
                            return datetime.strptime(d_str, fmt)
                        except ValueError:
                            pass
                    return None

                d_issue = parse_dt(invoice.issue_date)
                d_due = parse_dt(invoice.due_date)
                if d_issue and d_due and d_due < d_issue:
                    date_rule_passed = False
                    date_msg = f"Due date ({invoice.due_date}) is earlier than issue date ({invoice.issue_date})."
            except Exception:
                pass
        results.append(
            ValidationRuleResult(
                rule_name="DATES_CHRONOLOGY",
                passed=date_rule_passed,
                severity="ERROR" if not date_rule_passed else "INFO",
                message=date_msg,
            )
        )
        if not date_rule_passed:
            reasons.append(date_msg)

        # Rule 4: Arithmetic Integrity (Line Items Sum vs Subtotal/Total)
        arithmetic_passed = True
        arithmetic_msg = "Financial arithmetic verified"
        if invoice.line_items:
            sum_items = sum(item.total for item in invoice.line_items)
            # If line item total differs significantly from subtotal
            diff = abs(sum_items - invoice.financials.subtotal)
            if diff > 0.05 and invoice.financials.subtotal > 0:
                arithmetic_passed = False
                arithmetic_msg = f"Sum of line items ({sum_items:.2f}) does not match subtotal ({invoice.financials.subtotal:.2f})."
        else:
            # Check subtotal + tax = total
            calc_total = invoice.financials.subtotal + invoice.financials.tax_amount
            if abs(calc_total - invoice.financials.total_amount) > 0.05 and invoice.financials.total_amount > 0:
                arithmetic_passed = False
                arithmetic_msg = f"Subtotal + tax ({calc_total:.2f}) diverges from total amount ({invoice.financials.total_amount:.2f})."

        results.append(
            ValidationRuleResult(
                rule_name="ARITHMETIC_CONSISTENCY",
                passed=arithmetic_passed,
                severity="ERROR" if not arithmetic_passed else "INFO",
                message=arithmetic_msg,
            )
        )
        if not arithmetic_passed:
            reasons.append(arithmetic_msg)

        # Rule 5: Non-zero Total
        has_positive_total = invoice.financials.total_amount > 0.0
        results.append(
            ValidationRuleResult(
                rule_name="POSITIVE_TOTAL",
                passed=has_positive_total,
                severity="ERROR" if not has_positive_total else "INFO",
                message="Invoice has positive payable total" if has_positive_total else "Invoice total amount is zero or negative.",
            )
        )
        if not has_positive_total:
            reasons.append("Invoice total is zero or missing.")

        # Determine Global Validity and Routing Status
        errors = [r for r in results if not r.passed and r.severity == "ERROR"]
        warnings = [r for r in results if not r.passed and r.severity == "WARNING"]

        is_valid = len(errors) == 0
        final_confidence = extraction_confidence
        if warnings:
            final_confidence = max(0.2, final_confidence - 0.15)
        if errors:
            final_confidence = max(0.1, final_confidence - 0.35)

        # Straight-Through Processing (STP) Decision Gate
        if is_valid and final_confidence >= 0.85 and not warnings:
            status = ProcessingStatus.APPROVED
        elif is_valid and not errors:
            status = ProcessingStatus.PENDING_REVIEW  # Auditor exception review
        else:
            status = ProcessingStatus.PENDING_REVIEW  # Exceptions route to HITL queue

        return ValidationReport(
            is_valid=is_valid,
            status=status,
            confidence_score=round(final_confidence, 2),
            reasons=reasons,
            rule_results=results,
        )
