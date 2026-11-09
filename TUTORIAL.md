# 📘 Tutorial de Operação e Demonstração: PoC Backoffice Financeiro (Invoice AI Plumber)

Guia passo a passo para configuração, inicialização, execução de testes e demonstração ao vivo da **PoC de Processamento Inteligente de Faturas e Backoffice Financeiro** (`invoice-ai-plumber`).

---

## 🛠️ 1. Visão Geral e Arquitetura

O módulo combina a geração assistida de faturas com um motor corporativo de ingestão, extração via `pdfplumber`, validação determinística de regras fiscais (NIF/CNPJ) e roteamento inteligente com auditoria *Human-in-the-Loop* (HITL).

- **Backend:** Python 3.12 (FastAPI, Pydantic v2, `pdfplumber`, `fpdf2`, `uvicorn`)
- **Frontend PoC:** `invoice-ai-plumber/frontend/poc_dashboard.html`
- **Frontend Micro-SaaS:** `invoice-ai-plumber/frontend/index.html`
- **Porta Padrão:** `8001`

---

## 📋 2. Pré-requisitos do Sistema

- Python 3.11+ ou 3.12+
- `pip` atualizado
- Navegador moderno (Chrome, Firefox, Safari ou Edge)

---

## 🚀 3. Instalação e Execução

### Passo 1: Instalar dependências
```bash
cd invoice-ai-plumber/backend
pip install -r requirements.txt
```

### Passo 2: Iniciar o Servidor FastAPI
```bash
python main.py
```
O servidor estará disponível em `http://localhost:8001`. A documentação interativa Swagger pode ser acessada em `http://localhost:8001/docs`.

### Passo 3: Abrir o Dashboard da PoC
Abra o arquivo `invoice-ai-plumber/frontend/poc_dashboard.html` diretamente no seu navegador de preferência.

---

## 🎮 4. Roteiro de Demonstração para a Diretoria (Live Demo)

1. **Cenário 1: Processamento Direto (STP - Straight-Through Processing)**
   - No Dashboard da PoC, clique no botão **"Válida (STP)"** em "Faturas de Demonstração".
   - O sistema gera um PDF em tempo real, extrai os campos e valida as regras.
   - **Resultado:** Status **Aprovada (STP)** com Score de Confiança de 99%, sem necessidade de toque humano.

2. **Cenário 2: Detecção de Erro Aritmético (Prevenção de Fraude / Overbilling)**
   - Clique no botão **"Erro Soma"**.
   - O sistema detecta que o somatório dos itens de linha diverge do subtotal declarado na fatura.
   - **Resultado:** A fatura é direcionada imediatamente para a **Fila de Exceções (HITL)** para auditoria.

3. **Cenário 3: Resolução de Exceção com Aprovação Humana (HITL)**
   - Na tabela de auditoria, localize a fatura retida.
   - Clique em **"Aprovar (HITL)"** para simular o auditor financeiro validando a discrepância.
   - **Resultado:** A fatura passa ao status **Aprovada Auditor**, atualizando o volume financeiro auditado e as métricas de conformidade.

---

## 🧪 5. Execução de Testes Automatizados

Para rodar os testes unitários e de integração:

```bash
python3 -m pytest invoice-ai-plumber/tests/test_invoice_poc.py -v
```

Todos os 8 testes validam o pipeline de ponta a ponta:
- Extração precisa de PDFs nativos com `pdfplumber`.
- Validação algorítmica de NIF (Portugal) e CNPJ (Brasil).
- Detecção determinística de datas inconsistentes e erros matemáticos.
- Endpoints REST `/api/v1/invoices/upload`, `/metrics` e `/audit-approve`.
