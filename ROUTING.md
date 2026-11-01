# Royal Knot — Routing Reference

## Frontend routes
Source: frontend/src/App.tsx. React Router BrowserRouter. ClientProvider wraps the app. All dashboard-layout routes require authentication; unauthenticated visitors redirect to /login.

| Path | Component | Access | Purpose |
|---|---|---|---|
| /login | LoginPage | Public | Agency login |
| /activate | ClientActivationPage | Public | Client activation |
| / | Redirect to /dashboard | Protected | Default landing |
| /dashboard | DashboardPage | Protected | Agency overview |
| /inbox | EmailInboxPage | Protected | Email intake and review |
| /enquiries | EnquiriesPage | Protected | Enquiry directory and filters |
| /enquiries/new | AddEnquiryPage | Protected | New enquiry form |
| /enquiries/:id | EnquiryDetailsPage | Protected | Enquiry dossier, registration documents, email and notes |
| /clients | ClientsPage | Protected | Client directory |
| /clients/new | AddClientPage | Protected | New client form |
| /clients/:id | ClientDetailsPage | Protected | Client dossier |
| /weddings | WeddingsPage | Protected | Wedding directory |
| /weddings/:id | WeddingProjectPage | Protected | Wedding project and tabs |
| /settings | SettingsPage | Protected | Settings |
| * | Redirect to /dashboard | Fallback | Unknown paths |

## Query parameters and in-page navigation
- /clients?status=Confirmed: dashboard Active Clients card; ClientsPage reads the status query parameter and selects Confirmed. Reset clears the parameter.
- :id identifies an enquiry, client or wedding in its respective detail route.
- Wedding project tabs are not separate URL routes: Overview; Events & Schedule; Vendors & Quotations; Tasks & Team; Finance; Planning Files.
- WeddingTasksPanel stores demo tasks locally under rk-tasks-<weddingId>; this is not a backend endpoint.

## Backend API routing
Backend entry: backend/app/main.py. API version prefix settings.API_V1_STR (frontend uses /api/v1).

| Module | Prefix | Function |
|---|---|---|
| backend/app/routes/clients.py | /api/v1 | Client endpoints and health |
| backend/app/routes/enquiries.py | /api/v1/enquiries | Enquiry management, notes, documents and registration |
| backend/app/routes/auth.py | /api/v1/auth | Authentication |
| backend/app/routes/emails.py | /api/v1/emails | Email intake and message operations |
| backend/app/main.py | /health and / | Health and root |

Frontend API client: frontend/src/services/api.ts; API_BASE is http://localhost:8000/api/v1. Consult backend route handlers for exact HTTP verbs, subpaths and request schemas.

## Demo enquiries
frontend/src/data/demoEnquiries.ts contains six fictional records DEMO-ENQ-001 through DEMO-ENQ-006. enquiryApi.list combines live and demo entries and applies search, status and source filters. enquiryApi.get resolves demo IDs locally. Demo entries are not stored in the backend; server-dependent actions do not operate on them.

## Navigation files
- frontend/src/App.tsx — route registration and authentication guard
- frontend/src/components/layout/Sidebar.tsx — sidebar navigation
- frontend/src/pages/DashboardPage.tsx — dashboard links
- frontend/src/pages/ClientsPage.tsx — client status query filter
- frontend/src/pages/WeddingProjectPage.tsx — project tabs
- frontend/src/services/api.ts — frontend API requests
- backend/app/routes/ — backend route handlers

This documents implemented navigation, not a guarantee that every prototype workflow has backend persistence.