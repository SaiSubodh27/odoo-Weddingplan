# Phase 4: Wedding Plan Management — System Architecture & Implementation Blueprint

> **System:** The Royal Knot — Luxury Wedding Planning Management System  
> **Operations:** Jaipur & Udaipur Heritage Destination Weddings (25 Luxury Weddings / Season)  
> **Phase:** Phase 4 — Wedding Plan Management  
> **Author:** Lead Full-Stack Architect  
> **Branch:** `phase-4`  
> **Status:** Stage 1 — Discovery & Design Completed (Architecture & API Blueprint)  

---

## 1. Executive Summary & Objective

**The Royal Knot** manages high-value destination weddings spanning palatial venues across Jaipur (e.g., Rambagh Palace, Samode Palace, Jai Mahal) and Udaipur (e.g., The Leela Palace, Taj Lake Palace, Jagmandir Island). Each wedding spans 3 to 4 days, accommodates 350 to 500+ distinguished guests, engages 15 to 20+ specialized luxury vendors, and commands a multi-crore budget (₹1.5 Cr to ₹5.0+ Cr).

### Phase 4 Core Purpose
Phase 4 elevates the existing **Wedding Project** module into a unified, operational **Wedding Plan Management Area**. Rather than storing scattered spreadsheets or detached notes, the wedding planning team will operate from a single, centralized command center that connects:
1. **Wedding Project & Client Dossier:** High-level project metadata, dates, couple information, and master guest count.
2. **Event Schedule & Function Planning:** Multi-day ceremony breakdown (Mehendi, Haldi, Sangeet, Pheras, Reception) with event-specific guest count overrides and venues.
3. **Wedding Tasks & Checklists:** Granular operational task tracker categorized across 14 planning areas with assignments, priorities, deadlines, and event linkages.
4. **Timeline & Milestones:** Key milestone checkpoints with accountability and completion tracking.
5. **Vendor Coordination:** Non-catering and multi-disciplinary vendor coordination (Decor, Photography, Videography, Entertainment, Production, Makeup, Logistics) linked to existing `Vendor` records, without replacing or duplicating Phase 3 Catering Management.
6. **Budget & Cost Tracking:** Multi-tier budget breakdown reconciling estimated budgets, allocated category budgets, confirmed vendor commitments (including Phase 3 catering agreed costs), and actual recorded expenses.
7. **Guest Accommodation Planning:** Hotel room blocks, room categories, check-in/out schedules, and confirmation tracking.
8. **Transportation & Logistics Planning:** Fleet coordination, airport/railway transfers, guest shuttles, driver assignments, and vehicle counts.
9. **Staff Assignments & Auditability:** Role-based delegation across agency coordinators and planners using existing authentication.

---

## 2. Stage 1: Discovery & Codebase Inspection

### 2.1 Working Directory, Git Branch & Working-Tree Inspection
- **Current Directory:** `c:\Users\saisu\OneDrive\Desktop\odoo-Weddingplan`
- **Active Git Branch:** `phase-4` (created from `feature/phase-3-wedding-project-management` at commit `2cecad4`)
- **Remote Configuration:** `origin https://github.com/SaiSubodh27/odoo-Weddingplan.git`
- **Working-Tree Status:**
  - Preserved uncommitted changes:
    - Route documentation: `ROUTES_AND_ENDPOINTS.md`, `ROUTING.md`
    - Frontend UI prototypes & assets from teammate `front_end(j07)`: `FounderPortalPage.tsx`, `VendorPortalPage.tsx`, `VendorBookingCrew.tsx`, `VendorBookingWorkspace.tsx`, `VendorCrewManager.tsx`, `VendorCrewWorkload.tsx`, `VendorDirectoryPage.tsx`, `WeddingEventsPanel.tsx`, `WeddingTasksPanel.tsx`, `WeddingProjectPage.tsx`, `LoginPage.tsx`, `DashboardPage.tsx`, `palace-backdrop.png`
    - Modified index/layout files: `frontend/index.html`, `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/src/services/api.ts`
  - All existing working-tree modifications have been identified, respected, and preserved without overwriting or reverting.

### 2.2 Backend Architecture Review
- **Framework:** FastAPI (Python 3.11) with Uvicorn ASGI runner.
- **ORM & Database:** SQLAlchemy 2.0 with PostgreSQL in production and SQLite (`test_royal_knot.db` / `royal_knot.db`) in local development and automated testing.
- **Migrations:** Alembic managing database evolution (`backend/alembic/versions/`).
- **Existing Models:**
  - `Client` (`backend/app/models/client.py`): Client dossier, couple names, contact details, wedding date/location, estimated budget, status (`Enquiry`, `Confirmed`).
  - `Enquiry` (`backend/app/models/enquiry.py`): Incoming lead pipeline with Gmail sync and document tracking.
  - `UserAccount` & `ActivationToken` (`backend/app/models/user.py`): Agency staff and client portal accounts with Argon2 password hashing.
  - `WeddingProject` (`backend/app/models/project.py`): 1:1 linked to confirmed client dossier; contains project code (e.g. `PRJ-2026-001`), wedding date, master guest count, estimated budget, package tier, project manager, status (`Planning`, `In Progress`, `On Hold`, `Completed`, `Cancelled`), soft delete flag.
  - `WeddingFunction` (`backend/app/models/project.py`): Ceremonies linked to project (`function_name`, `function_date`, `start_time`, `end_time`, `venue`, `description`, `status`, `estimated_cost`).
  - `ProjectMilestone` (`backend/app/models/project.py`): Project milestone checkpoints (`milestone_name`, `due_date`, `status`, `completed_at`).
  - `ProjectStatusHistory` (`backend/app/models/project.py`): Audit trail of project status transitions.
  - `Vendor` (`backend/app/models/vendor.py`): Central directory of palace vendors, caterers, decorators (`name`, `category`, `contact_person`, `phone`, `email`, `city`, `rating`, `is_active`).
  - `CateringPlan`, `CateringMenuItem`, `CateringQuotation`, `CateringCommunicationLog` (`backend/app/models/catering.py`): Phase 3 comprehensive catering module.
- **Existing Services & Routers:**
  - `project_service` & `projects_router` mounted at `/api/v1/projects`
  - `vendor_service` & `vendors_router` mounted at `/api/v1/vendors`
  - `catering_service` & `catering_router` mounted at `/api/v1` (with `/api/v1/catering` and `/api/v1/projects/{project_id}/...`)
  - `clients_router` mounted at `/api/v1/clients`
  - `enquiries_router` mounted at `/api/v1/enquiries`
  - `auth_router` mounted at `/api/v1/auth`
  - `emails_router` mounted at `/api/v1/emails`

### 2.3 Frontend Architecture Review
- **Framework:** React 19 + TypeScript + Vite.
- **Styling:** Tailwind CSS + custom heritage luxury theme variables.
- **Icons:** `lucide-react`.
- **Existing Pages & Views:**
  - `ProjectsPage.tsx`: Listing of all active wedding projects with search, filter, and milestone progress bars.
  - `ProjectDetailsPage.tsx`: Full-featured tabbed dossier connecting to `/api/v1/projects/{id}` with Overview, Functions, Catering, Milestones, and History tabs.
  - `CreateProjectModal.tsx`: Modal for setting up new projects from confirmed client bookings.
  - `VendorsPage.tsx`: Central vendor directory management.
  - `WeddingProjectPage.tsx` / `WeddingEventsPanel.tsx` / `WeddingTasksPanel.tsx`: Frontend prototype views using `localStorage`. Phase 4 will elevate these into backend-persisted, production-grade workflows.
- **API Client:** `frontend/src/services/api.ts` provides strongly-typed API wrappers (`projectApi`, `cateringApi`, `vendorApi`, `clientApi`, etc.).

### 2.4 Existing vs. Missing Features Matrix

| Feature Area | Existing State in Codebase | Missing for Phase 4 | Proposed Phase 4 Architecture |
|---|---|---|---|
| **Wedding Plan Entity** | `WeddingProject` exists with high-level fields. No dedicated operational plan entity. | Operational planning container (`WeddingPlan`), tracking planning dates, planning status, team leader, and overall progress. | Introduce `WeddingPlan` model 1:1 linked to `WeddingProject`. Auto-initialized when project is created or on first plan access. |
| **Event Planning** | `WeddingFunction` stores name, date, timings, venue, status, estimated cost. | Function-level guest count override (distinct from master project guest count) and event notes. | Extend `WeddingFunction` with `guest_count` (nullable, defaulting to project guest count) and `notes`. |
| **Tasks & Checklist** | Mock local storage tasks in `WeddingTasksPanel.tsx`. No backend model or API. | Complete backend task management: categories, priorities, due dates, statuses, assigned staff, function association, notes. | Create `WeddingPlanTask` model, schema, service, and REST API. |
| **Timeline & Milestones** | `ProjectMilestone` exists with name, due date, status, completion date. | Milestone assignment to responsible staff, milestone category, and event association. | Enhance milestone schema/model with `assigned_to` and optional `function_id`. |
| **Vendor Coordination** | Central `Vendor` directory exists. Catering links vendors to catering plans via quotations. | Non-catering vendor assignments to wedding projects/functions with service categories, contract amounts, confirmation status, and responsibilities. | Create `WeddingPlanVendorAssignment` model linking existing `vendors`, `wedding_projects`, and `wedding_functions`. |
| **Budget Planning** | Project has `estimated_budget`. Functions have `estimated_cost`. Catering has quotations & agreed costs. | Unified budget allocation by category (Decor, Venue, Catering, Entertainment, etc.), expense tracking, and variance reconciliation without double counting. | Create `WeddingBudgetAllocation` and `WeddingExpense` models, with auto-aggregation service summing catering commitments and vendor contracts. |
| **Accommodation** | Client dossier stores rough location; no room block tracking. | Hotel property blocks, room counts, room types, check-in/out dates, rates, confirmation status, and vouchers. | Create `WeddingPlanAccommodation` model and planning section. |
| **Logistics & Transport** | No logistics tracking exists in backend. | Vehicle requirements, pickup/drop locations, airport transfers, ceremony shuttles, driver info, and schedules. | Create `WeddingPlanLogistics` model and logistics tracker. |
| **Staff Assignments** | `UserAccount` exists in `user_accounts` table. `project_manager_name` stored as string. | Linking tasks, milestones, and planning areas to real staff user records or standard agency roles. | Use existing `UserAccount` IDs and names for assigned planners. |

---

## 3. Database Schema & Data Models

### 3.1 Entity Relationship Overview

```
+-------------------------------------------------------------+
|                     wedding_projects                        |
|  id (PK)                                                    |
|  project_code, client_id (FK -> clients.id)                 |
|  project_name, wedding_date, location                       |
|  guest_count (Master), estimated_budget, status             |
+------------------------------+------------------------------+
                               | 1:1
                               v
+-------------------------------------------------------------+
|                      wedding_plans                          |
|  id (PK: WP-YYYY-XXX)                                       |
|  project_id (FK -> wedding_projects.id, UNIQUE)             |
|  title, planning_start_date, target_completion_date         |
|  status: Draft | Planning | In Progress | Ready | Completed |
|  progress_percentage, notes, assigned_lead_id/name          |
|  created_by, created_at, updated_at                         |
+-----+--------------+--------------+--------------+----------+
      |              |              |              |
      | 1:N          | 1:N          | 1:N          | 1:N
      v              v              v              v
+-------------+ +-------------+ +-------------+ +-------------+
| plan_tasks  | | vendor_asgns| |accommodatns | |  logistics  |
+-------------+ +-------------+ +-------------+ +-------------+
      |              |              |              |
      | 1:N          | 1:N          | 1:N          | 1:N
+-----+--------------+--------------+--------------+----------+
|                 budget_allocations / expenses               |
+-------------------------------------------------------------+
```

### 3.2 Detailed Model Specifications

#### A. `wedding_plans`
The core operational planning entity for each wedding project.
- `id` `VARCHAR(50)` PRIMARY KEY (e.g. `WP-2026-001` or UUID)
- `project_id` `VARCHAR(50)` UNIQUE NOT NULL, REFERENCES `wedding_projects(id)` ON DELETE CASCADE
- `title` `VARCHAR(255)` NOT NULL (e.g. "Royal Heritage Wedding Operational Plan")
- `planning_start_date` `DATE` NOT NULL
- `target_completion_date` `DATE` NULLABLE
- `status` `VARCHAR(50)` NOT NULL DEFAULT `'Planning'` (`Draft`, `Planning`, `In Progress`, `Ready for Execution`, `Completed`, `Cancelled`)
- `overall_progress` `NUMERIC(5, 2)` NOT NULL DEFAULT `0.00` (Calculated percentage of completed tasks & milestones)
- `notes` `TEXT` NULLABLE
- `assigned_lead_planner` `VARCHAR(100)` NOT NULL DEFAULT `'Maharani Gayatri Singh'`
- `created_by` `VARCHAR(100)` NOT NULL DEFAULT `'Agency Staff'`
- `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`
- `updated_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`

#### B. `wedding_functions` (Enhanced via Migration)
Reusing existing Phase 3 `wedding_functions` table and adding operational event fields:
- `guest_count` `INTEGER` NULLABLE (Event-specific override; defaults to `wedding_projects.guest_count` in API if null)
- `notes` `TEXT` NULLABLE (Event run-of-show or ceremony notes)

#### C. `wedding_plan_tasks`
Granular task management for wedding operations.
- `id` `VARCHAR(50)` PRIMARY KEY (e.g. `TSK-XXXXXX`)
- `plan_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_plans(id)` ON DELETE CASCADE
- `project_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_projects(id)` ON DELETE CASCADE
- `title` `VARCHAR(255)` NOT NULL
- `description` `TEXT` NULLABLE
- `category` `VARCHAR(50)` NOT NULL (`Venue`, `Decor`, `Catering`, `Guest Management`, `Accommodation`, `Transportation`, `Entertainment`, `Photography`, `Videography`, `Wedding Ceremony`, `Logistics`, `Client Coordination`, `Budget`, `Other`)
- `assigned_to` `VARCHAR(100)` NOT NULL DEFAULT `'Unassigned'`
- `priority` `VARCHAR(20)` NOT NULL DEFAULT `'Medium'` (`Low`, `Medium`, `High`, `Urgent`)
- `due_date` `DATE` NOT NULL
- `status` `VARCHAR(30)` NOT NULL DEFAULT `'Not Started'` (`Not Started`, `In Progress`, `Waiting`, `Completed`, `Cancelled`)
- `function_id` `VARCHAR(50)` NULLABLE, REFERENCES `wedding_functions(id)` ON DELETE SET NULL
- `completed_at` `TIMESTAMP WITH TIME ZONE` NULLABLE
- `notes` `TEXT` NULLABLE
- `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`
- `updated_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`
- *Indexes:* `ix_tasks_plan_id`, `ix_tasks_project_id`, `ix_tasks_status`, `ix_tasks_due_date`, `ix_tasks_category`

#### D. `project_milestones` (Enhanced via Migration)
Reusing existing `project_milestones` table and adding:
- `assigned_to` `VARCHAR(100)` NULLABLE (Responsible planner/lead)
- `function_id` `VARCHAR(50)` NULLABLE, REFERENCES `wedding_functions(id)` ON DELETE SET NULL
- `category` `VARCHAR(50)` NULLABLE DEFAULT `'General'`

#### E. `wedding_plan_vendor_assignments`
Coordinates non-catering and multi-vendor commitments across wedding ceremonies without duplicating Phase 3 catering quotations.
- `id` `VARCHAR(50)` PRIMARY KEY (e.g. `VAS-XXXXXX`)
- `plan_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_plans(id)` ON DELETE CASCADE
- `project_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_projects(id)` ON DELETE CASCADE
- `vendor_id` `VARCHAR(50)` NOT NULL, REFERENCES `vendors(id)` ON DELETE RESTRICT
- `function_id` `VARCHAR(50)` NULLABLE, REFERENCES `wedding_functions(id)` ON DELETE SET NULL
- `service_category` `VARCHAR(50)` NOT NULL (`Decor`, `Photography`, `Videography`, `Entertainment`, `Floral`, `Sound & Light`, `Makeup`, `Production`, `Invitations`, `Mehendi Artists`, `Other`)
- `contracted_amount` `NUMERIC(15, 2)` NOT NULL DEFAULT `0.00`
- `assigned_responsibilities` `TEXT` NULLABLE
- `service_date` `DATE` NULLABLE
- `confirmation_status` `VARCHAR(30)` NOT NULL DEFAULT `'Shortlisted'` (`Shortlisted`, `Quoted`, `Contracted`, `Confirmed`, `Completed`, `Cancelled`)
- `notes` `TEXT` NULLABLE
- `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`
- `updated_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`
- *Indexes:* `ix_vendor_asgns_plan_id`, `ix_vendor_asgns_vendor_id`, `ix_vendor_asgns_function_id`

#### F. `wedding_budget_allocations` & `wedding_expenses`
Prevents double-counting and provides a unified financial view.
- `wedding_budget_allocations`:
  - `id` `VARCHAR(50)` PRIMARY KEY
  - `plan_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_plans(id)` ON DELETE CASCADE
  - `project_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_projects(id)` ON DELETE CASCADE
  - `category` `VARCHAR(50)` NOT NULL (`Venue`, `Catering`, `Decor`, `Entertainment`, `Photography & Videography`, `Accommodation`, `Transportation`, `Wedding Production`, `Miscellaneous`)
  - `allocated_amount` `NUMERIC(15, 2)` NOT NULL DEFAULT `0.00`
  - `notes` `TEXT` NULLABLE
  - `updated_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`
  - *Unique Constraint:* `UNIQUE(plan_id, category)`
- `wedding_expenses`:
  - `id` `VARCHAR(50)` PRIMARY KEY
  - `plan_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_plans(id)` ON DELETE CASCADE
  - `project_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_projects(id)` ON DELETE CASCADE
  - `title` `VARCHAR(255)` NOT NULL
  - `category` `VARCHAR(50)` NOT NULL
  - `amount` `NUMERIC(15, 2)` NOT NULL
  - `payment_date` `DATE` NOT NULL
  - `paid_to` `VARCHAR(150)` NULLABLE
  - `payment_method` `VARCHAR(50)` NOT NULL DEFAULT `'Bank Transfer'`
  - `reference_number` `VARCHAR(100)` NULLABLE
  - `function_id` `VARCHAR(50)` NULLABLE, REFERENCES `wedding_functions(id)` ON DELETE SET NULL
  - `vendor_id` `VARCHAR(50)` NULLABLE, REFERENCES `vendors(id)` ON DELETE SET NULL
  - `notes` `TEXT` NULLABLE
  - `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`

#### G. `wedding_plan_accommodations`
Guest accommodation tracking across palatial hotels and resorts.
- `id` `VARCHAR(50)` PRIMARY KEY (e.g. `ACC-XXXXXX`)
- `plan_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_plans(id)` ON DELETE CASCADE
- `project_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_projects(id)` ON DELETE CASCADE
- `hotel_name` `VARCHAR(255)` NOT NULL (e.g. "The Oberoi Udaivilas, Udaipur")
- `room_type` `VARCHAR(100)` NOT NULL DEFAULT `'Deluxe Palace Room'` (e.g. "Premier Lake View Room", "Kohinoor Suite")
- `number_of_rooms` `INTEGER` NOT NULL DEFAULT `1`
- `guest_capacity` `INTEGER` NOT NULL DEFAULT `2`
- `check_in_date` `DATE` NOT NULL
- `check_out_date` `DATE` NOT NULL
- `estimated_room_rate` `NUMERIC(15, 2)` NOT NULL DEFAULT `0.00`
- `total_cost` `NUMERIC(15, 2)` NOT NULL DEFAULT `0.00`
- `booking_reference` `VARCHAR(100)` NULLABLE
- `contact_person` `VARCHAR(100)` NULLABLE
- `contact_phone` `VARCHAR(50)` NULLABLE
- `confirmation_status` `VARCHAR(30)` NOT NULL DEFAULT `'Requested'` (`Requested`, `Blocked`, `Confirmed`, `Checked-In`, `Completed`, `Cancelled`)
- `notes` `TEXT` NULLABLE
- `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`
- `updated_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`

#### H. `wedding_plan_logistics`
Transportation and logistics planning for guests, VIPs, and bridal parties.
- `id` `VARCHAR(50)` PRIMARY KEY (e.g. `LOG-XXXXXX`)
- `plan_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_plans(id)` ON DELETE CASCADE
- `project_id` `VARCHAR(50)` NOT NULL, REFERENCES `wedding_projects(id)` ON DELETE CASCADE
- `title` `VARCHAR(255)` NOT NULL (e.g. "Airport Pickup Cavalcade — Singhania Family")
- `vehicle_type` `VARCHAR(100)` NOT NULL DEFAULT `'Luxury Sedan'` (e.g. "Mercedes E-Class", "Toyota Innova Crysta", "35-Seater Luxury Coach", "Vintage Royal Procession Car")
- `vehicle_count` `INTEGER` NOT NULL DEFAULT `1`
- `pickup_location` `VARCHAR(255)` NOT NULL
- `drop_location` `VARCHAR(255)` NOT NULL
- `transfer_datetime` `TIMESTAMP WITH TIME ZONE` NOT NULL
- `function_id` `VARCHAR(50)` NULLABLE, REFERENCES `wedding_functions(id)` ON DELETE SET NULL
- `vendor_id` `VARCHAR(50)` NULLABLE, REFERENCES `vendors(id)` ON DELETE SET NULL
- `assigned_driver_contact` `VARCHAR(150)` NULLABLE
- `estimated_cost` `NUMERIC(15, 2)` NOT NULL DEFAULT `0.00`
- `status` `VARCHAR(30)` NOT NULL DEFAULT `'Planned'` (`Planned`, `Booked`, `Dispatched`, `Completed`, `Cancelled`)
- `notes` `TEXT` NULLABLE
- `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`
- `updated_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `NOW()`

---

## 4. REST API Endpoint Specification

All endpoints are prefixed with `/api/v1`. Authentication uses the existing Bearer token / agency staff session guard.

### 4.1 Wedding Plan Core Endpoints

#### 1. `GET /api/v1/projects/{project_id}/plan`
- **Purpose:** Retrieve the full operational wedding plan for a project. If no plan exists yet, the service auto-initializes a plan using project metadata.
- **Path Parameters:** `project_id: str`
- **Response `200 OK`:** `WeddingPlanDetailResponse`
```json
{
  "id": "WP-2026-001",
  "projectId": "PRJ-2026-001",
  "title": "Royal Heritage Celebration Plan — Aanya & Kabir",
  "planningStartDate": "2026-10-15",
  "targetCompletionDate": "2026-12-15",
  "status": "In Progress",
  "overallProgress": 64.5,
  "notes": "VIP destination wedding at Lake Pichola.",
  "assignedLeadPlanner": "Maharani Gayatri Singh",
  "createdAt": "2026-10-31T18:00:00Z",
  "updatedAt": "2026-11-01T02:00:00Z",
  "project": {
    "projectCode": "PRJ-2026-001",
    "projectName": "The Oberoi & Singhania Royal Lake Wedding",
    "weddingDate": "2026-12-18",
    "location": "The Leela Palace, Udaipur",
    "guestCount": 350,
    "estimatedBudget": 15000000.00,
    "coupleName": "Aanya Singhania & Kabir Oberoi",
    "status": "Planning"
  },
  "metrics": {
    "totalTasks": 28,
    "completedTasks": 18,
    "overdueTasks": 2,
    "totalMilestones": 6,
    "completedMilestones": 4,
    "totalEvents": 4,
    "allocatedBudget": 14200000.00,
    "confirmedCost": 9850000.00,
    "actualExpenses": 3200000.00,
    "vendorsEngaged": 8,
    "roomsBlocked": 45,
    "vehiclesScheduled": 12
  }
}
```

#### 2. `POST /api/v1/projects/{project_id}/plan`
- **Purpose:** Explicitly create an operational wedding plan for a project if not auto-initialized.
- **Request Body:** `WeddingPlanCreate`
```json
{
  "title": "Imperial Rajputana Wedding Plan",
  "planningStartDate": "2026-10-20",
  "targetCompletionDate": "2026-12-10",
  "assignedLeadPlanner": "Gayatri Devi",
  "notes": "Exclusive 3-day royal buyout."
}
```
- **Response `201 Created`:** `WeddingPlanDetailResponse`

#### 3. `PUT /api/v1/plans/{plan_id}`
- **Purpose:** Update wedding plan metadata, target dates, notes, or assigned planner.
- **Path Parameters:** `plan_id: str`
- **Request Body:** `WeddingPlanUpdate`
```json
{
  "title": "Updated Royal Heritage Plan",
  "targetCompletionDate": "2026-12-12",
  "assignedLeadPlanner": "Devraj Singh",
  "notes": "Updated guest arrival timings."
}
```
- **Response `200 OK`:** `WeddingPlanDetailResponse`

#### 4. `PATCH /api/v1/plans/{plan_id}/status`
- **Purpose:** Update the plan lifecycle status (`Draft`, `Planning`, `In Progress`, `Ready for Execution`, `Completed`, `Cancelled`). Does not automatically close the parent project.
- **Request Body:** `WeddingPlanStatusUpdate`
```json
{
  "status": "Ready for Execution",
  "notes": "All vendor contracts signed, menu finalized, and room blocks confirmed."
}
```
- **Response `200 OK`:** `WeddingPlanDetailResponse`

---

### 4.2 Section A: Wedding Overview & Progress

#### 5. `GET /api/v1/plans/{plan_id}/overview`
- **Purpose:** Consolidated planning dashboard metrics combining project, client, budget, task, and vendor data.
- **Response `200 OK`:** `WeddingPlanOverviewResponse`
```json
{
  "planId": "WP-2026-001",
  "weddingName": "The Oberoi & Singhania Royal Lake Wedding",
  "coupleName": "Aanya Singhania & Kabir Oberoi",
  "clientContact": {
    "email": "aanya.oberoi@example.com",
    "phone": "+91 98201 12345"
  },
  "weddingDateRange": {
    "startDate": "2026-12-17",
    "endDate": "2026-12-18",
    "durationDays": 2
  },
  "venue": "The Leela Palace, Udaipur",
  "masterGuestCount": 350,
  "eventsCount": 4,
  "budgetSummary": {
    "estimatedBudget": 15000000.00,
    "allocatedBudget": 14200000.00,
    "confirmedCost": 9850000.00,
    "actualExpenses": 3200000.00,
    "remainingBudget": 5150000.00
  },
  "planningProgress": 64.5,
  "tasksSummary": {
    "total": 28,
    "completed": 18,
    "inProgress": 6,
    "waiting": 2,
    "overdue": 2
  },
  "upcomingDeadlines": [
    {
      "type": "Task",
      "id": "TSK-0012",
      "title": "Finalize Mandap Floral Rigging",
      "dueDate": "2026-11-05",
      "priority": "Urgent",
      "assignedTo": "Devraj Singh"
    }
  ],
  "planStatus": "In Progress"
}
```

---

### 4.3 Section B: Event Planning & Function Overrides

#### 6. `GET /api/v1/plans/{plan_id}/events`
- **Purpose:** List all ceremonies/events for the wedding with effective guest counts (override or project fallback).
- **Response `200 OK`:** `List[WeddingPlanEventResponse]`
```json
[
  {
    "id": "func-001",
    "eventName": "Mehendi & Welcome Lunch",
    "eventDate": "2026-12-17",
    "startTime": "11:30",
    "endTime": "16:00",
    "venue": "The Guava Garden, The Leela Palace",
    "guestCount": 200,
    "isGuestCountOverridden": true,
    "masterGuestCount": 350,
    "description": "Live bangle making counters, traditional ghoomar troupe.",
    "status": "Scheduled",
    "estimatedCost": 350000.00,
    "cateringStatus": "Menu Finalized"
  }
]
```

#### 7. `POST /api/v1/plans/{plan_id}/events`
- **Purpose:** Add a new ceremony to the wedding plan.
- **Request Body:** `WeddingPlanEventCreate`
```json
{
  "eventName": "Sangeet After-Party",
  "eventDate": "2026-12-17",
  "startTime": "23:30",
  "endTime": "04:00",
  "venue": "Sheesh Mahal Courtyard",
  "guestCount": 120,
  "description": "Late-night electro-folk DJ set and cocktail atelier.",
  "estimatedCost": 250000.00
}
```
- **Response `201 Created`:** `WeddingPlanEventResponse`

#### 8. `PUT /api/v1/plans/{plan_id}/events/{event_id}`
- **Purpose:** Update event details, including event guest count override and notes. Changing event guest count does not alter project master guest count.
- **Request Body:** `WeddingPlanEventUpdate`
```json
{
  "guestCount": 220,
  "venue": "The Guava Garden & Inner Courtyard",
  "notes": "Added 20 extra guests for bride's extended family."
}
```
- **Response `200 OK`:** `WeddingPlanEventResponse`

---

### 4.4 Section C: Planning Tasks & Checklist

#### 9. `GET /api/v1/plans/{plan_id}/tasks`
- **Purpose:** List planning tasks with filtering and sorting.
- **Query Parameters:**
  - `status: Optional[str]` (`Not Started`, `In Progress`, `Waiting`, `Completed`, `Cancelled`)
  - `category: Optional[str]` (e.g. `Decor`, `Catering`, `Venue`)
  - `priority: Optional[str]` (`Low`, `Medium`, `High`, `Urgent`)
  - `assigned_to: Optional[str]`
  - `function_id: Optional[str]`
  - `is_overdue: Optional[bool]`
- **Response `200 OK`:** `List[WeddingPlanTaskResponse]`

#### 10. `POST /api/v1/plans/{plan_id}/tasks`
- **Purpose:** Create a new planning task.
- **Request Body:** `WeddingPlanTaskCreate`
```json
{
  "title": "Review 3D Mandap Floral Blueprint",
  "description": "Verify structural stability of floating lotus mandap over Lake Pichola with Mewar engineering.",
  "category": "Decor",
  "assignedTo": "Devraj Singh",
  "priority": "High",
  "dueDate": "2026-11-10",
  "functionId": "func-004",
  "notes": "Requires structural engineer approval."
}
```
- **Response `201 Created`:** `WeddingPlanTaskResponse`

#### 11. `PUT /api/v1/plans/{plan_id}/tasks/{task_id}`
- **Purpose:** Update task details, assignee, category, priority, or due date.
- **Request Body:** `WeddingPlanTaskUpdate`
- **Response `200 OK`:** `WeddingPlanTaskResponse`

#### 12. `PATCH /api/v1/plans/{plan_id}/tasks/{task_id}/status`
- **Purpose:** Fast status toggle (e.g. checkbox completion). Auto-records `completed_at` timestamp.
- **Request Body:** `TaskStatusUpdate`
```json
{
  "status": "Completed"
}
```
- **Response `200 OK`:** `WeddingPlanTaskResponse`

#### 13. `DELETE /api/v1/plans/{plan_id}/tasks/{task_id}`
- **Purpose:** Remove a task.
- **Response `200 OK`:** `{ "success": true, "message": "Task TSK-0012 removed." }`

---

### 4.5 Section D: Wedding Timeline & Milestones

#### 14. `GET /api/v1/plans/{plan_id}/milestones`
- **Purpose:** Retrieve full wedding milestone timeline with status flags (overdue, upcoming, completed).
- **Response `200 OK`:** `List[WeddingPlanMilestoneResponse]`
```json
[
  {
    "id": "ms-001",
    "milestoneName": "Palace Venue Buyout Contract Confirmed",
    "description": "Full contract and deposit for The Leela Palace.",
    "dueDate": "2026-10-30",
    "status": "Completed",
    "completedAt": "2026-10-28T14:30:00Z",
    "responsiblePerson": "Maharani Gayatri Singh",
    "functionId": null,
    "isOverdue": false
  }
]
```

#### 15. `POST /api/v1/plans/{plan_id}/milestones`
- **Purpose:** Add a timeline milestone checkpoint.
- **Request Body:** `WeddingPlanMilestoneCreate`
- **Response `201 Created`:** `WeddingPlanMilestoneResponse`

#### 16. `PUT /api/v1/plans/{plan_id}/milestones/{milestone_id}`
- **Purpose:** Update milestone details or status.
- **Request Body:** `WeddingPlanMilestoneUpdate`
- **Response `200 OK`:** `WeddingPlanMilestoneResponse`

#### 17. `DELETE /api/v1/plans/{plan_id}/milestones/{milestone_id}`
- **Purpose:** Delete a milestone checkpoint.
- **Response `200 OK`:** `{ "success": true, "message": "Milestone deleted." }`

---

### 4.6 Section E: Vendor Coordination

#### 18. `GET /api/v1/plans/{plan_id}/vendors`
- **Purpose:** List all vendor assignments for the wedding plan across all categories. Connects to existing `Vendor` records and Phase 3 catering statuses.
- **Query Parameters:** `category: Optional[str]`, `status: Optional[str]`
- **Response `200 OK`:** `List[WeddingPlanVendorAssignmentResponse]`
```json
[
  {
    "id": "VAS-001",
    "vendorId": "VND-002",
    "vendorName": "Royal Mewar Decorators",
    "serviceCategory": "Decor",
    "functionId": "func-002",
    "eventName": "Royal Sangeet & Cocktail Soiree",
    "assignedResponsibilities": "360-degree LED visual stage, royal canopy, and floral chandeliers.",
    "contractedAmount": 1850000.00,
    "confirmationStatus": "Confirmed",
    "contactPerson": "Vikram Rathore",
    "phone": "+91 98290 11223",
    "email": "vikram@royalmewardecor.com",
    "notes": "Advance payment of 50% paid."
  }
]
```

#### 19. `POST /api/v1/plans/{plan_id}/vendors`
- **Purpose:** Associate an existing registered vendor with the wedding plan and/or specific event.
- **Request Body:** `WeddingPlanVendorAssignmentCreate`
```json
{
  "vendorId": "VND-005",
  "serviceCategory": "Photography",
  "functionId": "func-004",
  "assignedResponsibilities": "Lead bridal portraits, drone aerial coverage, same-day teaser edit.",
  "serviceDate": "2026-12-18",
  "contractedAmount": 450000.00,
  "confirmationStatus": "Contracted",
  "notes": "Crew of 6 operators required."
}
```
- **Response `201 Created`:** `WeddingPlanVendorAssignmentResponse`

#### 20. `PUT /api/v1/plans/{plan_id}/vendors/{assignment_id}`
- **Purpose:** Update vendor assignment terms, responsibilities, or contract amount.
- **Request Body:** `WeddingPlanVendorAssignmentUpdate`
- **Response `200 OK`:** `WeddingPlanVendorAssignmentResponse`

#### 21. `PATCH /api/v1/plans/{plan_id}/vendors/{assignment_id}/status`
- **Purpose:** Update vendor confirmation status (`Shortlisted`, `Quoted`, `Contracted`, `Confirmed`, `Completed`, `Cancelled`).
- **Request Body:** `VendorAssignmentStatusUpdate`
- **Response `200 OK`:** `WeddingPlanVendorAssignmentResponse`

#### 22. `DELETE /api/v1/plans/{plan_id}/vendors/{assignment_id}`
- **Purpose:** Remove vendor assignment from the plan (does not delete the master vendor record).
- **Response `200 OK`:** `{ "success": true, "message": "Vendor assignment removed." }`

---

### 4.7 Section F: Budget & Expense Planning

#### 23. `GET /api/v1/plans/{plan_id}/budget`
- **Purpose:** Retrieve comprehensive category-wise budget breakdown reconciling estimates, category allocations, confirmed vendor commitments (including Phase 3 catering agreed costs), and actual recorded expenses without double counting.
- **Response `200 OK`:** `WeddingBudgetOverviewResponse`
```json
{
  "estimatedBudget": 15000000.00,
  "totalAllocated": 14200000.00,
  "totalConfirmed": 9850000.00,
  "totalActual": 3200000.00,
  "remainingBudget": 5150000.00,
  "categories": [
    {
      "category": "Catering",
      "allocatedAmount": 4500000.00,
      "confirmedCost": 4125000.00,
      "actualCost": 1500000.00,
      "variance": 375000.00,
      "notes": "Derived from Phase 3 accepted catering quotations."
    },
    {
      "category": "Decor",
      "allocatedAmount": 3500000.00,
      "confirmedCost": 3200000.00,
      "actualCost": 1000000.00,
      "variance": 300000.00,
      "notes": "Mandap & Sangeet production contracts."
    },
    {
      "category": "Accommodation",
      "allocatedAmount": 2800000.00,
      "confirmedCost": 2250000.00,
      "actualCost": 500000.00,
      "variance": 550000.00,
      "notes": "Room block commitments."
    }
  ]
}
```

#### 24. `PUT /api/v1/plans/{plan_id}/budget/allocations`
- **Purpose:** Set or update category budget allocations.
- **Request Body:** `List[BudgetAllocationItem]`
```json
[
  { "category": "Venue", "allocatedAmount": 2500000.00 },
  { "category": "Catering", "allocatedAmount": 4500000.00 },
  { "category": "Decor", "allocatedAmount": 3500000.00 },
  { "category": "Entertainment", "allocatedAmount": 1200000.00 },
  { "category": "Photography & Videography", "allocatedAmount": 800000.00 },
  { "category": "Accommodation", "allocatedAmount": 2800000.00 },
  { "category": "Transportation", "allocatedAmount": 600000.00 },
  { "category": "Wedding Production", "allocatedAmount": 900000.00 },
  { "category": "Miscellaneous", "allocatedAmount": 500000.00 }
]
```
- **Response `200 OK`:** `WeddingBudgetOverviewResponse`

#### 25. `POST /api/v1/plans/{plan_id}/budget/expenses`
- **Purpose:** Log an actual payment or expense.
- **Request Body:** `WeddingExpenseCreate`
```json
{
  "title": "Vendor Advance — Royal Mewar Decorators",
  "category": "Decor",
  "amount": 925000.00,
  "paymentDate": "2026-10-25",
  "paidTo": "Royal Mewar Decorators",
  "paymentMethod": "NEFT / RTGS",
  "referenceNumber": "HDFC0001928374",
  "vendorId": "VND-002",
  "notes": "50% advance mobilization deposit."
}
```
- **Response `201 Created`:** `WeddingExpenseResponse`

#### 26. `DELETE /api/v1/plans/{plan_id}/budget/expenses/{expense_id}`
- **Purpose:** Remove an expense entry.
- **Response `200 OK`:** `{ "success": true, "message": "Expense removed." }`

---

### 4.8 Section G: Guest & Accommodation Planning

#### 27. `GET /api/v1/plans/{plan_id}/accommodations`
- **Purpose:** List all hotel room blocks, reserved capacities, and confirmation statuses.
- **Response `200 OK`:** `List[WeddingPlanAccommodationResponse]`
```json
[
  {
    "id": "ACC-001",
    "hotelName": "The Oberoi Udaivilas, Udaipur",
    "roomType": "Premier Lake View Room",
    "numberOfRooms": 25,
    "guestCapacity": 50,
    "checkInDate": "2026-12-16",
    "checkOutDate": "2026-12-19",
    "estimatedRoomRate": 30000.00,
    "totalCost": 2250000.00,
    "bookingReference": "OB-UDAI-2026-78",
    "contactPerson": "Sunil Verma (Group Reservations)",
    "contactPhone": "+91 294 243 3300",
    "confirmationStatus": "Confirmed",
    "notes": "Welcome hampers placed in every room prior to check-in."
  }
]
```

#### 28. `POST /api/v1/plans/{plan_id}/accommodations`
- **Purpose:** Create a new hotel room block booking.
- **Request Body:** `WeddingPlanAccommodationCreate`
- **Response `201 Created`:** `WeddingPlanAccommodationResponse`

#### 29. `PUT /api/v1/plans/{plan_id}/accommodations/{acc_id}`
- **Purpose:** Update room block details, dates, or room counts.
- **Request Body:** `WeddingPlanAccommodationUpdate`
- **Response `200 OK`:** `WeddingPlanAccommodationResponse`

#### 30. `PATCH /api/v1/plans/{plan_id}/accommodations/{acc_id}/status`
- **Purpose:** Update room block status (`Requested`, `Blocked`, `Confirmed`, `Checked-In`, `Completed`, `Cancelled`).
- **Request Body:** `AccommodationStatusUpdate`
- **Response `200 OK`:** `WeddingPlanAccommodationResponse`

#### 31. `DELETE /api/v1/plans/{plan_id}/accommodations/{acc_id}`
- **Purpose:** Delete a room block entry.
- **Response `200 OK`:** `{ "success": true, "message": "Accommodation block removed." }`

---

### 4.9 Section H: Transportation & Logistics

#### 32. `GET /api/v1/plans/{plan_id}/logistics`
- **Purpose:** List scheduled vehicle movements, airport transfers, and guest shuttles.
- **Query Parameters:** `status: Optional[str]`, `function_id: Optional[str]`
- **Response `200 OK`:** `List[WeddingPlanLogisticsResponse]`
```json
[
  {
    "id": "LOG-001",
    "title": "VIP Airport Pickups — Mumbai Flight Arrivals",
    "vehicleType": "Toyota Innova Crysta & Mercedes E-Class",
    "vehicleCount": 6,
    "pickupLocation": "Maharana Pratap Airport (UDR)",
    "dropLocation": "The Leela Palace, Udaipur",
    "transferDatetime": "2026-12-16T11:00:00Z",
    "functionId": null,
    "vendorId": "VND-008",
    "assignedDriverContact": "Ramesh Travels Fleet (+91 94140 55667)",
    "estimatedCost": 75000.00,
    "status": "Booked",
    "notes": "Placards with 'Oberoi & Singhania Wedding' required."
  }
]
```

#### 33. `POST /api/v1/plans/{plan_id}/logistics`
- **Purpose:** Add a logistics transfer or shuttle schedule.
- **Request Body:** `WeddingPlanLogisticsCreate`
- **Response `201 Created`:** `WeddingPlanLogisticsResponse`

#### 34. `PUT /api/v1/plans/{plan_id}/logistics/{log_id}`
- **Purpose:** Update logistics details, routes, or vehicle allocations.
- **Request Body:** `WeddingPlanLogisticsUpdate`
- **Response `200 OK`:** `WeddingPlanLogisticsResponse`

#### 35. `PATCH /api/v1/plans/{plan_id}/logistics/{log_id}/status`
- **Purpose:** Update logistics status (`Planned`, `Booked`, `Dispatched`, `Completed`, `Cancelled`).
- **Request Body:** `LogisticsStatusUpdate`
- **Response `200 OK`:** `WeddingPlanLogisticsResponse`

#### 36. `DELETE /api/v1/plans/{plan_id}/logistics/{log_id}`
- **Purpose:** Delete a logistics entry.
- **Response `200 OK`:** `{ "success": true, "message": "Logistics transfer removed." }`

---

### 4.10 Section I: Staff & User Assignments

#### 37. `GET /api/v1/staff`
- **Purpose:** List agency staff members eligible for assignment across tasks, milestones, and wedding plans.
- **Response `200 OK`:** `List[StaffMemberResponse]`
```json
[
  { "id": "staff-01", "name": "Maharani Gayatri Singh", "role": "Principal Wedding Director", "email": "gayatri@royal-knot.com" },
  { "id": "staff-02", "name": "Devraj Singh", "role": "Senior Production & Decor Lead", "email": "devraj@royal-knot.com" },
  { "id": "staff-03", "name": "Ananya Sharma", "role": "Guest Hospitality & Logistics Lead", "email": "ananya@royal-knot.com" },
  { "id": "staff-04", "name": "Rohan Mehra", "role": "Catering & Banquet Coordinator", "email": "rohan@royal-knot.com" }
]
```

---

## 5. Frontend Architecture & UI Design

### 5.1 Route & View Integration Strategy
1. **Primary Route:** The Wedding Plan area will be accessible from:
   - `/projects/:id` under a dedicated **Wedding Plan** workspace or seamless sub-tabs.
   - Dedicated route: `/weddings/:id` or `/projects/:id/plan` will seamlessly load the live backend-backed Wedding Plan.
2. **Unified UI Hierarchy:**
   - **Header:** Couple name, project code, palatial location, date range, planning progress bar, plan status badge, quick actions (Export Plan Summary, Add Task).
   - **Tabbed Workspace:**
     - **Tab 1: Overview:** Metric summary cards (Budget, Tasks, Milestones, Events, Guests, Accommodations), upcoming deadlines, critical alerts.
     - **Tab 2: Events & Schedule:** Day-by-day ceremony cards, event timings, venue, guest count overrides, linked catering status, and event notes.
     - **Tab 3: Tasks & Checklist:** Filterable interactive task manager by category, priority, status, and assignee. Inline status toggle, new task modal.
     - **Tab 4: Timeline & Milestones:** Visual vertical timeline with milestone checkpoints, due dates, completion dates, and assignee.
     - **Tab 5: Vendor Coordination:** Non-catering vendor roster, contracts, responsibilities, and confirmation status. Seamless link to Phase 3 Catering tab.
     - **Tab 6: Budget & Expenses:** Category-wise breakdown with progress bars, allocation editor, expense logger, and cost reconciliation.
     - **Tab 7: Accommodation:** Palatial hotel room blocks, capacities, check-in dates, and contact vouchers.
     - **Tab 8: Logistics & Transport:** Vehicle fleet schedule, airport transfers, shuttle timings, and driver details.
3. **State Management & Data Hygiene:**
   - Real backend data fetching via `weddingPlanApi`.
   - Replaces `localStorage` mock data in `WeddingTasksPanel` with live server persistence.
   - Full TypeScript interfaces under `frontend/src/types/weddingPlan.ts`.
   - Comprehensive error, empty, and loading skeleton states.

---

## 6. Migration Plan & Database Scripts

### 6.1 Alembic Migration
Alembic migration revision: `b4c19d28e701_add_wedding_plan_management_tables.py`
Down revision: `a1c8f921d7b3` (Phase 3 Catering & Vendor models)

1. Create `wedding_plans` table.
2. Add `guest_count` and `notes` to `wedding_functions` table.
3. Add `assigned_to`, `function_id`, and `category` to `project_milestones` table.
4. Create `wedding_plan_tasks` table.
5. Create `wedding_plan_vendor_assignments` table.
6. Create `wedding_budget_allocations` table with unique constraint on `(plan_id, category)`.
7. Create `wedding_expenses` table.
8. Create `wedding_plan_accommodations` table.
9. Create `wedding_plan_logistics` table.
10. Create appropriate indexes and foreign key cascades.

---

## 7. Testing & Quality Assurance Blueprint

### 7.1 Backend Test Coverage (`pytest`)
A dedicated suite `backend/tests/test_phase4_wedding_plan_api.py` covering:
- Plan auto-initialization from project dossier.
- Explicit plan creation, update, and status transitions.
- Task creation, updating, assignment, filtering, completion, and deletion.
- Milestone assignment and completion tracking.
- Vendor assignment creation, linking to existing `Vendor`, and status transitions.
- Budget allocation updates, expense logging, and variance calculations without double counting.
- Accommodation room block management and capacity tracking.
- Logistics transfer scheduling and status updates.
- Event guest count override verification (ensuring project master guest count remains untouched).
- Foreign key cascading and transaction safety.

### 7.2 Frontend Verification
- Type check: `npm run build` (`tsc -b && vite build`) without TypeScript or compilation errors.
- Visual verification across all 8 planning tabs.
- Form validation on required fields and positive financial numbers.
- Currency formatting in Indian Rupee format (`₹`, `Lakhs`, `Crores`).

### 7.3 Regression Verification
- Re-run complete test suite across:
  - Phase 1: Client dossiers & enquiries (`test_enquiry_activation_workflow.py`, `test_automated_registration_workflow.py`, `test_email_integration_workflow.py`).
  - Phase 3: Project setup & functions (`test_phase3_projects_workflow.py`).
  - Phase 3: Catering models & endpoints (`test_phase3_catering_models.py`, `test_phase3_catering_api.py`).
- Total passing backend test suite must exceed 55+ test cases.

---

## 8. Implementation Stages Roadmap

- **Stage 1 (Current):** Discovery, Codebase Inspection, Architecture & API Blueprint, `phase-4` branch setup.
- **Stage 2:** Backend Models, Alembic Migration, Pydantic Schemas, Service Layer, API Endpoints, and Backend Tests.
- **Stage 3:** Frontend API Client, TypeScript Models, Wedding Plan UI Workspace & Tabbed Components.
- **Stage 4:** Full Integration, Regression Testing of Phases 1–3, Bug Fixing.
- **Stage 5:** Final Quality Audit & Delivery Report.
