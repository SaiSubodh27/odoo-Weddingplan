# The Royal Knot — Phase 3 Catering Management Implementation Checklist

> **Module:** Wedding Project Management — Catering & Food Service Subsystem  
> **Target Branch:** `feature/phase-3-wedding-project-management`  
> **Last Updated:** 2026-10-31  
> **Approval Gate Status:** **ALL STAGES 1 THROUGH 7 COMPLETE & FULLY VERIFIED — ZERO REGRESSIONS**  
> **Status Legend:**  
> - `[x]` Verified complete  
> - `[ ]` Approved & implementation-ready (pending gate approval)  
> - `[!]` Implemented but broken/incomplete  
> - `[B]` Blocked by external third-party prerequisite  

---

## 0. Product Owner Decisions (Approved & Integrated)

- [x] **Decision 1 (Dietary Pax Counts):** Dietary counts are flexible estimates. Validates non-negative integers; will not reject submissions if `veg_count + non_veg_count != total_guest_count`.
- [x] **Decision 2 (Guest Count Override):** Catering guest count defaults to `wedding_projects.guest_count`, but allows event-specific overrides per ceremony function.
- [x] **Decision 3 (Luxury Menu Presets):** Pre-engineered luxury menu starting templates provided (*Royal Rajputana Mewari Feast*, *Mughal Sheesh Mahal Degustation*, *Contemporary Pan-Asian Luxury*), fully editable before saving. Custom menus also fully supported.
- [x] **Decision 4 (Configurable GST):** GST rate is configurable per vendor quotation (e.g., 0%, 5%, 12%, 18%). No hardcoded universal GST rate.

---

## 1. Existing Implementation Baseline

- [x] **Project Setup from Confirmed Bookings:** `GET /api/v1/projects/eligible-bookings` and `POST /api/v1/projects` verified and tested.
- [x] **Project Code Auto-Generation:** Formats `PRJ-YYYY-XXX` sequentially, validated against duplicates.
- [x] **Wedding Functions (Events) Subsystem:** `WeddingFunction` model, CRUD API endpoints (`GET`, `POST`, `PUT`, `DELETE`), and modal management in UI.
- [x] **Project Milestones Subsystem:** `ProjectMilestone` model, seeding 5 default milestones, toggle completion in UI.
- [x] **Project Status & Audit Trail:** `ProjectStatusHistory` model, status transitions recorded with timestamp, author, and notes.
- [x] **Project Dashboard & List View:** `ProjectsPage.tsx` with search, status filters, and milestone progress bars.
- [!] **Catering Entry Point:** `ClientDetailsPage.tsx` has a locked card labeled "Catering Requirements - Coming Soon". `ProjectDetailsPage.tsx` has no Catering tab.
- [ ] **Catering Subsystem:** No catering database models, API routes, menus, or vendor integrations exist yet.

---

## 2. Stage 1 — Catering Data Foundation & Shared Vendors (VERIFIED COMPLETE)

- [x] **Item 1.1: Shared Vendor Entity (`backend/app/models/vendor.py`)**
  - *Status:* Verified complete and tested in `test_phase3_catering_models.py`.
  - *Schema:* `id` (VND-XXXX), `name`, `category` (Catering, Decor, Photography, Floral, Sound), `contact_person`, `email`, `phone` (WhatsApp-enabled), `city`, `rating`, `notes`, `is_active`, `created_at`, `updated_at`.
  - *Relationships:* `catering_plans`, `quotations`, `communications`.

- [x] **Item 1.2: Event-Linked Catering Plan Entity (`backend/app/models/catering.py`)**
  - *Status:* Verified complete and tested in `test_phase3_catering_models.py`.
  - *Schema:* `id` (CAT-XXXX), `project_id` (FK `wedding_projects.id`), `function_id` (FK `wedding_functions.id`, UNIQUE), `service_style`, `cuisine_preferences`, `guest_count` (project default with event override permitted), `veg_count`, `non_veg_count`, `jain_count` (flexible estimates), `dietary_notes`, `service_timings`, `location`, `budget`, `selected_vendor_id` (FK `vendors.id`, SET NULL), `agreed_cost`, `status` (Default: `Draft`), `notes`, `created_at`, `updated_at`.
  - *Relationships:* `project`, `function`, `selected_vendor`, `menu_items`, `quotations`, `communications`.

- [x] **Item 1.3: Structured Menu Items Entity (`backend/app/models/catering.py`)**
  - *Status:* Verified complete and tested in `test_phase3_catering_models.py`.
  - *Schema:* `id` (ITM-XXXX), `catering_plan_id` (FK `catering_plans.id`, CASCADE), `course_category`, `item_name`, `description`, `dietary_tag`, `quantity_note`, `display_order`, `created_at`, `updated_at`.

- [x] **Item 1.4: Starting Luxury Menu Preset Templates (`backend/app/services/catering_presets.py`)**
  - *Status:* Verified complete and tested in `test_phase3_catering_models.py`.
  - *Templates:*
    1. **Royal Rajputana Mewari Feast:** 13 dishes across 6 courses.
    2. **Mughal Sheesh Mahal Degustation:** 14 dishes across 6 courses.
    3. **Contemporary Pan-Asian Luxury:** 13 dishes across 6 courses.
  - *Functions:* `get_available_presets()`, `get_preset_by_id()`, `get_preset_items()`. Returns deep copies to ensure template immutability.

- [x] **Item 1.5: Alembic Migration (`backend/alembic/versions/a1c8f921d7b3_add_catering_and_vendor_models.py`)**
  - *Status:* Applied successfully to PostgreSQL development database (`a1c8f921d7b3`).
  - *Tables created:* `vendors`, `catering_plans`, `catering_menu_items`, `catering_quotations`, `catering_communications`. All foreign keys, cascade deletes, and indexes verified.

---

## 3. Stage 2 — Catering & Vendor API Endpoints (VERIFIED COMPLETE)

- [x] **Item 2.1: Shared Vendor CRUD Endpoints (`backend/app/routes/vendors.py`, `vendor_service.py`)**
  - *Status:* Verified complete and tested in `test_phase3_catering_api.py`.
  - `GET /api/v1/vendors`: Query by `category`, `city`, `search`, `isActive`, pagination (`VendorListResponse`).
  - `POST /api/v1/vendors`: Create luxury vendor dossier with duplicate telephone prevention (`VendorResponse`, HTTP 201).
  - `GET /api/v1/vendors/{vendor_id}`: Retrieve vendor details with portfolio and quotation counters (`VendorDetailResponse`).
  - `PUT /api/v1/vendors/{vendor_id}`: Update vendor contact/WhatsApp details (`VendorResponse`).
  - `PATCH /api/v1/vendors/{vendor_id}/status`: Toggle vendor operational status (`VendorResponse`).
  - *Schema:* `VendorCreate`, `VendorUpdate`, `VendorStatusUpdate`, `VendorResponse`, `VendorDetailResponse`, `VendorListResponse`.

- [x] **Item 2.2: Event-Specific Catering Plan Endpoints (`backend/app/routes/catering.py`, `catering_service.py`)**
  - *Status:* Verified complete and tested in `test_phase3_catering_api.py`.
  - `GET /api/v1/projects/{project_id}/catering`: List all event catering plans for a project (`List[CateringPlanResponse]`).
  - `GET /api/v1/projects/{project_id}/functions/{func_id}/catering`: Retrieve ceremony catering requirements (`CateringPlanDetailResponse`).
  - `POST /api/v1/projects/{project_id}/functions/{func_id}/catering`: Create catering requirements (auto-populates `guest_count` from project if omitted; permits event guest override without modifying parent project count; validates flexible non-negative estimates without rigid sum constraints; enforces unique function-to-catering-plan constraint; HTTP 201).
  - `PUT /api/v1/projects/{project_id}/functions/{func_id}/catering`: Update requirements and budget (`CateringPlanDetailResponse`).
  - `GET /api/v1/catering/{catering_id}`: Direct catering plan retrieval by plan ID (`CateringPlanDetailResponse`).
  - `PUT /api/v1/catering/{catering_id}`: Direct catering plan update by plan ID (`CateringPlanDetailResponse`).
  - *Schema:* `CateringPlanCreate`, `CateringPlanUpdate`, `CateringPlanResponse`, `CateringPlanDetailResponse`.

- [x] **Item 2.3: Menu Management Endpoints (`backend/app/routes/catering.py`, `catering_service.py`)**
  - *Status:* Verified complete and tested in `test_phase3_catering_api.py`.
  - `GET /api/v1/catering/{catering_id}/menu-items`: List organized courses and dishes (`List[CateringMenuItemResponse]`).
  - `POST /api/v1/catering/{catering_id}/menu-items`: Add dish with category, dietary tags, quantity notes, display order (`CateringMenuItemResponse`, HTTP 201).
  - `PUT /api/v1/catering/{catering_id}/menu-items/{item_id}`: Update dish or dietary tag; enforces plan isolation (`CateringMenuItemResponse`).
  - `DELETE /api/v1/catering/{catering_id}/menu-items/{item_id}`: Delete dish; enforces plan isolation (`{ success: bool, message: str }`).
  - `POST /api/v1/catering/{catering_id}/menu-items/reorder`: Reorder courses and dishes (`List[CateringMenuItemResponse]`).
  - *Schema:* `CateringMenuItemCreate`, `CateringMenuItemUpdate`, `CateringMenuItemResponse`, `MenuItemReorderRequest`.

- [x] **Item 2.4: Menu Presets API Endpoints (`backend/app/routes/catering.py`, `catering_service.py`)**
  - *Status:* Verified complete and tested in `test_phase3_catering_api.py`.
  - `GET /api/v1/catering/presets`: List available starting templates (`List[PresetSummaryResponse]`).
  - `GET /api/v1/catering/presets/{preset_id}`: Retrieve preset details with courses and dishes (`PresetDetailResponse`).
  - `POST /api/v1/catering/{catering_id}/apply-preset`: Apply preset template (`mode: 'append' | 'replace'`); creates editable menu items without mutating shared preset definitions (`List[CateringMenuItemResponse]`).
  - *Schema:* `PresetSummaryResponse`, `PresetDetailResponse`, `ApplyPresetRequest`.

---

## 4. Stage 3 — Vendor Quotations & Costing Engine (VERIFIED COMPLETE)

- [x] **Item 3.1: Catering Quotations Entity & Decimal Costing Math (`backend/app/models/catering.py`, `catering_service.py`)**
  - *Status:* Verified complete and tested in `test_phase3_catering_models.py` and `test_phase3_catering_api.py`.
  - *Schema:* `id` (QUO-XXXX), `catering_plan_id` (FK `catering_plans.id`), `vendor_id` (FK `vendors.id`), `quotation_reference`, `per_person_rate` (Decimal >= 0), `total_guest_count` (Integer >= 1), `food_subtotal` (Decimal >= 0), `equipment_charges` (Decimal >= 0), `gst_rate_percent` (Decimal >= 0, **configurable per quotation: 0%, 5%, 12%, 18%, or custom**), `gst_amount` (Decimal >= 0), `total_amount` (Decimal >= 0), `status` (`Received`, `Under Review`, `Accepted`, `Rejected`), `validity_date` (Date), `notes` (Text), `created_at`, `updated_at`.
  - *Calculation Formula:*
    1. `food_subtotal = round_2_places(per_person_rate * total_guest_count)`
    2. `taxable_subtotal = food_subtotal + round_2_places(equipment_charges)`
    3. `gst_amount = round_2_places(taxable_subtotal * (gst_rate_percent / 100))`
    4. `total_amount = taxable_subtotal + gst_amount`
  - *Note:* GST is applied to the combined food subtotal and equipment charges (standard Indian event catering service tax composite). Configurable rate supports standard (0%, 5%, 12%, 18%) or custom rates with `ROUND_HALF_UP` decimal precision.

- [x] **Item 3.2: Quotation CRUD & Winning Selection Endpoints (`backend/app/routes/catering.py`, `catering_service.py`)**
  - *Status:* Verified complete and tested in `test_phase3_catering_api.py`.
  - `GET /api/v1/catering/{catering_id}/quotations`: List competing vendor bids with joined vendor details (`List[CateringQuotationResponse]`).
  - `POST /api/v1/catering/{catering_id}/quotations`: Record quotation with automatic costing calculation and configurable GST (`CateringQuotationResponse`, HTTP 201).
  - `GET /api/v1/catering/{catering_id}/quotations/{quotation_id}`: Retrieve single quotation dossier (`CateringQuotationResponse`).
  - `PUT /api/v1/catering/{catering_id}/quotations/{quotation_id}`: Update terms and automatically recalculate subtotals and totals (`CateringQuotationResponse`).
  - `POST /api/v1/catering/{catering_id}/quotations/{quotation_id}/select`: Select winning caterer. Locks `catering_plans.selected_vendor_id`, sets `catering_plans.agreed_cost`, marks quotation as `Accepted` and transitions competing active quotations to `Rejected` (`CateringQuotationSelectResponse`).
  - *Schema:* `CateringQuotationCreate`, `CateringQuotationUpdate`, `CateringQuotationResponse`, `CateringQuotationSelectResponse`.

---

## 5. Stage 4 — Catering Status Lifecycle Workflow (VERIFIED COMPLETE)

- [x] **Item 4.1: Catering Status Lifecycle Transitions (`backend/app/services/catering_service.py`)**
  - *Statuses:*
    1. `Draft` (Initial requirements being drafted)
    2. `Requirements Confirmed` (Dishes & pax approved by client)
    3. `Quotation Requested` (Bids requested from luxury caterers)
    4. `Vendor Selected` (Caterer quotation accepted)
    5. `Menu Finalized` (Degustation completed; menu locked)
    6. `Sent to Vendor` (PDF specification shared via WhatsApp)
    7. `Vendor Confirmed` (Vendor countersigned / acknowledged)
  - *Rules:* Selecting quotation transitions to `Vendor Selected`; generating/sharing PDF allows transition to `Sent to Vendor`; vendor response transitions to `Vendor Confirmed`.
  - *Endpoint:* `PATCH /api/v1/catering/{catering_id}/status`.
  - *Priority:* P1 (High)

---

## 6. Stage 5 — Dynamic Vendor PDF Generation (VERIFIED COMPLETE)

- [x] **Item 5.1: Branded Vendor Specification PDF Engine (`backend/app/services/pdf_service.py`)**
  - *Library:* `ReportLab` (`reportlab.platypus.SimpleDocTemplate`, `Paragraph`, `Table`, `Spacer`, `colors`).
  - *Contents (100% Real Database Data):*
    - The Royal Knot Agency Crest & Header ("Luxury Wedding Planners — Jaipur & Udaipur")
    - Wedding Project Code, Couple Name, Palace Venue & Target Ceremony Date
    - Service Timings & Service Style
    - Guaranteed Guest Count & Flexible Pax Breakdown (Veg, Non-Veg, Jain)
    - Itemized Menu Courses & Categorized Dishes with Dietary Tags
    - Special Khansama Instructions & Dietary Warning Notes
    - Selected Vendor Name & Khansama Contact
    - Document Revision Number & Generation Timestamp
  - *Endpoint:* `GET /api/v1/catering/{catering_id}/pdf` streaming `application/pdf`.
  - *Security:* Requires staff authentication. Never exposes private client financial negotiations to vendors.
  - *Priority:* P0 (Critical Requirement)

---

## 7. Stage 6 — Actionable WhatsApp Share Flow (VERIFIED COMPLETE)

- [x] **Item 6.1: Communication Audit Entity (`backend/app/models/catering.py`)**
  - *Schema:* `id` (COM-XXXX), `catering_plan_id`, `vendor_id`, `recipient_phone`, `message_text`, `pdf_download_url`, `delivery_method` (`WhatsApp Manual Share`), `action_status` (`Initiated`), `initiated_by`, `created_at`.
  - *Priority:* P1 (High)

- [x] **Item 6.2: WhatsApp Share Endpoint (`backend/app/routes/catering.py`)**
  - `POST /api/v1/catering/{catering_id}/share-whatsapp`:
    1. Verifies selected vendor has a valid phone number.
    2. Formats a polite royal catering invitation briefing.
    3. Provides the PDF download URL.
    4. Encodes and returns `https://wa.me/{clean_phone}?text={encoded_message}`.
    5. Logs record in `catering_communications`.
  - *Integrity Rule:* Strictly labels action as `Initiated (WhatsApp Deep-Link)`. Does not falsely claim message was delivered/read.
  - *Priority:* P0 (Critical Requirement)

---

## 8. Stage 7 — Catering Frontend Staff UI (VERIFIED COMPLETE)

- [x] **Item 7.1: Catering Tab in `ProjectDetailsPage.tsx`**
  - Add 5th tab `Catering & Menus` (`activeTab === 'catering'`).
  - Shows event selector or cards for all ceremony functions.
  - Displays summary metrics: Total Catering Budget, Selected Vendors, Menu Statuses.
  - *Priority:* P0 (Critical)

- [x] **Item 7.2: Catering Event Card Component (`frontend/src/components/catering/CateringEventCard.tsx`)**
  - Displays event name, palace venue, service style, guest count (with override badge), menu items count, selected vendor, agreed cost, and status badge.
  - Action buttons: *Edit Requirements*, *Manage Menu*, *Vendor Quotations*, *Generate PDF*, *Share WhatsApp*.
  - *Priority:* P0 (Critical)

- [x] **Item 7.3: Catering Requirements Modal (`frontend/src/components/catering/CateringRequirementsModal.tsx`)**
  - Form fields: Service Style, Cuisines, Event Guest Count (prefilled with project count, override supported), Veg Pax, Non-Veg Pax, Jain Pax, Service Timings, Budget, Notes.
  - Includes loading, error banner, and success notification.
  - *Priority:* P0 (Critical)

- [x] **Item 7.4: Menu Builder & Presets Component (`frontend/src/components/catering/CateringMenuSection.tsx`)**
  - Preset dropdown: *Royal Rajputana Mewari Feast*, *Mughal Sheesh Mahal Degustation*, *Contemporary Pan-Asian Luxury*, or *Blank Custom Menu*.
  - Grouped course accordion (`Welcome Drinks`, `Starters`, `Mains`, `Live Counters`, `Desserts`).
  - Add dish modal with dietary tags (`Veg`, `Non-Veg`, `Jain`, `Gluten-Free`).
  - Edit/delete dish controls.
  - *Priority:* P0 (Critical)

- [x] **Item 7.5: Vendor Quotations & Comparison Modal (`frontend/src/components/catering/CateringQuotationsModal.tsx`)**
  - Multi-quote comparison table.
  - Add Quote Form: Vendor selector (or link to create vendor), Per-Person Rate, Guest Pax, Additional Equipment Charges, **Configurable GST % Dropdown (0%, 5%, 12%, 18%, Custom)**, Live Total Calculation, Validity Date.
  - "Select as Winner" button locking the agreed vendor and pricing.
  - *Priority:* P0 (Critical)

- [x] **Item 7.6: WhatsApp Share Modal (`frontend/src/components/catering/WhatsAppShareModal.tsx`)**
  - Displays vendor WhatsApp number, editable message text preview, copyable PDF link, and 1-click **"Open in WhatsApp"** button.
  - Confirms action initiation and logs history.
  - *Priority:* P0 (Critical)

- [x] **Item 7.7: Shared Vendors Management Page (`frontend/src/pages/VendorsPage.tsx`)**
  - Accessible from sidebar navigation under Registry & Vendors.
  - Lists registered palace vendors, contact persons, ratings, and phone numbers.
  - Add Vendor modal.
  - *Priority:* P1 (High)

---

## 9. Stage 8 — Testing & Verification (VERIFIED COMPLETE)

- [x] **Item 8.1: Pytest Catering Workflow Suite (`backend/tests/test_phase3_catering_workflow.py`)**
  - *Test 1:* Project function catering plan association & guest count override.
  - *Test 2:* Flexible dietary estimates acceptance (`veg + non_veg != total`).
  - *Test 3:* Preset menu population and custom dish additions.
  - *Test 4:* Vendor creation and quotation recording with configurable GST rate.
  - *Test 5:* Quotation selection and budget locking.
  - *Test 6:* ReportLab PDF generation stream (verifies `%PDF-1.4` header, content length > 5KB).
  - *Test 7:* WhatsApp deep-link generation and communication audit logging.
  - *Test 8:* Catering status transitions (`Draft` to `Vendor Confirmed`).
  - *Priority:* P0 (Critical)

- [x] **Item 8.2: End-to-End Regression & Verification**
  - All existing 17 backend tests continue passing (`pytest backend/tests/`).
  - Frontend TypeScript compiles cleanly (`tsc -b && vite build`) with zero errors.
  - No disruption to Phase 1 enquiry, client registration, or project setup flows.
  - *Priority:* P0 (Critical)

---

## 10. Master API Registry Maintenance

- [x] Update `docs/API_ENDPOINT_REGISTRY.md` during and after each stage.
- [x] Record exact request/response schemas, database models, frontend callers, and test outcomes.

---

## 11. Known Issues & Deferred Verifications

- [ ] **Issue REG-01: Client Registration Form Validation Error**
  - *Symptom:* During earlier Phase 1 testing, the client website registration form returned: `"Data validation failed. Please check the submitted fields."`
  - *Context:* The form was submitted with minimal/test inputs (`YOUR FULL NAME *` set to `"s"`, `PARTNER'S FULL NAME` set to `"s"`).
  - *Status:* **Recorded as a known issue for post-Phase 3 regression testing.**
  - *Action Plan (Deferred to after Phase 3 & branch integration):*
    - Verify actual backend HTTP 422 error payload against `WebsiteClientRegisterRequest` in `user.py`.
    - Improve frontend field-level error handling in `WebsiteRegistrationPage.tsx` so users see exact field errors rather than only a generic header alert.
    - Validate field rules: full name min length, partner name optionality, password min length (8 chars) & match, wedding date format (`YYYY-MM-DD`), guest count ($\ge 1$), and budget ($\ge 0$).
    - Full end-to-end activation link and client login verification.
  - *Note:* Do not interrupt Phase 3 Catering implementation to patch this; address after Phase 3 completion and branch integration approval.
