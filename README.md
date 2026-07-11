# PlumbInvoice AI 🪠✨

PlumbInvoice AI is a specialized Micro-SaaS tool designed for plumbers to turn messy, voice-to-text or handwritten notes into professional, itemized PDF invoices in seconds.

## 🚀 The Problem
Plumbers often finish a job and have to spend hours at night typing up invoices or manual notes, leading to delayed payments and a poor professional image.

## 💡 The Solution
A simple AI wrapper that:
1. Takes raw job notes (e.g., "fixed leak, 2h, replaced 3 pipes").
2. Uses LLM intelligence to categorize items and estimate fair pricing.
3. Generates a professional PDF ready to be emailed to the client.

## 🛠️ Quick Start

### Backend (FastAPI)
```bash
cd backend
pip install fastapi uvicorn fpdf2
python main.py
```
Server runs at: `http://localhost:8001`

### Frontend
Simply open `invoice-ai-plumber/frontend/index.html` in your browser.

## 💰 Monetization Plan (MRR Focus)

*   **Free Tier:** 3 invoices per month.
*   **Pro Tier ($19/mo):** Unlimited invoices, custom branding/logo, and automatic email delivery.
*   **Enterprise ($49/mo):** Multi-plumber support, QuickBooks integration, and performance analytics.

## 📈 Marketing Strategy
*   **Cold Outreach:** Contact local plumbing businesses on Yelp/Google Maps offering a 1-month free trial.
*   **Niche SEO:** "Invoice automation for plumbers", "Plumbing business software free".
*   **TikTok/Shorts:** Record "Satisfying" videos of messy notes turning into clean invoices in 1 click.

---

## 🛠️ Project Deep Dive & Technical Guide

### 🎯 Main Purpose
Turn messy, raw job notes into formatted, itemized professional PDF invoices for plumbers.

### 🧰 Tecnologias Utilizadas (Tech Stack)
- **Primary Technologies:** Python 3.12 (FastAPI, fpdf2), HTML5, JavaScript
- **Deployment Strategy:** Standalone local deployment or standard web server for the static frontend.

### 🚀 Como Implantar e Executar (How to Deploy & Run)
#### Python FastAPI Backend
1. Navigate to the `backend` directory.
2. Install dependencies: `pip install fastapi uvicorn fpdf2`.
3. Run the backend server: `python main.py` (or `uvicorn main:app --port 8001`).

#### Static Frontend
1. Open the file `frontend/index.html` in any web browser.

---
