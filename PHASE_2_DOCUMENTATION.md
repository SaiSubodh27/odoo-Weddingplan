# The Royal Knot – Phase 2: Service Agreement & Wedding Booking Confirmation
## Architecture, Endpoints & Integration Documentation

> **Target Audience:** Engineering Leads, Full-Stack Developers, and QA Engineers  
> **Module Status:** Production-Ready, Tested (100% Pass across 60 automated tests), PR #1 Conflict-Free  
> **Key Technologies:** FastAPI (Python 3.11), SQLAlchemy 2.x, PostgreSQL 18, React 19, Vite, TypeScript, Tailwind CSS, ReportLab, Zoho Sign API & Polling Engine

---

## Table of Contents
1. [Overview & Business Workflow](#1-overview--business-workflow)
2. [State Machine & Agreement Lifecycle](#2-state-machine--agreement-lifecycle)
3. [Database Schema & Data Models](#3-database-schema--data-models)
4. [Complete Backend REST API Endpoints](#4-complete-backend-rest-api-endpoints)
   - [Metrics & Listing](#41-metrics--listing)
   - [Agreement Creation & Dossier](#42-agreement-creation--dossier)
   - [PDF Generation & Download](#43-pdf-generation--download)
   - [Internal Approval](#44-internal-approval)
   - [Electronic Signature (Zoho Sign)](#45-electronic-signature-zoho-sign)
   - [Signature Status & Polling Synchronization](#46-signature-status--polling-synchronization)
   - [Employee Verification](#47-employee-verification)
   - [Wedding Booking Confirmation & Phase 3 Handoff](#48-wedding-booking-confirmation--phase-3-handoff)
   - [Webhooks](#49-webhooks)
5. [Zoho Sign Integration & Polling Engine](#5-zoho-sign-integration--polling-engine)
6. [Frontend Routes & Components](#6-frontend-routes--components)
7. [Environment Configuration](#7-environment-configuration)
8. [Running & Testing the Project](#8-running--testing-the-project)

---

## 1. Overview & Business Workflow

Phase 2 bridges the gap between client registration (Phase 1) and full event project execution (Phase 3). Once a client enquiry is qualified and their profile is created, the agency prepares a formal, legally binding **Service Agreement**.

### End-to-End Workflow:
```
[Registered Client] 
        │
        ▼
[1. Create Service Agreement] ──> Draft created with milestones & GST breakdown
        │
        ▼
[2. Generate ReportLab PDF]   ──> Printable PDF generated with SHA-256 fingerprint
        │
        ▼
[3. Internal Staff Approval]  ──> Manager review & sign-off
        │
        ▼
[4. Dispatch to Zoho Sign]    ──> E-sign request sent (Mock mode or Zoho Sandbox/Prod)
        │
        ├── Polling Service (runs every 30s locally or on demand)
        ├── Webhook Listener (receives real-time Zoho events)
        │
        ▼
[5. Client Signs Agreement]   ──> Status -> COMPLETED; Signed PDF & Audit Certificate stored
        │
        ▼
[6. Employee Verification]    ──> Staff verifies signed contract, checks milestones
        │
        ▼
[7. Booking Confirmation]     ──> Wedding Booking confirmed; Dossier marked Phase 3 Handoff Ready
```

---

## 2. State Machine & Agreement Lifecycle

An agreement transitions through explicit statuses enforced by business validation:

| Agreement Status (`status`) | Signing Status (`signing_status`) | Description | Allowed Transitions |
|---|---|---|---|
| `DRAFT` | `NOT_CREATED` | Newly created agreement, terms can be updated | `PENDING_INTERNAL_APPROVAL`, `APPROVED_TO_SEND` |
| `PENDING_INTERNAL_APPROVAL` | `NOT_CREATED` | Awaiting management sign-off | `APPROVED_TO_SEND`, `DRAFT` |
| `APPROVED_TO_SEND` | `NOT_CREATED` | Approved internally, ready for e-signature | `SIGNING_PENDING`, `DRAFT` |
| `SIGNING_PENDING` | `SENT` / `VIEWED` | Dispatched to Zoho Sign; waiting for client | `SIGNED`, `DECLINED`, `EXPIRED` |
| `SIGNED` | `COMPLETED` | Client completed electronic signing | `UNDER_VERIFICATION` |
| `UNDER_VERIFICATION` | `COMPLETED` | Agency reviewing executed PDF & audit trail | `VERIFIED`, `NEEDS_CORRECTION` |
| `VERIFIED` | `COMPLETED` | Employee verified signatures and terms | `BOOKING_CONFIRMED` |
| `BOOKING_CONFIRMED` | `COMPLETED` | Wedding booking confirmed; Phase 3 ready | Terminal state |
| `DECLINED` / `EXPIRED` | `DECLINED` / `EXPIRED` | Signing failed or was rejected | `DRAFT` (revision allowed) |

---

## 3. Database Schema & Data Models

All models are defined in [`backend/app/models/agreement.py`](file:///c:/Users/sidar/OneDrive/Desktop/Odoo/odoo-Weddingplan/backend/app/models/agreement.py):

### 1. `service_agreements`
- `id` (VARCHAR 50, PK): e.g. `AGR-2026-0001`
- `agreement_number` (VARCHAR 50, UNIQUE)
- `client_id` (FK -> `clients.id`)
- `status` (VARCHAR 50): Agreement lifecycle status
- `signing_status` (VARCHAR 50): E-signature provider status
- `wedding_date` (DATE), `wedding_location` (VARCHAR), `venue` (VARCHAR)
- `guest_count` (INTEGER), `wedding_functions` (JSON)
- `service_package` (VARCHAR), `included_services` (JSON), `excluded_services` (JSON), `deliverables` (JSON)
- `package_price`, `tax_percentage`, `tax_amount`, `discount_amount`, `total_amount` (NUMERIC 15,2)
- `current_version_number` (INT)
- `is_internally_approved` (BOOL), `approved_by` (VARCHAR), `approved_at` (TIMESTAMP)
- `is_verified` (BOOL), `verified_by` (VARCHAR), `verified_at` (TIMESTAMP)
- `is_deleted` (BOOL, soft-deletion)

### 2. `service_agreement_versions`
Immutable version snapshots. Whenever an agreement is revised, a new version is recorded with `snapshot_data` (JSON) and SHA-256 PDF hash.

### 3. `agreement_payment_milestones`
- `agreement_id` (FK), `sequence_order` (INT), `name` (VARCHAR)
- `percentage` (NUMERIC 5,2), `amount` (NUMERIC 15,2), `due_date` (DATE)

### 4. `agreement_documents`
Stores metadata and physical file paths for:
- `generated_unsigned_pdf`
- `signed_agreement_pdf`
- `signature_audit_trail` (Zoho completion certificate)

### 5. `agreement_signature_requests`
Tracks transactions dispatched to the signing provider:
- `provider`: `"Zoho Sign"`
- `environment`: `"sandbox"` / `"production"` / `"mock"`
- `provider_request_id`: Zoho Sign `request_id`
- `provider_document_id`: Zoho Sign `document_id`
- `signing_url`: Client signing link
- `status`: Provider state
- `polling_attempt_count`, `last_status_checked_at`, `next_status_check_at`

### 6. `agreement_webhook_events`
Incoming webhook audit records with SHA-256 idempotency fingerprint (`event_fingerprint`).

### 7. `wedding_bookings`
Confirmed booking record created upon successful verification:
- `booking_reference`: e.g. `BK-2026-0001`
- `client_id` (FK), `agreement_id` (FK, UNIQUE)
- `couple_title`, `wedding_date`, `wedding_location`, `venue`
- `confirmed_total_amount`, `advance_amount_agreed`
- `confirmed_by`, `confirmed_at`, `phase3_handoff_ready` (TRUE)

---

## 4. Complete Backend REST API Endpoints

Base URL: `http://localhost:8000/api/v1`

---

### 4.1. Metrics & Listing

#### `GET /api/v1/service-agreements/metrics`
Retrieves live count metrics for the management dashboard cards.

* **Response (`200 OK`):**
```json
{
  "total_agreements": 12,
  "draft_agreements": 3,
  "pending_approval": 2,
  "signing_pending": 4,
  "signed_agreements": 3,
  "awaiting_verification": 1,
  "verified_agreements": 2,
  "confirmed_bookings": 2
}
```

#### `GET /api/v1/service-agreements`
Lists service agreements with pagination, search, and status filtering.

* **Query Parameters:**
  - `page` (int, default: 1)
  - `page_size` (int, default: 20, max: 100)
  - `search` (string, optional): Searches agreement number, client names, email
  - `status` (string, optional): Filter by `DRAFT`, `SIGNING_PENDING`, `SIGNED`, etc.
  - `client_id` (string, optional): Filter by specific client ID
* **Response (`200 OK`):**
```json
{
  "items": [
    {
      "id": "AGR-2026-0001",
      "agreement_number": "TRK-SA-2026-0001",
      "client_id": "CLT-2026-001",
      "status": "APPROVED_TO_SEND",
      "signing_status": "NOT_CREATED",
      "wedding_date": "2026-12-15",
      "wedding_location": "Udaipur, Rajasthan",
      "venue": "The Oberoi Udaivilas",
      "guest_count": 350,
      "service_package": "Royal Palace Grandeur",
      "package_price": "2500000.00",
      "tax_percentage": "18.00",
      "tax_amount": "450000.00",
      "discount_amount": "0.00",
      "total_amount": "2950000.00",
      "currency": "INR",
      "current_version_number": 1,
      "is_internally_approved": true,
      "is_verified": false,
      "client_partner1_name": "Aarav Sharma",
      "client_partner2_name": "Ananya Patel",
      "client_email": "client@example.com",
      "client_phone": "+91 98765 43210"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 4.2. Agreement Creation & Dossier

#### `POST /api/v1/service-agreements`
Creates a new Service Agreement for an existing registered client.

* **Request Body (`application/json`):**
```json
{
  "client_id": "CLT-2026-001",
  "wedding_date": "2026-12-15",
  "wedding_location": "Udaipur, Rajasthan",
  "venue": "The Oberoi Udaivilas",
  "guest_count": 350,
  "wedding_functions": [
    {
      "name": "Mehendi & Sangeet",
      "date": "2026-12-14",
      "venue": "Chandni Chowk Courtyard",
      "guest_count": 250,
      "notes": "Traditional Rajasthani theme"
    },
    {
      "name": "Royal Phera & Reception",
      "date": "2026-12-15",
      "venue": "Grand Ballroom",
      "guest_count": 350,
      "notes": "Royal floral mandap"
    }
  ],
  "service_package": "Royal Palace Grandeur",
  "included_services": [
    "Full Wedding Design & Thematic Decor",
    "Vendor Sourcing, Negotiation & Contract Management",
    "Guest Concierge, Hospitality & RSVP Services",
    "On-Day Event Flow & Coordination"
  ],
  "excluded_services": [
    "International flight tickets for guests",
    "Personal jewelry purchases"
  ],
  "deliverables": [
    "Comprehensive Wedding Itinerary",
    "Production Timeline & Vendor Grid",
    "Dedicated Wedding Director on Site"
  ],
  "additional_terms": "Standard cancellation policy applies as per clause 12.",
  "package_price": 2500000.00,
  "tax_percentage": 18.00,
  "discount_amount": 0.00,
  "milestones": [
    {
      "name": "Booking Advance (25%)",
      "percentage": 25.00,
      "amount": 737500.00,
      "due_date": "2026-11-15",
      "description": "Due on signing"
    },
    {
      "name": "Midway Planning Milestone (50%)",
      "percentage": 50.00,
      "amount": 1475000.00,
      "due_date": "2026-11-30",
      "description": "Due after vendor locks"
    },
    {
      "name": "Final Settlement (25%)",
      "percentage": 25.00,
      "amount": 737500.00,
      "due_date": "2026-12-10",
      "description": "Due 5 days prior to wedding"
    }
  ],
  "created_by": "Maharani Gayatri Singh"
}
```
* **Response (`201 Created`):** Returns full `ServiceAgreementResponse` object.

#### `GET /api/v1/service-agreements/{id}`
Retrieves complete agreement details, client contacts, version history, and milestones.

* **Path Parameter:** `id` (e.g. `AGR-2026-0001`)
* **Response (`200 OK`):** `ServiceAgreementResponse`

---

### 4.3. PDF Generation & Download

#### `POST /api/v1/service-agreements/{id}/generate-pdf`
Builds a high-fidelity ReportLab PDF with Royal Knot branding, terms, financials, milestones, and signature boxes.

* **Response (`200 OK`):**
```json
{
  "success": true,
  "message": "Service agreement PDF generated successfully.",
  "document_id": "DOC-2026-0001",
  "filename": "Service_Agreement_TRK-SA-2026-0001_v1.pdf",
  "file_size": 245820,
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

#### `GET /api/v1/service-agreements/{id}/download-pdf`
Streams the generated PDF file directly.

* **Query Parameters:**
  - `inline` (bool, default: `true`): If `true`, returns `Content-Disposition: inline` for browser viewing. If `false`, triggers file download.
* **Response (`200 OK`):** Binary stream (`application/pdf`).

---

### 4.4. Internal Approval

#### `POST /api/v1/service-agreements/{id}/approve`
Records internal management sign-off before the document can be sent to the client.

* **Request Body:**
```json
{
  "approved_by": "Maharani Gayatri Singh",
  "notes": "All service inclusions and budget reviewed and approved."
}
```
* **Response (`200 OK`):** Updated `ServiceAgreementResponse` with `status: "APPROVED_TO_SEND"` and `is_internally_approved: true`.

---

### 4.5. Electronic Signature (Zoho Sign)

#### `POST /api/v1/service-agreements/{id}/send-for-signature`
Submits the approved agreement and PDF to Zoho Sign (or Mock provider in local/test mode).

* **Request Body (optional overrides):**
```json
{
  "provider": "zoho_sign",
  "signer_name": "Aarav Sharma & Ananya Patel",
  "signer_email": "client@example.com",
  "signing_reason": "Execution of Royal Palace Grandeur Service Agreement"
}
```
* **Response (`200 OK`):**
```json
{
  "success": true,
  "message": "Service agreement successfully dispatched to Zoho Sign for electronic signature.",
  "agreement_id": "AGR-2026-0001",
  "agreement_number": "TRK-SA-2026-0001",
  "version_number": 1,
  "provider": "Zoho Sign",
  "environment": "sandbox",
  "provider_request_id": "zoho_req_98234123",
  "provider_document_id": "zoho_doc_10293847",
  "signing_url": "http://localhost:5173/sign-agreement/AGR-2026-0001",
  "status": "SENT",
  "sent_at": "2026-11-01T02:00:00Z"
}
```

---

### 4.6. Signature Status & Polling Synchronization

#### `GET /api/v1/service-agreements/{id}/signature-status`
Returns live e-signature status, signing URL, and completion flags.

* **Response (`200 OK`):**
```json
{
  "agreement_id": "AGR-2026-0001",
  "agreement_number": "TRK-SA-2026-0001",
  "version_number": 1,
  "signing_status": "SENT",
  "agreement_status": "SIGNING_PENDING",
  "provider": "Zoho Sign",
  "environment": "sandbox",
  "provider_request_id": "zoho_req_98234123",
  "provider_document_id": "zoho_doc_10293847",
  "signing_url": "http://localhost:5173/sign-agreement/AGR-2026-0001",
  "signer_name": "Aarav Sharma & Ananya Patel",
  "signer_email": "client@example.com",
  "completed_at": null,
  "last_status_checked_at": "2026-11-01T02:05:00Z",
  "next_status_check_at": "2026-11-01T02:05:30Z",
  "polling_attempt_count": 2,
  "last_polling_error": null,
  "has_signed_pdf": false,
  "has_audit_certificate": false
}
```

#### `POST /api/v1/service-agreements/{id}/refresh-status`
Explicitly invokes the Zoho Sign Polling Service to query the provider API right away. If the document is signed, it downloads the signed PDF and completion certificate.

* **Response (`200 OK`):** Updated `SigningStatusResponse`.

---

### 4.7. Employee Verification

#### `POST /api/v1/service-agreements/{id}/verify`
Employee verification of the executed agreement, signatures, and payment schedule.

* **Request Body:**
```json
{
  "reviewer_name": "Vikramaditya Rathore",
  "decision": "VERIFIED",
  "remarks": "Signatures verified against client credentials. Milestones confirmed."
}
```
* **Decisions:** `"VERIFIED"`, `"REJECTED"`, `"NEEDS_CORRECTION"`
* **Response (`200 OK`):** Updated `ServiceAgreementResponse` with `status: "VERIFIED"` and `is_verified: true`.

---

### 4.8. Wedding Booking Confirmation & Phase 3 Handoff

#### `POST /api/v1/service-agreements/{id}/confirm-booking`
Finalizes the contract and creates a formal `WeddingBooking` record, initiating the Phase 3 handoff dossier.

* **Request Body:**
```json
{
  "confirmed_by": "Maharani Gayatri Singh",
  "confirmation_notes": "All advance terms agreed. Ready for Phase 3 vendor allocation."
}
```
* **Response (`200 OK`):**
```json
{
  "success": true,
  "message": "Wedding booking 'TRK-WB-2026-0001' confirmed successfully! Dossier ready for Phase 3 Project Handoff.",
  "booking_id": "BK-2026-0001",
  "booking_reference": "TRK-WB-2026-0001",
  "client_id": "CLT-2026-001",
  "agreement_id": "AGR-2026-0001",
  "confirmed_version_number": 1,
  "couple_title": "Aarav Sharma & Ananya Patel",
  "wedding_date": "2026-12-15",
  "wedding_location": "Udaipur, Rajasthan",
  "venue": "The Oberoi Udaivilas",
  "confirmed_total_amount": "2950000.00",
  "advance_amount_agreed": "737500.00",
  "confirmed_by": "Maharani Gayatri Singh",
  "confirmed_at": "2026-11-01T02:10:00Z",
  "phase3_handoff_ready": true
}
```

---

### 4.9. Webhooks

#### `POST /api/v1/webhooks/zoho/callback` (Alias: `/zoho/success`)
Receives real-time asynchronous notifications from Zoho Sign.
- Automatically handles JSON payloads or form-encoded `notifications` JSON strings.
- Verifies idempotency through SHA-256 payload hashing.
- Downloads signed PDF & audit certificate upon `RequestCompleted` event.

---

## 5. Zoho Sign Integration & Polling Engine

To guarantee 100% operational reliability in both local development (where no public IP or ngrok tunnel exists) and production environments, the system implements a **Dual Sync Architecture**:

1. **Active Background Polling Engine ([`zoho_polling_service.py`](file:///c:/Users/sidar/OneDrive/Desktop/Odoo/odoo-Weddingplan/backend/app/services/zoho_polling_service.py))**:
   - Runs continuously in the FastAPI application lifespan.
   - Automatically polls agreements in `SIGNING_PENDING` status.
   - Built-in exponential backoff (starting at 30 seconds, backing off on errors).
   - Graceful recovery: On application restart, any in-flight agreements are picked up automatically.
2. **On-Demand Manual Refresh**:
   - Frontends or staff can trigger `POST /api/v1/service-agreements/{id}/refresh-status` at any time.
3. **Webhook Fallback**:
   - Webhook callback endpoints remain active and ready for production webhooks.

---

## 6. Frontend Routes & Components

All frontend routes are integrated in [`frontend/src/App.tsx`](file:///c:/Users/sidar/OneDrive/Desktop/Odoo/odoo-Weddingplan/frontend/src/App.tsx):

| Route Path | Component | Target Role | Description |
|---|---|---|---|
| `/agreements` | `AgreementsPage.tsx` | Staff / Admin | Dashboard with metrics cards, status tabs, search & agreements list |
| `/agreements/new` | `AddAgreementPage.tsx` | Staff / Admin | Multi-step form to create new agreement with milestone calculation |
| `/agreements/:id` | `AgreementDetailsPage.tsx` | Staff / Admin | Complete dossier: PDF viewer, approval button, Zoho send, status badge, verify & booking confirmation |
| `/sign-agreement/:id` | `ClientSigningPage.tsx` | Public / Client | Client-facing portal to review the contract, preview the PDF, and execute signature |

### API Client Service:
All backend calls are pre-wired in `frontend/src/services/api.ts` under `export const agreementApi`:
- `agreementApi.getMetrics()`
- `agreementApi.list(params)`
- `agreementApi.get(id)`
- `agreementApi.create(data)`
- `agreementApi.generatePdf(id)`
- `agreementApi.getPdfUrl(id, inline)`
- `agreementApi.approve(id, approvedBy, notes)`
- `agreementApi.sendForSignature(id)`
- `agreementApi.getSignatureStatus(id)`
- `agreementApi.refreshSignatureStatus(id)`
- `agreementApi.verify(id, reviewerName, decision, remarks)`
- `agreementApi.confirmBooking(id, confirmedBy, confirmationNotes)`

---

## 7. Environment Configuration

In `backend/.env`:
```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/royal_knot_db

# Electronic Signature Provider
ESIGN_PROVIDER=zoho_sign
ESIGN_ENVIRONMENT=sandbox

# Zoho Sign Credentials (If empty, automatically runs in high-fidelity mock mode)
ZOHO_SIGN_CLIENT_ID=
ZOHO_SIGN_CLIENT_SECRET=
ZOHO_SIGN_REFRESH_TOKEN=
ZOHO_SIGN_ACCOUNTS_URL=https://accounts.zoho.in
ZOHO_SIGN_BASE_URL=https://sign.zoho.in

# Zoho Sign Polling Service
ZOHO_POLLING_ENABLED=True
ZOHO_POLLING_INTERVAL_SECONDS=30
ZOHO_POLLING_MAX_ATTEMPTS=50
```

---

## 8. Running & Testing the Project

### Start All Services (Recommended)
You can start both backend and frontend servers together using the project root startup script:
```powershell
.\start-servers.ps1
```

### Or Start Individually:
1. **Backend Server:**
   ```powershell
   cd backend
   & "C:\RoyalKnot\venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
   - OpenAPI Specification: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

2. **Frontend Server:**
   ```powershell
   cd frontend
   npm run dev
   ```
   - Web Application URL: [http://localhost:5173](http://localhost:5173)

### Running Automated Verification Suite:
```powershell
# Run backend test suite (60 tests)
cd backend
& "C:\RoyalKnot\venv\Scripts\python.exe" -m pytest tests/ -v

# Run frontend production build
cd frontend
npm run build
```

