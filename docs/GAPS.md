# The Royal Knot — Gap Analysis & Resolution Matrix

| Item | Requirement | Status | Resolution File Path | Verification |
|---|---|---|---|---|
| 1 | Agreement gate (403 AGREEMENT_REQUIRED, OTP hash, PDF SHA-256, /agreement redirect) | **COMPLETED** | `backend/app/core/dependencies.py`, `backend/app/routes/service_agreements.py`, `backend/app/services/agreement_service.py` | 37/37 tests passing |
| 2 | Vendor Quotes (RFQ, line items, price/plate, compare, select winner in 1 TX) | **COMPLETED** | `backend/app/routes/catering.py`, `backend/app/services/catering_service.py`, `frontend/src/components/catering/CateringQuotationsSection.tsx` | 4/4 tests passing |
| 3 | Deposit -> plan (paid deposit triggers 25+ tasks per tier, 3 payment stages, idempotent) | **COMPLETED** | `backend/app/services/project_service.py`, `backend/app/models/project.py`, `backend/app/routes/projects.py` | 2/2 tests passing |
| 4 | Founder profit (client payments - vendor costs - team cost [hrs x rate]) | **COMPLETED** | `backend/app/services/project_service.py`, `backend/app/routes/projects.py`, `frontend/src/pages/FounderPortalPage.tsx` | 1/1 test passing (hand-calculated) |
| 5 | Big day (live schedule, vendor arrived_at, late flag grace polling 30s, mobile UI) | **COMPLETED** | `backend/app/routes/projects.py`, `frontend/src/pages/BigDayLivePage.tsx`, `docs/screenshots/mobile-big-day.png` | 1/1 test passing + screenshot |
| 6 | Settlement (extras to invoice, vendor payout = agreed + extras - advances, final view) | **COMPLETED** | `backend/app/models/project.py`, `backend/app/services/project_service.py`, `backend/app/routes/projects.py` | 2/2 tests passing |
| 7 | Client wedding overview (read-only: events, tasks, vendors, payments, final costs) | **COMPLETED** | `backend/app/routes/projects.py`, `frontend/src/pages/ClientPortalPage.tsx` | 1/1 test passing + screenshot |
| 8 | Founder season view (all weddings, vendor performance, 4-week dues, report export) | **COMPLETED** | `backend/app/routes/founder.py`, `frontend/src/pages/FounderPortalPage.tsx`, `docs/screenshots/founder-season.png` | 3/3 tests passing + screenshot |
| 9 | Vendor area (vendor login, requests, submit quote with lines, won/closed, weddings) | **COMPLETED** | `backend/app/routes/vendor_portal.py`, `frontend/src/pages/VendorPortalPage.tsx`, `docs/screenshots/vendor-portal.png` | 3/3 tests passing + screenshot |
| 10 | Catering PDF & WhatsApp share | **COMPLETED** | `backend/app/services/pdf_service.py`, `backend/app/routes/catering.py`, `frontend/src/components/catering/WhatsAppShareModal.tsx` | %PDF- verified + wa.me tested |
| 11 | Loading, empty, error states & mobile layout | **COMPLETED** | `frontend/src/pages/ProjectDetailsPage.tsx`, `frontend/src/pages/ClientPortalPage.tsx`, `frontend/src/pages/BigDayLivePage.tsx` | Verified via Playwright screenshots |
