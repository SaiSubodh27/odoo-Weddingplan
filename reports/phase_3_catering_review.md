# Phase 3 Catering Management — Architecture & Implementation Review

**Executive Summary & Review Report**  
*The Royal Knot — Wedding Planning Management System*  
**Date:** 2026-10-31  
**Target Branch:** `feature/phase-3-wedding-project-management`  
**Reviewer:** Lead Full-Stack Engineer, Product Analyst & QA  

---

## 1. What Has Already Been Implemented

Your colleague has completed foundational work for **Wedding Project Setup & Milestones Management**:

1. **Database Models (`backend/app/models/project.py`):**
   - `WeddingProject`: Maps 1:1 with confirmed client bookings (`client_id`). Generates sequential project codes (`PRJ-YYYY-XXX`), stores palace locations, overall guest counts, budgets, and project managers.
   - `WeddingFunction`: Models multi-day wedding events (Mehendi, Haldi, Sangeet, Wedding Ceremony, Reception) with date, timing, venue, and status.
   - `ProjectMilestone`: Checkpoints with due dates and completion timestamps. Auto-seeds 5 luxury palace planning milestones.
   - `ProjectStatusHistory`: Complete audit trail logging every status change (`Planning` -> `In Progress` -> `Completed`), author, timestamp, and notes.

2. **Backend API Routes & Services (`backend/app/routes/projects.py`, `project_service.py`):**
   - `GET /api/v1/projects/eligible-bookings`: Discovers confirmed client dossiers awaiting project creation.
   - `POST /api/v1/projects`: Creates wedding projects, verifies confirmed client status, prevents duplicate projects, and seeds initial milestones.
   - `GET /api/v1/projects`: Paginated project list with search and status filtering.
   - `GET/PUT /api/v1/projects/{project_id}`: Full project details and metadata updates.
   - `PATCH /api/v1/projects/{project_id}/status`: Status progression with history logging.
   - `GET/POST/PUT/DELETE /api/v1/projects/{project_id}/functions`: Event ceremony CRUD with automated tier-based cost estimation.
   - `POST/PUT/DELETE /api/v1/projects/{project_id}/milestones`: Milestone lifecycle management.

3. **Frontend Staff UI:**
   - `ProjectsPage.tsx`: Elegant registry view with progress bars, search, and status filters.
   - `CreateProjectModal.tsx`: Project initialization modal reading eligible confirmed bookings.
   - `ProjectDetailsPage.tsx`: Tabs for *Overview*, *Wedding Functions*, *Milestones*, and *Status History*.

---

## 2. What Works and Has Been Verified

| Component / Flow | Verification Method | Status |
|---|---|---|
| Project Creation from Confirmed Booking | Pytest automated test & manual API execution | **VERIFIED (PASS)** |
| Prevention of Duplicate Projects | Pytest test case | **VERIFIED (PASS)** |
| Automatic Milestone Seeding | Inspected database output and API response | **VERIFIED (PASS)** |
| Wedding Functions CRUD & Auto-Costing | Pytest test case | **VERIFIED (PASS)** |
| Milestone Toggle & Completed_at Stamping | Pytest test case | **VERIFIED (PASS)** |
| Status Transition Audit Trail | Pytest test case | **VERIFIED (PASS)** |
| Frontend TypeScript Compilation | `tsc -b && vite build` | **VERIFIED (0 errors)** |
| Complete Test Suite (17 tests) | `pytest backend/tests/` | **VERIFIED (100% pass)** |

---

## 3. What is Incomplete or Broken

1. **Branch Divergence from Main:**
   - The `feature/phase-3-wedding-project-management` branch was branched from `3c896de` before recent Phase 1 commits (`ecb9ab1`, `fe2ccf6`, `8a75249` for Google Forms CSV sync and public website registration) were merged to `main`.
   - As a result, files like `backend/app/services/google_sheets_service.py` and `frontend/src/pages/WebsiteRegistrationPage.tsx` are missing on this branch.
   - *Recommendation:* Keep the Phase 3 branch focused on Phase 3 Catering completion. Once Phase 3 is completed and reviewed, cleanly rebase/merge with `main` to preserve both Phase 1 and Phase 3 capabilities.

2. **Placeholder in `ClientDetailsPage.tsx`:**
   - In `ClientDetailsPage.tsx` (lines 354–369), the "Catering Requirements" block is currently an inert card with a `[Coming Soon]` badge and zero interactive functionality.

3. **Missing Catering Tab in `ProjectDetailsPage.tsx`:**
   - In `ProjectDetailsPage.tsx`, staff can view functions and milestones, but there is no tab to view or manage catering, menus, or food service vendors.

---

## 4. What is Missing from the Catering Workflow

The entire **Catering Management Subsystem** has not yet been implemented on this branch:

1. **No Catering Plans:** No table or API associating an event (`WeddingFunction`) with a catering specification.
2. **No Menu Management:** No ability to record dishes, courses (Welcome Drinks, Starters, Mains, Live Counters, Desserts), quantities, or dietary tags (Veg, Non-Veg, Jain, Gluten-Free).
3. **No Vendor Integration:** No shared vendor directory or quotation comparison for competing palace caterers.
4. **No Quotation & Cost Breakdown:** No per-person rate tracking, GST calculations, or agreed pricing locks.
5. **No Vendor PDF Generator:** No ReportLab service to compile and download an official catering specification PDF.
6. **No WhatsApp Communication:** No WhatsApp dispatch, deep-link generation, or communication audit log.
7. **No Catering Status Stepper:** No workflow states (`Draft` -> `Requirements Confirmed` -> `Quotation Requested` -> `Vendor Selected` -> `Menu Finalized` -> `PDF Generated` -> `Sent to Vendor` -> `Vendor Confirmed`).

---

## 5. API Endpoints Analysis

### Existing Endpoints (14 Phase 3 Project endpoints verified)
* `GET /api/v1/projects/eligible-bookings`
* `POST /api/v1/projects`
* `GET /api/v1/projects`
* `GET /api/v1/projects/{project_id}`
* `PUT /api/v1/projects/{project_id}`
* `PATCH /api/v1/projects/{project_id}/status` (& `POST` alias)
* `GET /api/v1/projects/{project_id}/functions`
* `POST /api/v1/projects/{project_id}/functions`
* `PUT /api/v1/projects/{project_id}/functions/{func_id}` (& `PATCH` alias)
* `PUT /api/v1/projects/functions/{func_id}` (& `PATCH` alias)
* `DELETE /api/v1/projects/{project_id}/functions/{func_id}`
* `POST /api/v1/projects/{project_id}/milestones`
* `PUT /api/v1/projects/{project_id}/milestones/{ms_id}` (& `PATCH` alias)
* `DELETE /api/v1/projects/{project_id}/milestones/{ms_id}`

### Missing Endpoints Required for Catering (12 new endpoints to implement)
1. `GET /api/v1/projects/{project_id}/catering` — List project catering plans across events.
2. `GET /api/v1/projects/{project_id}/functions/{func_id}/catering` — Get event catering details.
3. `POST /api/v1/projects/{project_id}/functions/{func_id}/catering` — Create event catering requirements.
4. `PUT /api/v1/projects/{project_id}/functions/{func_id}/catering` — Update catering requirements.
5. `GET /api/v1/catering/{catering_id}/menu-items` — Get organized menu courses and dishes.
6. `POST /api/v1/catering/{catering_id}/menu-items` — Add food items to event menu.
7. `PUT /api/v1/catering/{catering_id}/menu-items/{item_id}` — Update menu item / dietary flags.
8. `DELETE /api/v1/catering/{catering_id}/menu-items/{item_id}` — Remove item from menu.
9. `GET /api/v1/vendors?category=Catering` — Shared vendor directory filtered by caterers.
10. `POST /api/v1/vendors` — Register a luxury vendor / master khansama.
11. `GET /api/v1/catering/{catering_id}/quotations` — List vendor bids for comparison.
12. `POST /api/v1/catering/{catering_id}/quotations` — Record vendor quotation (per-person rate, taxes, total).
13. `POST /api/v1/catering/{catering_id}/quotations/{quotation_id}/select` — Select winning caterer & lock agreed pricing.
14. `GET /api/v1/catering/{catering_id}/pdf` — Generate & stream dynamic vendor specification PDF.
15. `POST /api/v1/catering/{catering_id}/share-whatsapp` — Generate WhatsApp deep-link & log communication.
16. `PATCH /api/v1/catering/{catering_id}/status` — Transition catering lifecycle status.

---

## 6. Database and Model Gaps

The following relational models must be created in PostgreSQL:

```
┌─────────────────────────────────┐
│         wedding_projects        │
└────────────────┬────────────────┘
                 │ 1:N
┌────────────────▼────────────────┐
│        wedding_functions        │
└────────────────┬────────────────┘
                 │ 1:1
┌────────────────▼────────────────┐         ┌────────────────────────┐
│         catering_plans          ├────────►│        vendors         │
└───────┬─────────────────┬───────┘ (1:N)   └───────────▲────────────┘
        │ 1:N             │ 1:N                         │
┌───────▼───────────┐ ┌───▼────────────────┐            │
│catering_menu_items│ │catering_quotations ├────────────┘
└───────────────────┘ └────────────────────┘
```

1. **`vendors` (Shared Vendor Entity):**
   `id`, `name`, `category` (Catering, Decor, Photography, etc.), `contact_person`, `email`, `phone` (WhatsApp), `city`, `rating`, `notes`, `is_active`, `created_at`.
2. **`catering_plans`:**
   `id`, `project_id`, `function_id`, `service_type`, `cuisine_preferences`, `guest_count`, `veg_count`, `non_veg_count`, `dietary_notes`, `service_timings`, `budget`, `selected_vendor_id`, `agreed_cost`, `status`, `notes`, `created_at`, `updated_at`.
3. **`catering_menu_items`:**
   `id`, `catering_plan_id`, `course_category` (`Welcome Drinks`, `Appetizers & Starters`, `Main Courses`, `Live Counters`, `Breads & Dal`, `Dessert Atelier`, `Late Night Bites`), `item_name`, `description`, `dietary_tag` (`Veg`, `Non-Veg`, `Jain`, `Gluten-Free`), `quantity_note`, `created_at`.
4. **`catering_quotations`:**
   `id`, `catering_plan_id`, `vendor_id`, `per_person_rate`, `total_guest_count`, `additional_charges`, `tax_gst`, `total_quoted_cost`, `validity_date`, `status` (`Received`, `Under Review`, `Accepted`, `Rejected`), `notes`, `created_at`.
5. **`catering_communications`:**
   `id`, `catering_plan_id`, `vendor_id`, `recipient_phone`, `message_text`, `pdf_url`, `delivery_method` (`WhatsApp Deep-Link`, `Direct API`), `status`, `created_at`.

---

## 7. PDF Generation Status

- **Current Status:** Not implemented.
- **Engine Choice:** `ReportLab` (industry standard, natively available in Python, zero external binary daemon dependencies).
- **Format Requirements:**
  - Standard `%PDF-1.4` output.
  - Agency header with "The Royal Knot — Luxury Wedding Planners (Jaipur & Udaipur)".
  - Project code, couple name, and event details (e.g. "Royal Sangeet at Zenana Mahal Courtyard").
  - Exact guest pax breakdown (Veg, Non-Veg, Jain).
  - Categorized, beautiful tables of approved food items with course headers.
  - Selected vendor and head khansama instructions.
  - Timestamp, version number, and contact info.
- **Verification Plan:** Unit test asserting non-empty binary stream, valid PDF signature header, and inclusion of actual event parameters (no hardcoded text).

---

## 8. WhatsApp Integration Status

- **Direct WhatsApp Business API:**
  - Requires Meta Business verification, approved message templates, phone number registration, and permanent bearer access tokens. These credentials are not configured in the repository.
  - Per instructions, **we will not fabricate or mock fake successful delivery**.
- **Actionable Production Fallback:**
  - We will implement an automated **WhatsApp Share Flow**:
    1. Endpoint `/api/v1/catering/{catering_id}/share-whatsapp` compiles the catering summary, creates the PDF download route, and formats a pre-filled, professional invitation message.
    2. Returns a verified `https://wa.me/{vendor_phone}?text={encoded_message}` deep-link.
    3. Frontend displays a modal with the vendor's WhatsApp phone number, full message preview, copyable PDF link, and a 1-click **"Open in WhatsApp"** button.
    4. Automatically records a timestamped communication log in `catering_communications`.
  - This provides genuine staff utility today without external blockers.

---

## 9. Product Owner Decisions (Approved & Confirmed)

The Product Owner has reviewed the audit and formally approved the following 4 architectural decisions:

1. **Dietary Pax Validation:**
   - **Approved:** Dietary counts are flexible estimates. Validates non-negative integers; does **not** reject submissions if `veg_count + non_veg_count != total_guest_count`.

2. **Catering Guest Count vs Event Guest Count:**
   - **Approved:** Event catering guest count defaults to `wedding_projects.guest_count`, but allows custom event-specific overrides per ceremony function without overwriting the master project guest count.

3. **Curated Luxury Menu Preset Library:**
   - **Approved:** Provide 3 pre-engineered palace banquet templates (*Royal Rajputana Mewari Feast*, *Mughal Sheesh Mahal Degustation*, *Contemporary Pan-Asian Luxury*) that staff can auto-populate with 1 click, edit, customize, or start completely from scratch.

4. **Quotation GST Calculation:**
   - **Approved:** GST rate is **configurable per quotation** (e.g., 0%, 5%, 12%, 18%). Universal GST rates are not hardcoded.

---

## 10. Staged Implementation Roadmap (Stages 1 through 8)

Implementation will proceed strictly through the following 8 controlled stages upon Product Owner approval:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: CATERING DATA FOUNDATION & SHARED VENDORS                                                     │
│ - Shared Vendor model (`backend/app/models/vendor.py`)                                                 │
│ - Catering models (`catering_plans`, `catering_menu_items`, `catering_quotations`, `communications`)   │
│ - 3 Luxury Menu preset templates (`backend/app/services/catering_presets.py`)                           │
│ - Database migration (`backend/alembic/versions/`)                                                     │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
┌───────────────────────────────────────────────────▼────────────────────────────────────────────────────┐
│ STAGE 2: CATERING & VENDOR API ENDPOINTS                                                               │
│ - Shared Vendor CRUD (`/api/v1/vendors`)                                                               │
│ - Event Catering CRUD (`/api/v1/projects/{project_id}/functions/{func_id}/catering`)                  │
│ - Menu Management & Preset Applicator (`/api/v1/catering/{catering_id}/menu-items`)                    │
│ - Update `docs/API_ENDPOINT_REGISTRY.md`                                                               │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
┌───────────────────────────────────────────────────▼────────────────────────────────────────────────────┐
│ STAGE 3: QUOTATIONS & COSTING ENGINE                                                                   │
│ - Quotation recording with configurable GST rate, equipment charges & itemized math                    │
│ - Quotation comparison & winning caterer selection (`select-quotation`)                                │
│ - Agreed pricing sync with function financials                                                         │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
┌───────────────────────────────────────────────────▼────────────────────────────────────────────────────┐
│ STAGE 4: CATERING STATUS LIFECYCLE WORKFLOW                                                            │
│ - Status progression: `Draft` -> `Requirements Confirmed` -> `Vendor Selected` ->                      │
│   `Menu Finalized` -> `Sent to Vendor` -> `Vendor Confirmed`                                           │
│ - Status transition validation endpoint (`PATCH /api/v1/catering/{catering_id}/status`)               │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
┌───────────────────────────────────────────────────▼────────────────────────────────────────────────────┐
│ STAGE 5: DYNAMIC VENDOR PDF GENERATION                                                                 │
│ - Branded ReportLab PDF engine pulling live catering, menu, and pax data                               │
│ - Stream endpoint: `GET /api/v1/catering/{catering_id}/pdf` (returns `%PDF-1.4`)                       │
│ - Secure binary streaming with zero hardcoded/mock text                                                │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
┌───────────────────────────────────────────────────▼────────────────────────────────────────────────────┐
│ STAGE 6: ACTIONABLE WHATSAPP SHARE FLOW                                                                │
│ - Endpoint: `POST /api/v1/catering/{catering_id}/share-whatsapp`                                      │
│ - Pre-fills vendor WhatsApp number, formats royal invitation message, generates deep-link              │
│ - Records action in `catering_communications` audit trail                                              │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
┌───────────────────────────────────────────────────▼────────────────────────────────────────────────────┐
│ STAGE 7: CATERING FRONTEND STAFF UI INTEGRATION                                                        │
│ - 5th tab `Catering & Menus` in `ProjectDetailsPage.tsx`                                               │
│ - Event Catering Cards, Requirements Modal, Menu Builder with Presets Accordion                        │
│ - Quotation Comparison Modal with live GST math & Selection                                            │
│ - PDF Download button & WhatsApp Share Modal with 1-click deep-link                                    │
│ - Dedicated `VendorsPage.tsx` in sidebar registry                                                      │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
┌───────────────────────────────────────────────────▼────────────────────────────────────────────────────┐
│ STAGE 8: COMPREHENSIVE AUTOMATED TESTING & REGRESSION VERIFICATION                                     │
│ - Automated pytest suite `backend/tests/test_phase3_catering_workflow.py` (8 new test flows)           │
│ - Verification of existing 17 project/Phase 1 tests (zero regression)                                  │
│ - TypeScript compilation (`tsc -b`) and Vite production build (`npm run build`)                        │
│ - Final API Endpoint Registry & Checklist updates                                                      │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Current Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\saisu\OneDrive\Desktop\odoo-Weddingplan\backend
configfile: pytest.ini
plugins: anyio-4.15.1
collected 40 items

backend\tests\test_automated_registration_workflow.py .                  [  2%]
backend\tests\test_email_integration_workflow.py ..........              [ 27%]
backend\tests\test_enquiry_activation_workflow.py .....                  [ 40%]
backend\tests\test_phase3_catering_api.py ...............                [ 77%]
backend\tests\test_phase3_catering_models.py ........                    [ 97%]
backend\tests\test_phase3_projects_workflow.py .                         [100%]

======================== 40 passed, 1 warning in 7.46s ========================
```

- **Stage 1 Specific Suite:** `pytest backend/tests/test_phase3_catering_models.py` — **8 passed in 1.54s**.
- **Stage 2 & 3 API Suite:** `pytest backend/tests/test_phase3_catering_api.py` — **15 passed in 3.46s**.
- **Frontend Build Check:** `npm --prefix frontend run build` completed in **836ms** with **0 TypeScript errors**.

---

## 12. Known Issues & Deferred Verifications

- **Issue REG-01: Client Registration Form Validation Error**
  - *Symptom:* During earlier Phase 1 testing, the client website registration form returned: `"Data validation failed. Please check the submitted fields."`
  - *Context:* The form was submitted with minimal/test inputs (`YOUR FULL NAME *` set to `"s"`, `PARTNER'S FULL NAME` set to `"s"`).
  - *Status:* **Recorded as a known issue for post-Phase 3 regression testing.**
  - *Action Plan (Deferred to after Phase 3 & branch integration):*
    - Verify actual backend HTTP 422 error payload against `WebsiteClientRegisterRequest` in `user.py`.
    - Improve frontend field-level error handling in `WebsiteRegistrationPage.tsx` so users see exact field errors rather than only a generic header alert.
    - Validate field rules: full name min length, partner name optionality, password min length (8 chars) & match, wedding date format (`YYYY-MM-DD`), guest count ($\ge 1$), and budget ($\ge 0$).
    - Full end-to-end activation link and client login verification.
  - *Note:* Do not interrupt Phase 3 Catering implementation to patch this; address after Phase 3 completion and branch integration approval.

---

**Status:** Stage 3 (Vendor Quotations & Costing Engine) VERIFIED COMPLETE.  
**Gate Status:** STOPPED at Stage 3. Awaiting Product Owner approval before beginning Stage 4 (Catering Status Lifecycle Workflow).

