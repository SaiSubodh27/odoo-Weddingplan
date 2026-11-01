# Implementation Progress - The Royal Knot

## Step 1: Gap Check
- Comprehensive gap check completed. Initial checklist and gap matrix established.

## Step 2: Build Remaining Work
- **P0 Item 1: Agreement Gate (COMPLETED)**
  - Unified AgreementService with in-app client OTP signing (10-min expiry, 5 attempts, SHA-256 hashed) and agency electronic signature workflows (Zoho Sign & Leegality).
  - Digital signature PDF generation with cryptographic SHA-256 audit block, timestamp, IP, User Agent, and consent tracking.
  - Idempotent signature handling: re-signing returns existing signed agreement record.
  - Backend `require_signed_agreement` middleware enforcing 403 `AGREEMENT_REQUIRED` + `X-Agreement-Required: true`.
  - Frontend auto-redirect to `/agreement` via `ProtectedRoute` and global fetch interceptor.
  - Planners can access and download executed signed PDF.
  - 37/37 tests passing (`test_service_agreement_otp_signing.py`, `test_zoho_sign_polling.py`, `test_service_agreement_workflow.py`).

- **P0 Item 2: Quotes & Multi-Vendor RFQ Comparison (COMPLETED)**
  - Added multi-vendor RFQ dispatch endpoint `POST /api/v1/catering/{id}/rfq` creating quotes and communication logs.
  - Implemented itemized quotation line items with decimal-safe costing engine and normalized price-per-plate calculation.
  - Implemented side-by-side comparison endpoint `GET /api/v1/catering/{id}/quotations/compare` returning vendor ratings, normalized rates, breakdowns, and lowest-price indicators.
  - Implemented atomic "select winner" transaction: winning quote -> Accepted, competing quotes -> Closed, catering plan updated, and vendor linked directly to wedding project in `project_vendors` in one single DB transaction.
  - 4/4 tests passing (`backend/tests/test_p0_quotes_comparison.py`).

- **P0 Item 3: Deposit -> Plan Generation (COMPLETED)**
  - Added `PlanningTask` and `PaymentStage` models with relationships to `WeddingProject`.
  - Added `deposit_paid` and `deposit_paid_at` tracking to `WeddingProject`.
  - Implemented `POST /api/v1/projects/{project_id}/deposit-paid`:
    - Generates 25+ tasks from package template (28 tasks for Full-Service, 25 tasks for Partial Planning) covering Venue, Design, Vendors, Mehendi, Sangeet, Wedding Day, Reception.
    - Each task assigned an owner and stage ("To Plan" -> "In Progress" -> "Done") with due dates computed relative to wedding date.
    - Creates 3 payment stages: Retainer Deposit (25%, Paid), Advance Production (40%, due wedding date - 30 days, Pending), Final Settlement (35%, due wedding date + 3 days, Pending).
    - Idempotent: replaying deposit_paid creates no duplicate tasks and no duplicate payment milestones.
  - Implemented tasks listing (`GET /api/v1/projects/{id}/tasks`), task stage update (`PATCH /api/v1/projects/{id}/tasks/{id}`), and payment stages endpoints.
  - Tests passing (`backend/tests/test_p0_deposit_plan_generation.py`).

- **P0 Item 4: Founder Gross Profit Calculation per Wedding (COMPLETED)**
  - Added `TeamTimeEntry` model for minimal time tracking (hours x hourly_rate, employee, role, task, date).
  - Implemented time tracking endpoints (`POST /api/v1/projects/{id}/time-entries` and `GET /api/v1/projects/{id}/time-entries`).
  - Implemented profitability engine `GET /api/v1/projects/{id}/profitability`:
    - Founder Gross Profit = client payments received - vendor contracted costs - team labor costs (hours x rate).
    - Profit Margin Percentage = (founder_gross_profit / client_payments_received) * 100.
  - Verified with hand-written expected numbers in tests (`backend/tests/test_p0_founder_profit.py`).
