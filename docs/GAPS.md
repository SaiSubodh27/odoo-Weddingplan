# The Royal Knot — Gap Analysis (Step 1)

| Item | Requirement | Status | File Path |
|---|---|---|---|
| 1 | Agreement gate (403 AGREEMENT_REQUIRED, OTP hash, PDF SHA-256, /agreement redirect) | Partial | `backend/app/core/dependencies.py`, `backend/app/routes/agreements.py` |
| 2 | Vendor Quotes (RFQ, line items, price/plate, compare, select winner in 1 TX) | Partial | `backend/app/routes/catering.py`, `frontend/src/components/catering/CateringQuotationsSection.tsx` |
| 3 | Deposit -> plan (paid deposit triggers 25+ tasks per tier, 3 payment stages, idempotent) | Partial | `backend/app/services/project_service.py`, `backend/app/models/project.py` |
| 4 | Founder profit (client payments - vendor costs - team cost [hrs x rate]) | Partial | `frontend/src/pages/FounderPortalPage.tsx`, `backend/app/models/project.py` |
| 5 | Big day (live schedule, vendor arrived_at, late flag grace polling 30s, mobile UI) | Missing | `frontend/src/pages/WeddingEventsPanel.tsx`, `backend/app/models/project.py` |
| 6 | Settlement (extras to invoice, vendor payout = agreed + extras - advances, final view) | Missing | `backend/app/models/project.py`, `backend/app/routes/projects.py` |
| 7 | Client wedding overview (read-only: events, tasks, vendors, payments, final costs) | Partial | `frontend/src/pages/ClientPortalPage.tsx`, `backend/app/routes/projects.py` |
| 8 | Founder season view (all weddings, vendor performance, 4-week dues, report export) | Partial | `frontend/src/pages/FounderPortalPage.tsx`, `backend/app/routes/projects.py` |
| 9 | Vendor area (vendor login, requests, submit quote with lines, won/closed, weddings) | Partial | `frontend/src/pages/VendorPortalPage.tsx`, `backend/app/routes/vendors.py` |
| 10 | Catering PDF & WhatsApp share | Done | `backend/app/services/pdf_service.py`, `backend/app/routes/catering.py` |
| 11 | Loading, empty, error states & mobile layout | Partial | `frontend/src/pages/ProjectDetailsPage.tsx`, `frontend/src/pages/ClientPortalPage.tsx` |
