# Phase 4 implementation handoff

## Scope delivered

- Persistent wedding plan and task records, project-scoped task CRUD and completion timestamps.
- Function guest-count overrides and notes; milestone category, staff assignment and function association.
- Vendor assignments, category budget allocations, expenses, accommodation room blocks and transport logistics with CRUD endpoints.
- Budget summary combining expenses, confirmed non-catering vendor commitments and Phase 3 catering agreed costs.
- Planning activity log for tasks and resource mutations; staff and function selectors in the planning interface.
- A React Planning Command Center linked from the wedding dossier, with editable records and financial summary.
- Four Alembic revisions, `b4f001` through `b4f004`.

## Local preview

- Frontend: http://localhost:5175
- Backend: http://localhost:8000
- API documentation: http://localhost:8000/docs
- Preview uses `backend/phase4_preview.db`, not the original application database.
- Demo project ID: `PHASE4-DEMO-PROJECT` (only in the preview database).

## Validation

- `backend/.venv/Scripts/python.exe -m pytest -q` — 51 tests passed.
- `frontend/npm run build` — TypeScript and Vite build passed; chunk-size warning only.
- Alembic `upgrade head`, downgrade, and re-upgrade passed on a separate SQLite database.
- HTTP health, OpenAPI, CORS, plan creation, task creation, expense creation and budget summary verified on the local preview.

## Important limitations before production

- The inherited authentication design does not provide token-based authorization for API requests. The new endpoints follow the existing app's access model, so a real deployment must add server-side authentication, staff authorization, and actor identity to the audit log.
- The activity log currently records a generic agency actor, not a verified signed-in user.
- The preview has not been verified through a complete interactive browser journey with a real staff account.
- Vendor/staff assignment and financial records need operational acceptance testing with real data and workflow approvals.
- No changes have been merged or pushed to the original project branch.
