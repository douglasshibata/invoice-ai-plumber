# PlumbInvoice AI & Corporate Invoice Processing Platform 🪠📑✨

PlumbInvoice AI is an end-to-end intelligent invoice generation and processing platform. Originally a Micro-SaaS tool designed for field contractors, it now features an **Enterprise Backoffice Financeiro PoC Engine** for autonomous accounts payable ingestion, `pdfplumber` layout extraction, deterministic compliance validation, and Human-in-the-Loop (HITL) exception audit.

---

## 🚀 The Enterprise Backoffice Problem
Accounts Payable (AP) and finance departments spend days manually checking scanned or native PDF invoices, calculating line-item sums against grand totals, validating Tax IDs, and typing invoice data into ERPs. This manual overhead causes delayed month-end closes and exposes organizations to costly late-payment penalties and human data-entry errors.

## 💡 The Enterprise PoC Solution
An automated, deterministic, and audit-ready document processing pipeline:
1. **Intelligent Ingestion:** Ingests native or scanned PDF invoices via REST API (`/api/v1/invoices/upload`) or drag-and-drop web UI.
2. **Hybrid Layout Extraction (`pdfplumber`):** Extracts metadata (Issuer, Recipient, NIF/CNPJ, Dates, Currencies) and itemized tables with coordinate layout heuristics and zero external API dependencies.
3. **Deterministic Financial Validation:**
   - **Arithmetic Checks:** Validates $\sum(\text{Line Items}) == \text{Subtotal}$ and $\text{Subtotal} + \text{Tax} == \text{Total}$.
   - **Chronology Rules:** Verifies that due dates are greater than or equal to issue dates.
   - **Tax ID Checksums:** Implements checksum validation for Portuguese NIF (9 digits) and Brazilian CNPJ (14 digits).
4. **Straight-Through Processing (STP) vs. HITL Exception Routing:**
   - Invoices passing all rules with confidence score $\ge 85\%$ are auto-approved directly for ERP ingestion.
   - Flagged invoices (arithmetic mismatch, invalid dates, unverified Tax IDs) route to a dedicated **Human-in-the-Loop Exception Queue** with 1-click audit approval.

---

## 🛠️ Quick Start

### 1. Backend (FastAPI)
```bash
cd invoice-ai-plumber/backend
pip install -r requirements.txt
python main.py
```
Server runs at: `http://localhost:8001` (Interactive Swagger docs: `http://localhost:8001/docs`).

### 2. PoC Backoffice Financeiro Dashboard
Simply open `invoice-ai-plumber/frontend/poc_dashboard.html` in your web browser.
* Live KPI metrics banner: Total Invoices Processed, STP Automation Rate, Exception Queue count, Total Volume.
* Quick test buttons: Generate and process synthetic valid invoices, arithmetic mismatch invoices, inverted date invoices, or invalid NIF invoices in 1 click.
* Interactive Exception Queue with 1-click auditor approval.

### 3. Classic Micro-SaaS Interface
Open `invoice-ai-plumber/frontend/index.html` for the plumber invoice generation interface.

---

## 🧪 Automated Testing
Run the comprehensive test suite verifying extraction, mathematical validation, and API endpoints:
```bash
python3 -m pytest invoice-ai-plumber/tests/test_invoice_poc.py -v
```

---

## 🏛️ PoC Architecture Diagram

```
                     ┌──────────────────────────────────────────────┐
                     │          Canais de Entrada (Ingestão)        │
                     │  - Upload via Web App / Portal Fornecedor    │
                     │  - REST API Multipart (POST /upload)         │
                     └──────────────────────┬───────────────────────┘
                                            │
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │       Motor de Extração (pdfplumber)         │
                     │  - Extração de texto e coordenadas           │
                     │  - Parsing de tabelas e itens de linha       │
                     │  - Cálculo de Score de Confiança             │
                     └──────────────────────┬───────────────────────┘
                                            │
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │         Regras de Validação & Compliance     │
                     │  - Checksum NIF (PT) / CNPJ (BR)             │
                     │  - Conferência matemática (Itens vs Total)   │
                     │  - Consistência cronológica de datas         │
                     └──────────────┬───────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
       [Score >= 85% & Sem Erros]          [Discrepância / Erro]
                    │                               │
                    ▼                               ▼
       ┌────────────────────────┐      ┌────────────────────────┐
       │   Aprovação Automática │      │   Fila de Exceções     │
       │   (STP) para o ERP     │      │   Auditoria Humana     │
       └────────────────────────┘      │   (Dashboard HITL)     │
                                       └───────────┬────────────┘
                                                   │
                                                   ▼
                                       ┌────────────────────────┐
                                       │  Validação Manual      │
                                       │  (1-Click Approval)    │
                                       └────────────────────────┘
```

---

## 🧰 Tech Stack
- **Backend:** Python 3.12, FastAPI, Uvicorn, Pydantic v2, `pdfplumber`, `fpdf2`
- **Frontend:** Vanilla HTML5, Tailwind CSS, FontAwesome
- **Test Suite:** Pytest, HTTPX, FastAPI TestClient
