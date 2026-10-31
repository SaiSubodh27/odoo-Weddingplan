# The Royal Knot — Routes, API endpoints and integration status

Updated: 2026-11-01. Source of truth: `frontend/src/App.tsx`, `backend/app/main.py` and `backend/app/routes/*.py`. This documents declared routes, **not** proof of live server/database availability.

## Frontend routes

| URL | Screen | Access |
| --- | --- | --- |
| `/login` | Sign in and signup interface | Public |
| `/activate` | Client account activation | Public |
| `/vendor-portal` | Vendor dashboard, clients, requests, bookings, messages, crew, business | Public prototype (no role guard) |
| `/founder-portal` | Overview, vendors, employees, profit analysis, finances | Public prototype (no role guard) |
| `/` | Redirect to `/dashboard` | Protected layout |
| `/dashboard` | Agency dashboard | Protected |
| `/inbox` | Email inbox | Protected |
| `/enquiries` | Enquiry list | Protected |
| `/enquiries/new` | New enquiry | Protected |
| `/enquiries/:id` | Enquiry details | Protected |
| `/clients` | Client directory | Protected |
| `/clients/new` | Add client | Protected |
| `/clients/:id` | Client dossier | Protected |
| `/weddings` | Weddings list | Protected |
| `/weddings/:id` | Wedding project | Protected |
| `/vendors` | Vendor directory | Protected |
| `/quotations` | Currently reuses VendorDirectoryPage | Protected |
| `/settings` | Settings | Protected |
| `*` | Redirect to `/dashboard` | Fallback |

Protected means the frontend `ProtectedRoute` checks `ClientContext.isAuthenticated`. This alone is not a server-side authorization boundary.

## Backend API

Base prefix: `/api/v1` (from `settings.API_V1_STR`). The FastAPI interactive docs are at `/docs`, ReDoc at `/redoc`, and OpenAPI JSON at `/openapi.json` when the backend is running.

### System
- `GET /` — root information
- `GET /health` — service health
- `GET /api/v1/health` — database-backed client service health

### Authentication — `/api/v1/auth`
- `GET /verify-token` — validate client activation token
- `POST /activate` — activate account and set password
- `POST /login` — login with existing credentials

### Clients — `/api/v1`
- `POST /clients` — create client dossier
- `GET /clients` — list/search/filter clients
- `GET /clients/{client_id}` — client details
- `PUT /clients/{client_id}` — update client
- `DELETE /clients/{client_id}` — soft-delete client

### Enquiries — `/api/v1/enquiries`
- `POST /` — create enquiry
- `GET /` — list enquiries
- `GET /{enquiry_id}` — details
- `PUT /{enquiry_id}` — update enquiry
- `POST /{enquiry_id}/notes` — add note
- `GET /{enquiry_id}/registration-template` — registration template
- `POST /{enquiry_id}/documents/upload` — upload document
- `GET /{enquiry_id}/documents` — list documents
- `GET /{enquiry_id}/documents/{document_id}/download` — download document
- `POST /{enquiry_id}/send-document` — send registration document
- `POST /{enquiry_id}/mark-document-received` — mark received
- `POST /{enquiry_id}/mark-document-reviewed` — mark reviewed
- `GET /{enquiry_id}/messages` — message history
- `POST /{enquiry_id}/reply` — reply
- `POST /{enquiry_id}/register` — register enquiry as client

### Emails — `/api/v1/emails`
- `GET /status` — email integration status
- `POST /sync` — sync mailbox
- `GET /inbox` — inbox messages
- `GET /{email_id}` — email details
- `POST /{email_id}/convert-to-enquiry` — convert to enquiry
- `POST /{email_id}/associate` — associate email
- `POST /{email_id}/ignore` — ignore email
- `GET /{email_id}/attachments/{attachment_id}/download` — download attachment
- `POST /simulate` — simulate incoming email

All endpoint paths in the sections above are relative to the stated section prefix unless already fully qualified.

## New frontend-only modules and status

- `FounderPortalPage.tsx`: founder overview, vendor directory, employee directory, profit and finance summaries. Uses demo data and localStorage, not dedicated founder API endpoints.
- `VendorPortalPage.tsx`: vendor workspace, bookings, requests, messages and business profile. Demo state, not a production vendor API.
- `VendorBookingWorkspace.tsx`: booking Overview, Crew and Payments tabs.
- `VendorBookingCrew.tsx`: per-booking crew assignments.
- `VendorCrewManager.tsx`: crew roster management.
- `VendorCrewWorkload.tsx`: demo workload view.
- `LoginPage.tsx` and `LoginPage.css`: sign-in and signup UI with User, Employee and Vendor selection and email/phone input. **Signup is not wired to account creation or SMS verification**. Google and Yahoo signup UI has been removed.
- Founder employee Layoff control opens a prefilled Gmail compose window; it does not send mail automatically or confirm delivery. Removing an employee affects only the local demo directory.

## Security and implementation notes

1. Founder and vendor routes currently bypass the frontend ProtectedRoute; **add server-backed authentication and role-based authorization before deployment**.
2. Do not treat localStorage demo records as authoritative business data.
3. Signup and phone OTP require backend endpoints, verification, validation, approval and account persistence.
4. Employee termination flow is a prototype and should not be treated as a complete HR workflow.
5. `/quotations` currently points to `VendorDirectoryPage`, not a dedicated quotations screen.
6. The backend's `/openapi.json` is the authoritative runtime schema for request bodies, responses and status codes.

## Development checks

Frontend: `cd frontend && npm install && npm run dev`; production compilation: `npm run build`. Backend setup: consult `backend/README.md` and `backend/.env.example`. Do not commit secrets or `.env` files.
