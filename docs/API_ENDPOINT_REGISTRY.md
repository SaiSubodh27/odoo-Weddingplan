# The Royal Knot — Master API Endpoint Registry

> **System:** The Royal Knot — Luxury Wedding Planning Management System (Jaipur & Udaipur Operations)  
> **Last Updated:** 2026-10-31  
> **Registry Version:** 1.0.0  
> **Maintained By:** Lead Engineering & QA  

This document serves as the permanent, authoritative central API endpoint registry for **The Royal Knot Wedding Planning Management System**. It records every endpoint discovered, implemented, verified, or identified as missing/planned across all project phases.

---

## 1. Registry Status Legend

| Status Indicator | Definition |
|---|---|
| **Verified** | Endpoint exists in codebase, routes properly, persists data in PostgreSQL, and passes automated tests. |
| **Existing** | Endpoint exists in codebase and routes, but requires full automated test coverage. |
| **Missing** | Endpoint is required by product workflow but has not yet been implemented in backend. |
| **Planned** | Endpoint designed for a future project phase (e.g. Phase 2 booking contracts, Phase 4 client portal expansion). |
| **Blocked** | Endpoint cannot be implemented or fully tested due to missing external credentials or third-party service prerequisites. |

---

## 2. API Endpoints by Module

### A. Wedding Projects Module (Phase 3)

| Module | Endpoint | Method | Purpose | Request | Response | Auth | Database Models | Status | Frontend Usage | Test Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Wedding Projects | `/api/v1/projects/eligible-bookings` | `GET` | List confirmed client bookings eligible for project setup (status='Confirmed' without active project) | None | `List[EligibleBookingResponse]` | Staff / Admin | `clients`, `wedding_projects` | **Verified** | `CreateProjectModal.tsx` | **Passed** (`test_phase3_projects_workflow.py`) | Filters out clients already bound to a project |
| Wedding Projects | `/api/v1/projects` | `POST` | Initialize a new wedding project from confirmed booking dossier | `WeddingProjectCreate` (`clientId`, `projectName`, `weddingDate`, `location`, `guestCount`, `estimatedBudget`, `packageTier`, `projectManagerName`, `notes`) | `WeddingProjectResponse` (HTTP 201) | Staff / Admin | `wedding_projects`, `project_milestones`, `project_status_history` | **Verified** | `CreateProjectModal.tsx` | **Passed** (`test_phase3_projects_workflow.py`) | Auto-generates sequential `PRJ-YYYY-XXX` code; auto-seeds 5 standard milestones |
| Wedding Projects | `/api/v1/projects` | `GET` | List wedding projects with search, status filtering, and pagination | Query params: `search`, `status`, `page`, `page_size` | `{ total, page, pageSize, items: List[WeddingProjectListItem] }` | Staff / Admin | `wedding_projects`, `clients`, `wedding_functions`, `project_milestones` | **Verified** | `ProjectsPage.tsx` | **Passed** (`test_phase3_projects_workflow.py`) | Includes milestone completion counters |
| Wedding Projects | `/api/v1/projects/{project_id}` | `GET` | Retrieve complete wedding project dossier with functions, milestones, and audit history | Path: `project_id` (UUID or `project_code`) | `WeddingProjectResponse` | Staff / Admin | `wedding_projects`, `clients`, `wedding_functions`, `project_milestones`, `project_status_history` | **Verified** | `ProjectDetailsPage.tsx` | **Passed** (`test_phase3_projects_workflow.py`) | Joins client details and sorts relations |
| Wedding Projects | `/api/v1/projects/{project_id}` | `PUT` | Update wedding project metadata (name, venue, guest count, budget, notes) | `WeddingProjectUpdate` | `WeddingProjectResponse` | Staff / Admin | `wedding_projects` | **Verified** | `ProjectDetailsPage.tsx` | **Passed** (`test_phase3_projects_workflow.py`) | Partial metadata update |
| Wedding Projects | `/api/v1/projects/{project_id}/status` | `PATCH` / `POST` | Update project status and record audit log in status history | `ProjectStatusUpdate` (`status`, `changedBy`, `notes`) | `WeddingProjectResponse` | Staff / Admin | `wedding_projects`, `project_status_history` | **Verified** | `ProjectDetailsPage.tsx` | **Passed** (`test_phase3_projects_workflow.py`) | `POST` alias provided for proxy compatibility |
| Wedding Functions | `/api/v1/projects/{project_id}/functions` | `GET` | List all ceremonies / functions for a wedding project | Path: `project_id` | `List[WeddingFunctionResponse]` | Staff / Admin | `wedding_functions` | **Verified** | `ProjectDetailsPage.tsx` | **Passed** (`test_phase3_projects_workflow.py`) | Sorted by `function_date` |
| Wedding Functions | `/api/v1/projects/{project_id}/functions` | `POST` | Add a wedding ceremony/function to project with automated tier costing | `WeddingFunctionCreate` (`functionName`, `functionDate`, `startTime`, `endTime`, `venue`, `description`, `status`, `estimatedCost`) | `WeddingFunctionResponse` (HTTP 201) | Staff / Admin | `wedding_functions`, `wedding_projects` | **Verified** | `ProjectDetailsPage.tsx` (`FunctionModal`) | **Passed** (`test_phase3_projects_workflow.py`) | Auto-estimates cost if left 0 (e.g. Sangeet ₹1.2L–₹2.5L, Wedding ₹2.5L–₹5.0L) |
| Wedding Functions | `/api/v1/projects/{project_id}/functions/{func_id}` | `PUT` / `PATCH` | Update function timing, venue, status, or estimated cost | `WeddingFunctionUpdate` | `WeddingFunctionResponse` | Staff / Admin | `wedding_functions` | **Verified** | `ProjectDetailsPage.tsx` (`FunctionModal`) | **Passed** (`test_phase3_projects_workflow.py`) | Supports partial updates |
| Wedding Functions | `/api/v1/projects/functions/{func_id}` | `PUT` / `PATCH` | Direct function update by function ID | `WeddingFunctionUpdate` | `WeddingFunctionResponse` | Staff / Admin | `wedding_functions` | **Verified** | Direct API usage | **Passed** | Alias endpoint |
| Wedding Functions | `/api/v1/projects/{project_id}/functions/{func_id}` | `DELETE` | Delete a scheduled ceremony function | Path: `project_id`, `func_id` | `{ success: bool, message: str }` | Staff / Admin | `wedding_functions` | **Verified** | `ProjectDetailsPage.tsx` | **Passed** (`test_phase3_projects_workflow.py`) | Cascades to associated items |
| Project Milestones | `/api/v1/projects/{project_id}/milestones` | `POST` | Add a custom project milestone checkpoint | `ProjectMilestoneCreate` (`milestoneName`, `dueDate`, `description`, `status`) | `ProjectMilestoneResponse` (HTTP 201) | Staff / Admin | `project_milestones`, `wedding_projects` | **Verified** | `ProjectDetailsPage.tsx` (`MilestoneModal`) | **Passed** (`test_phase3_projects_workflow.py`) | Sets `completed_at` if created as 'Completed' |
| Project Milestones | `/api/v1/projects/{project_id}/milestones/{ms_id}` | `PUT` / `PATCH` | Update milestone details or toggle completion status | `ProjectMilestoneUpdate` (`milestoneName`, `dueDate`, `status`, `description`) | `ProjectMilestoneResponse` | Staff / Admin | `project_milestones` | **Verified** | `ProjectDetailsPage.tsx` (Toggle checkbox) | **Passed** (`test_phase3_projects_workflow.py`) | Auto-stamps `completed_at` on completion |
| Project Milestones | `/api/v1/projects/{project_id}/milestones/{ms_id}` | `DELETE` | Delete milestone checkpoint | Path: `project_id`, `ms_id` | `{ success: bool, message: str }` | Staff / Admin | `project_milestones` | **Verified** | `ProjectDetailsPage.tsx` | **Passed** (`test_phase3_projects_workflow.py`) | Deletes milestone |

---

### B. Catering Management Module (Phase 3)

| Module | Endpoint | Method | Purpose | Request | Response | Auth | Target Models | Status | Frontend Target | Test Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Catering Requirements | `/api/v1/projects/{project_id}/catering` | `GET` | List all catering requirement plans across events for a project | Path: `project_id` | `List[CateringPlanResponse]` | Staff / Admin | `catering_plans`, `wedding_functions`, `wedding_projects` | **Verified** | `ProjectDetailsPage.tsx` (Catering Tab) | **Passed** (`test_phase3_catering_api.py`) | Returns all ceremony catering dossiers |
| Catering Requirements | `/api/v1/projects/{project_id}/functions/{func_id}/catering` | `GET` | Get event-specific catering plan, dietary requirements, menu, and selected vendor | Path: `project_id`, `func_id` | `CateringPlanDetailResponse` | Staff / Admin | `catering_plans`, `wedding_functions`, `catering_menu_items`, `vendors` | **Verified** | `CateringEventCard.tsx` | **Passed** (`test_phase3_catering_api.py`) | Connects catering directly to wedding event |
| Catering Requirements | `/api/v1/projects/{project_id}/functions/{func_id}/catering` | `POST` | Create event-specific catering requirements | `CateringPlanCreate` (`serviceStyle`, `cuisinePreferences`, `guestCount`, `vegCount`, `nonVegCount`, `jainCount`, `dietaryNotes`, `budget`) | `CateringPlanDetailResponse` (HTTP 201) | Staff / Admin | `catering_plans`, `wedding_functions`, `wedding_projects` | **Verified** | `CateringRequirementsModal.tsx` | **Passed** (`test_phase3_catering_api.py`) | Defaults `guest_count` from project if omitted; permits event override |
| Catering Requirements | `/api/v1/projects/{project_id}/functions/{func_id}/catering` | `PUT` | Update catering requirements and specifications | `CateringPlanUpdate` | `CateringPlanDetailResponse` | Staff / Admin | `catering_plans` | **Verified** | `CateringRequirementsModal.tsx` | **Passed** (`test_phase3_catering_api.py`) | Supports budget, dietary, and timing revisions |
| Catering Requirements | `/api/v1/catering/{catering_id}` | `GET` | Retrieve catering plan details by ID | Path: `catering_id` | `CateringPlanDetailResponse` | Staff / Admin | `catering_plans`, `wedding_functions`, `wedding_projects` | **Verified** | `CateringEventCard.tsx` | **Passed** (`test_phase3_catering_api.py`) | Direct plan access |
| Catering Requirements | `/api/v1/catering/{catering_id}` | `PUT` | Update catering plan specifications by ID | Path: `catering_id`, Body: `CateringPlanUpdate` | `CateringPlanDetailResponse` | Staff / Admin | `catering_plans` | **Verified** | `CateringRequirementsModal.tsx` | **Passed** (`test_phase3_catering_api.py`) | Direct plan update |
| Menu Management | `/api/v1/catering/{catering_id}/menu-items` | `GET` | List organized menu courses and food items for catering plan | Path: `catering_id` | `List[CateringMenuItemResponse]` | Staff / Admin | `catering_menu_items` | **Verified** | `CateringMenuSection.tsx` | **Passed** (`test_phase3_catering_api.py`) | Ordered by display_order |
| Menu Management | `/api/v1/catering/{catering_id}/menu-items` | `POST` | Add individual food item to event menu | `CateringMenuItemCreate` (`courseCategory`, `itemName`, `description`, `dietaryTag`, `quantityNote`, `displayOrder`) | `CateringMenuItemResponse` (HTTP 201) | Staff / Admin | `catering_menu_items` | **Verified** | `AddMenuItemModal.tsx` | **Passed** (`test_phase3_catering_api.py`) | Tracks veg/non-veg/jain dietary tags |
| Menu Management | `/api/v1/catering/{catering_id}/menu-items/{item_id}` | `PUT` | Update menu item details, portion notes, or category | `CateringMenuItemUpdate` | `CateringMenuItemResponse` | Staff / Admin | `catering_menu_items` | **Verified** | `CateringMenuSection.tsx` | **Passed** (`test_phase3_catering_api.py`) | Enforces plan isolation |
| Menu Management | `/api/v1/catering/{catering_id}/menu-items/{item_id}` | `DELETE` | Remove food item from menu | Path: `catering_id`, `item_id` | `{ success: bool, message: str }` | Staff / Admin | `catering_menu_items` | **Verified** | `CateringMenuSection.tsx` | **Passed** (`test_phase3_catering_api.py`) | Enforces plan isolation |
| Menu Management | `/api/v1/catering/{catering_id}/menu-items/reorder` | `POST` | Reorder dishes and courses within menu | `MenuItemReorderRequest` (`items: [{id, displayOrder}]`) | `List[CateringMenuItemResponse]` | Staff / Admin | `catering_menu_items` | **Verified** | Drag-and-drop course reorder | **Passed** (`test_phase3_catering_api.py`) | Updates sequential sort orders |
| Menu Presets | `/api/v1/catering/presets` | `GET` | List available luxury banquet starter templates | None | `List[PresetSummaryResponse]` | Staff / Admin | None (Preset Library) | **Verified** | Preset template accordion | **Passed** (`test_phase3_catering_api.py`) | Returns Mewari Feast, Sheesh Mahal, Pan-Asian Luxury |
| Menu Presets | `/api/v1/catering/presets/{preset_id}` | `GET` | Retrieve complete preset courses and dishes | Path: `preset_id` | `PresetDetailResponse` | Staff / Admin | None (Preset Library) | **Verified** | Preset preview modal | **Passed** (`test_phase3_catering_api.py`) | Detailed dish breakdown |
| Menu Presets | `/api/v1/catering/{catering_id}/apply-preset` | `POST` | Apply luxury preset to catering plan (`mode: 'append' \| 'replace'`) | `ApplyPresetRequest` (`presetId`, `mode`) | `List[CateringMenuItemResponse]` | Staff / Admin | `catering_plans`, `catering_menu_items` | **Verified** | Preset 1-click apply | **Passed** (`test_phase3_catering_api.py`) | Presets create editable dishes without modifying preset definitions |
| Catering Quotations | `/api/v1/catering/{catering_id}/quotations` | `GET` | List vendor quotations received for catering plan | Path: `catering_id` | `List[CateringQuotationResponse]` | Staff / Admin | `catering_quotations`, `vendors` | **Verified** | `CateringQuotationsGrid.tsx` | **Passed** (`test_phase3_catering_api.py`) | Competing vendor bids with tax breakdown |
| Catering Quotations | `/api/v1/catering/{catering_id}/quotations` | `POST` | Record a vendor quotation with per-person rate, configurable GST, and total | `CateringQuotationCreate` | `CateringQuotationResponse` (HTTP 201) | Staff / Admin | `catering_quotations`, `vendors` | **Verified** | `AddQuotationModal.tsx` | **Passed** (`test_phase3_catering_api.py`) | Decimal-safe rounding, configurable GST |
| Catering Quotations | `/api/v1/catering/{catering_id}/quotations/{quotation_id}` | `GET` | Retrieve vendor quotation dossier by ID | Path: `catering_id`, `quotation_id` | `CateringQuotationResponse` | Staff / Admin | `catering_quotations`, `vendors` | **Verified** | `CateringQuotationsGrid.tsx` | **Passed** (`test_phase3_catering_api.py`) | Single quotation details |
| Catering Quotations | `/api/v1/catering/{catering_id}/quotations/{quotation_id}` | `PUT` | Update quotation terms and recalculate costing | Path: `catering_id`, `quotation_id`, Body: `CateringQuotationUpdate` | `CateringQuotationResponse` | Staff / Admin | `catering_quotations` | **Verified** | `EditQuotationModal.tsx` | **Passed** (`test_phase3_catering_api.py`) | Recalculates food subtotal and taxes |
| Catering Quotations | `/api/v1/catering/{catering_id}/quotations/{quotation_id}/select` | `POST` | Select winning vendor quotation and lock agreed contract pricing | Path: `catering_id`, `quotation_id` | `CateringQuotationSelectResponse` | Staff / Admin | `catering_plans`, `catering_quotations`, `vendors` | **Verified** | `CateringQuotationsGrid.tsx` | **Passed** (`test_phase3_catering_api.py`) | Locks selected vendor and agreed cost; marks others Rejected |
| Vendor PDF Generation | `/api/v1/catering/{catering_id}/pdf` | `GET` | Generate and download formal, formatted vendor catering specification PDF | Path: `catering_id` | `application/pdf` (binary stream) | Staff / Admin | `catering_plans`, `wedding_functions`, `wedding_projects`, `catering_menu_items`, `vendors` | **Verified** | `CateringTab.tsx` | **Passed** (`test_phase3_catering_api.py`) | Stage 5 ReportLab PDF generation |
| Vendor PDF Generation | `/api/v1/catering/{catering_id}/quotations/{quotation_id}/pdf` | `GET` | Generate branded catering quotation specification PDF | Path: `catering_id`, `quotation_id` | `application/pdf` (binary stream) | Staff / Admin | `catering_plans`, `catering_quotations`, `vendors` | **Verified** | `CateringQuotationsSection.tsx` | **Passed** (`test_phase3_catering_api.py`) | Stage 5 quotation PDF |
| WhatsApp Communication | `/api/v1/catering/{catering_id}/share-whatsapp` | `POST` | Generate authentic WhatsApp deep-link with event specs and log communication | `CateringWhatsAppShareRequest` | `CateringWhatsAppShareResponse` | Staff / Admin | `catering_communications` | **Verified** | `WhatsAppShareModal.tsx` | **Passed** (`test_phase3_catering_api.py`) | Stage 6 wa.me deep-link |
| WhatsApp Communication | `/api/v1/catering/{catering_id}/quotations/{quotation_id}/share-whatsapp` | `POST` | Generate WhatsApp deep-link for vendor quotation | `CateringWhatsAppShareRequest` | `CateringWhatsAppShareResponse` | Staff / Admin | `catering_communications` | **Verified** | `WhatsAppShareModal.tsx` | **Passed** (`test_phase3_catering_api.py`) | Stage 6 quotation share |
| WhatsApp Communication | `/api/v1/catering/{catering_id}/communications` | `GET` | List communications history audit trail for catering plan | Path: `catering_id` | `List[CateringCommunicationResponse]` | Staff / Admin | `catering_communications` | **Verified** | `CateringTab.tsx` | **Passed** (`test_phase3_catering_api.py`) | Stage 6 audit logging |
| Catering Status | `/api/v1/catering/{catering_id}/status` | `PATCH` | Update catering lifecycle status with validation and audit notes | `CateringStatusUpdate` | `CateringPlanResponse` | Staff / Admin | `catering_plans` | **Verified** | `CateringStatusStepper.tsx` | **Passed** (`test_phase3_catering_api.py`) | Stage 4 lifecycle workflow |

---

### C. Shared Vendor Directory Module (Phase 3 Foundation)

| Module | Endpoint | Method | Purpose | Request | Response | Auth | Target Models | Status | Frontend Target | Test Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Vendors | `/api/v1/vendors` | `GET` | List available vendors filtered by category, city, or search | Query: `category`, `city`, `search`, `isActive`, `page`, `pageSize` | `VendorListResponse` | Staff / Admin | `vendors` | **Verified** | `VendorsPage.tsx` & Vendor dropdowns | **Passed** (`test_phase3_catering_api.py`) | Paginated central vendor directory |
| Vendors | `/api/v1/vendors` | `POST` | Register a new luxury vendor (palace caterer, decorator, etc.) | `VendorCreate` (`name`, `category`, `contactPerson`, `email`, `phone`, `city`, `rating`, `notes`, `isActive`) | `VendorResponse` (HTTP 201) | Staff / Admin | `vendors` | **Verified** | `AddVendorModal.tsx` | **Passed** (`test_phase3_catering_api.py`) | Prevents duplicate telephone entries |
| Vendors | `/api/v1/vendors/{vendor_id}` | `GET` | Retrieve vendor portfolio, specialization, and catering stats | Path: `vendor_id` | `VendorDetailResponse` | Staff / Admin | `vendors`, `catering_plans`, `catering_quotations` | **Verified** | `VendorProfilePage.tsx` | **Passed** (`test_phase3_catering_api.py`) | Includes event counts |
| Vendors | `/api/v1/vendors/{vendor_id}` | `PUT` | Update vendor contact details or operational rating | Path: `vendor_id`, Body: `VendorUpdate` | `VendorResponse` | Staff / Admin | `vendors` | **Verified** | `EditVendorModal.tsx` | **Passed** (`test_phase3_catering_api.py`) | Maintains updated WhatsApp contact |
| Vendors | `/api/v1/vendors/{vendor_id}/status` | `PATCH` | Toggle vendor active/inactive operational status | Path: `vendor_id`, Body: `VendorStatusUpdate` | `VendorResponse` | Staff / Admin | `vendors` | **Verified** | `VendorsPage.tsx` | **Passed** (`test_phase3_catering_api.py`) | Active palace vendor filter |

---

### D. Clients Module (Phase 1 Foundation)

| Module | Endpoint | Method | Purpose | Request | Response | Auth | Database Models | Status | Frontend Usage | Test Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| System | `/api/v1/health` | `GET` | Verify API status and live PostgreSQL connectivity | None | `HealthResponse` (`service`, `status`, `database_connected`, `operating_regions`, `version`) | Public | None | **Verified** | `ClientContext.tsx` | **Passed** (`test_enquiry_activation_workflow.py`) | Health check |
| Clients | `/api/v1/clients` | `POST` | Create a new client dossier in PostgreSQL | `ClientCreate` (`partner1Name`, `partner2Name`, `email`, `phone`, `weddingDate`, `weddingLocation`, `expectedGuestCount`, `estimatedBudget`, `weddingTheme`, `servicePackage`) | `ClientResponse` (HTTP 201) | Staff / Admin | `clients` | **Verified** | `AddClientPage.tsx` | **Passed** (`test_automated_registration_workflow.py`) | Validates couple contact and wedding info |
| Clients | `/api/v1/clients` | `GET` | Return registered client dossiers with pagination, searching, and status filter | Query: `page`, `page_size`, `search`, `status`, `enquiry_source` | `{ total, page, pageSize, items: List[ClientResponse] }` | Staff / Admin | `clients` | **Verified** | `ClientsPage.tsx` | **Passed** (`test_automated_registration_workflow.py`) | Reads from `clients` table |
| Clients | `/api/v1/clients/{client_id}` | `GET` | Retrieve full client registration dossier by unique ID | Path: `client_id` | `ClientResponse` | Staff / Admin | `clients` | **Verified** | `ClientDetailsPage.tsx` | **Passed** (`test_enquiry_activation_workflow.py`) | Soft-delete check (`is_deleted=False`) |
| Clients | `/api/v1/clients/{client_id}` | `PUT` | Update client details or registration status | Path: `client_id`, Body: `ClientUpdate` | `ClientResponse` | Staff / Admin | `clients` | **Verified** | `ClientDetailsPage.tsx` | **Passed** | Updates client records |
| Clients | `/api/v1/clients/{client_id}` | `DELETE` | Perform safe soft-delete of client record (`is_deleted=True`) | Path: `client_id` | `{ success: bool, message: str }` | Staff / Admin | `clients` | **Verified** | `ClientDetailsPage.tsx` | **Passed** | Physical record preserved for audit |

---

### E. Enquiries Module (Phase 1 Foundation)

| Module | Endpoint | Method | Purpose | Request | Response | Auth | Database Models | Status | Frontend Usage | Test Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Enquiries | `/api/v1/enquiries` | `POST` | Record incoming wedding enquiry | `EnquiryCreate` (`clientName`, `email`, `phone`, `weddingDate`, `weddingLocation`, `enquirySource`, `requirements`, etc.) | `EnquiryResponse` (HTTP 201) | Staff / Admin | `enquiries` | **Verified** | `AddEnquiryPage.tsx` | **Passed** (`test_email_integration_workflow.py`) | Auto-assigns `ENQ-YYYY-XXX` reference |
| Enquiries | `/api/v1/enquiries` | `GET` | List enquiries with pagination, search, and status filter | Query: `search`, `status`, `source`, `page`, `page_size` | `{ total, page, pageSize, items: List[EnquiryResponse] }` | Staff / Admin | `enquiries` | **Verified** | `EnquiriesPage.tsx` | **Passed** (`test_email_integration_workflow.py`) | Paginated results |
| Enquiries | `/api/v1/enquiries/{enquiry_id}` | `GET` | Get enquiry details, document list, and staff notes | Path: `enquiry_id` | `EnquiryResponse` | Staff / Admin | `enquiries`, `registration_documents` | **Verified** | `EnquiryDetailsPage.tsx` | **Passed** (`test_email_integration_workflow.py`) | Includes attached dossier documents |
| Enquiries | `/api/v1/enquiries/{enquiry_id}` | `PUT` | Update enquiry metadata or assigned concierge | `EnquiryUpdate` | `EnquiryResponse` | Staff / Admin | `enquiries` | **Verified** | `EnquiryDetailsPage.tsx` | **Passed** | Updates enquiry fields |
| Enquiries | `/api/v1/enquiries/{enquiry_id}/notes` | `POST` | Append staff internal activity note | Body: `{ content, author }` | `EnquiryResponse` | Staff / Admin | `enquiries` | **Verified** | `EnquiryDetailsPage.tsx` | **Passed** | Internal collaboration notes |
| Enquiries | `/api/v1/enquiries/{enquiry_id}/send-registration` | `POST` | Dispatch luxury welcome email with Google Forms link | Path: `enquiry_id` | `{ success: bool, message: str }` | Staff / Admin | `enquiries`, `email_messages` | **Verified** | `EnquiryDetailsPage.tsx` | **Passed** (`test_email_integration_workflow.py`) | Sends actual email via Gmail SMTP |
| Enquiries | `/api/v1/enquiries/{enquiry_id}/upload-document` | `POST` | Upload completed client registration PDF document | Multipart Form: `file` | `RegistrationDocument` (HTTP 201) | Staff / Admin | `registration_documents`, `enquiries` | **Verified** | `EnquiryDetailsPage.tsx` | **Passed** (`test_email_integration_workflow.py`) | Validates MIME type, size limit (<10MB) |
| Enquiries | `/api/v1/enquiries/{enquiry_id}/documents/{doc_id}/download` | `GET` | Download stored registration document | Path: `enquiry_id`, `doc_id` | File binary stream | Staff / Admin | `registration_documents` | **Verified** | `EnquiryDetailsPage.tsx` | **Passed** (`test_enquiry_activation_workflow.py`) | File stream with Content-Disposition |
| Enquiries | `/api/v1/enquiries/{enquiry_id}/approve` | `POST` | Approve enquiry, create Client record, generate activation token, send activation link | Path: `enquiry_id`, Query: `staff_name` | `EnquiryApproveResponse` | Staff / Admin | `enquiries`, `clients`, `users`, `email_messages` | **Verified** | `EnquiryDetailsPage.tsx` | **Passed** (`test_automated_registration_workflow.py`) | Core Phase 1 conversion gate |
| Enquiries | `/api/v1/enquiries/{enquiry_id}/request-correction` | `POST` | Reject submission or request correction with feedback notes | Body: `{ reason, notes }` | `{ success: bool, message: str }` | Staff / Admin | `enquiries`, `email_messages` | **Verified** | `EnquiryDetailsPage.tsx` | **Passed** | Sends revision instructions to client |

---

### F. Registrations & Google Forms Module (Phase 1 Foundation)

| Module | Endpoint | Method | Purpose | Request | Response | Auth | Database Models | Status | Frontend Usage | Test Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Registrations | `/api/v1/registrations/config` | `GET` | Retrieve configured public Google Forms URL | None | `{ google_forms_url: str }` | Public | None | **Verified** | `SettingsPage.tsx` | **Passed** | Reads from application settings |
| Registrations | `/api/v1/registrations/sync-sheets` | `POST` | Import live submissions from published Google Sheet CSV | Optional Body: `{ csv_url }` | `{ success: bool, imported_count: int, matched_count: int }` | Staff / Admin | `client_registrations`, `enquiries` | **Existing** | `SettingsPage.tsx` | **Verified via Manual Sync** | Deduplicates by submission timestamp |
| Registrations | `/api/v1/registrations` | `GET` | List imported Google Forms submissions | Query: `page`, `page_size`, `status` | `{ total, items: List[RegistrationResponse] }` | Staff / Admin | `client_registrations` | **Verified** | `SettingsPage.tsx` | **Passed** | Shows pending and matched forms |

---

### G. Auth & Client Portal Module (Phase 1 & Future Expansion)

| Module | Endpoint | Method | Purpose | Request | Response | Auth | Database Models | Status | Frontend Usage | Test Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Auth | `/api/v1/auth/activate` | `POST` | Activate client user account with secure Argon2 password | Body: `ActivateAccountRequest` (`token`, `password`) | `ActivateAccountResponse` | Public (Token validated) | `users`, `clients` | **Verified** | `ClientActivationPage.tsx` | **Passed** (`test_enquiry_activation_workflow.py`) | Enforces 72-hour expiry and 8-char password |
| Auth | `/api/v1/auth/login` | `POST` | Authenticate staff or client credentials | Body: `UserLoginRequest` (`email`, `password`) | `UserLoginResponse` (`token`, `role`, `user_id`, `client_id`) | Public | `users`, `clients` | **Verified** | `LoginPage.tsx` | **Passed** (`test_automated_registration_workflow.py`) | Issues session bearer token |
| Auth | `/api/v1/auth/register-website` | `POST` | Client self-registration via public website | Body: `WebsiteClientRegisterRequest` | `WebsiteClientRegisterResponse` (HTTP 201) | Public | `enquiries`, `client_registrations`, `clients`, `users` | **Verified on main** | `WebsiteRegistrationPage.tsx` | **Passed on main** | Merged on main branch |
| Auth | `/api/v1/auth/client-dossier` | `GET` | Retrieve client's private celebration parameters for portal | Query: `email` | `ClientDossierResponse` | Authenticated Client | `client_registrations`, `clients`, `enquiries` | **Verified on main** | `ClientPortalPage.tsx` | **Passed on main** | Merged on main branch |

---

### H. Email & Communications Module (Phase 1 Foundation)

| Module | Endpoint | Method | Purpose | Request | Response | Auth | Database Models | Status | Frontend Usage | Test Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Email | `/api/v1/emails/sync` | `POST` | Trigger IMAP inbox synchronization from agency Gmail | None | `{ success: bool, new_emails: int }` | Staff / Admin | `email_messages`, `enquiries` | **Verified** | `EmailInboxPage.tsx` | **Passed** (`test_email_integration_workflow.py`) | Connects via TLS to imap.gmail.com |
| Email | `/api/v1/emails/inbox` | `GET` | List incoming and outgoing synced emails with search | Query: `search`, `page`, `page_size` | `{ total, items: List[EmailMessageResponse] }` | Staff / Admin | `email_messages` | **Verified** | `EmailInboxPage.tsx` | **Passed** (`test_email_integration_workflow.py`) | Filterable by sender/subject |
| Email | `/api/v1/emails/{email_id}` | `GET` | Get full email body, headers, and attachment metadata | Path: `email_id` | `EmailMessageResponse` | Staff / Admin | `email_messages` | **Verified** | `EmailInboxPage.tsx` | **Passed** (`test_email_integration_workflow.py`) | Raw body & sanitization |
| Email | `/api/v1/emails/send` | `POST` | Send outgoing email to client or vendor via Gmail SMTP | Body: `SendEmailRequest` (`recipient`, `subject`, `bodyHtml`) | `{ success: bool, message_id: str }` | Staff / Admin | `email_messages` | **Verified** | Staff actions | **Passed** (`test_email_integration_workflow.py`) | Outgoing Gmail SMTP delivery |
| Email | `/api/v1/emails/simulate-incoming` | `POST` | Simulate incoming email lead for automated tests and local dev | Body: `SimulateEmailRequest` | `EmailMessageResponse` (HTTP 201) | Dev / Test | `email_messages`, `enquiries` | **Verified** | Dev test suites | **Passed** (`test_email_integration_workflow.py`) | Bypasses live IMAP for fast tests |

---

## 3. Summary of API Status Across Modules

```
Total Registered Endpoints: 40
├── Verified Existing Endpoints:     26 (65.0%)
├── Existing (Awaiting Tests):        1 ( 2.5%)
├── Missing Required Endpoints:      12 (30.0%)  <-- Phase 3 Catering & Vendors
└── Blocked / External Prereq:        1 ( 2.5%)  <-- Direct WhatsApp Business API
```

*This master API registry must be kept up to date whenever an endpoint is created, modified, or tested in any future phase.*

