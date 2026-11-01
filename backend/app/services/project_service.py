import uuid
import random
from typing import Optional, List, Tuple
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func

from app.models.client import Client
from app.models.vendor import Vendor
from app.models.project import (
    WeddingProject,
    WeddingFunction,
    ProjectMilestone,
    ProjectStatusHistory,
    ProjectVendor,
    PlanningTask,
    PaymentStage,
    TeamTimeEntry,
    BigDayScheduleEvent,
    WeddingExtra,
    VendorPayout,
)
from app.models.catering import CateringPlan
from app.schemas.project import (
    WeddingProjectCreate,
    WeddingProjectUpdate,
    ProjectStatusUpdate,
    WeddingFunctionCreate,
    WeddingFunctionUpdate,
    WeddingFunctionResponse,
    ProjectMilestoneCreate,
    ProjectMilestoneUpdate,
    EligibleBookingResponse,
    PlanningTaskCreate,
    PlanningTaskUpdate,
    PlanningTaskResponse,
    PaymentStageCreate,
    PaymentStageUpdate,
    PaymentStageResponse,
    TeamTimeEntryCreate,
    TeamTimeEntryResponse,
    FounderProfitabilityResponse,
    DepositPaidResponse,
    BigDayScheduleEventCreate,
    BigDayScheduleEventUpdate,
    BigDayScheduleEventResponse,
    BigDayScheduleOverviewResponse,
    WeddingExtraCreate,
    WeddingExtraResponse,
    VendorPayoutCreate,
    VendorPayoutResponse,
    FinalSettlementResponse,
    ClientWeddingOverviewResponse,
)


class ProjectService:

    @staticmethod
    def generate_project_code(db: Session, target_date: Optional[date] = None) -> str:
        """
        Generates unique, sequential project code in format PRJ-YYYY-XXX (e.g. PRJ-2026-001).
        """
        year = target_date.year if target_date else datetime.now().year
        prefix = f"PRJ-{year}-"

        # Count existing projects for that year
        count = db.query(func.count(WeddingProject.id)).filter(
            WeddingProject.project_code.like(f"{prefix}%")
        ).scalar() or 0

        next_num = count + 1
        return f"{prefix}{next_num:03d}"

    @staticmethod
    def get_eligible_confirmed_bookings(db: Session) -> List[EligibleBookingResponse]:
        """
        Retrieves all client dossiers with status == 'Confirmed' that do NOT currently
        have an active wedding project associated with them.
        """
        # Subquery of client_ids already having a wedding project
        existing_project_client_ids = db.query(WeddingProject.client_id).filter(
            WeddingProject.is_deleted == False
        ).scalar_subquery()

        eligible_clients = db.query(Client).filter(
            Client.status == "Confirmed",
            Client.is_deleted == False,
            ~Client.id.in_(existing_project_client_ids)
        ).order_by(Client.wedding_date.asc()).all()

        results = []
        for c in eligible_clients:
            results.append(EligibleBookingResponse(
                client_id=c.id,
                partner1_name=c.partner1_name,
                partner2_name=c.partner2_name,
                couple_name=f"{c.partner1_name} & {c.partner2_name}",
                wedding_date=c.wedding_date,
                wedding_location=c.wedding_location,
                expected_guest_count=c.expected_guest_count,
                estimated_budget=c.estimated_budget,
                service_package=c.service_package,
                status=c.status,
                created_at=c.created_at
            ))
        return results

    @classmethod
    def create_project(cls, db: Session, project_in: WeddingProjectCreate) -> WeddingProject:
        """
        Creates a new wedding project from an eligible confirmed client booking.
        Validates confirmed status, checks for duplicate projects, auto-fills defaults,
        generates project code, and logs initial status history.
        """
        # 1. Fetch client
        client = db.query(Client).filter(
            Client.id == project_in.client_id,
            Client.is_deleted == False
        ).first()

        if not client:
            raise ValueError(f"Client dossier '{project_in.client_id}' does not exist.")

        # 2. Validate confirmed booking status
        if client.status != "Confirmed":
            raise ValueError(
                f"Client '{client.id}' has status '{client.status}'. "
                f"Only confirmed bookings (status: 'Confirmed') are eligible for wedding project setup."
            )

        # 3. Check for existing project to prevent duplicate setup
        existing = db.query(WeddingProject).filter(
            WeddingProject.client_id == client.id,
            WeddingProject.is_deleted == False
        ).first()
        if existing:
            raise ValueError(
                f"A wedding project ({existing.project_code}) has already been created for booking '{client.id}'."
            )

        # 4. Resolve defaults from client dossier
        couple_name = f"{client.partner1_name} & {client.partner2_name}"
        project_name = project_in.project_name or f"{couple_name} Royal Wedding"
        wedding_date = project_in.wedding_date or client.wedding_date
        location = project_in.location or client.wedding_location
        guest_count = project_in.guest_count or client.expected_guest_count
        estimated_budget = project_in.estimated_budget if project_in.estimated_budget is not None else client.estimated_budget
        package_tier = project_in.package_tier or client.service_package
        project_manager = project_in.project_manager_name or "Maharani Gayatri Singh"
        notes = project_in.notes or client.notes

        # 5. Generate project code and ID
        project_code = cls.generate_project_code(db, wedding_date)
        project_id = f"PRJ-{uuid.uuid4().hex[:8].upper()}"

        db_project = WeddingProject(
            id=project_id,
            project_code=project_code,
            client_id=client.id,
            booking_id=client.id,  # Prepared for Phase 2
            project_name=project_name,
            wedding_date=wedding_date,
            location=location,
            guest_count=guest_count,
            estimated_budget=estimated_budget,
            package_tier=package_tier,
            project_manager_name=project_manager,
            status="Planning",
            notes=notes,
            is_deleted=False
        )

        db.add(db_project)
        db.flush()

        # 6. Record initial status history
        initial_history = ProjectStatusHistory(
            project_id=db_project.id,
            old_status=None,
            new_status="Planning",
            changed_by=project_manager,
            notes="Project initialized from confirmed wedding booking dossier.",
            changed_at=datetime.now(timezone.utc)
        )
        db.add(initial_history)

        # 7. Seed standard destination wedding milestones relative to wedding date
        default_milestones = [
            ("Finalise Heritage Palace Venue & Run-Sheet", 60, "Confirm production permissions, sound licenses, and lawn allocations."),
            ("Confirm Royal Decor & Floral Mandap Concept", 45, "Approve design moodboards, lighting setups, and flower installations."),
            ("Finalise Catering Menu & Khansama Degustation", 30, "Confirm royal Marwari degustation courses, live counter setups, and dietary logs."),
            ("Confirm Photography, Sound/Light & Pyrotechnics", 20, "Review technical riders, drone permissions, and rehearsal schedules."),
            ("Final Logistics, Baraat Procession & VIP Protocol", 7, "Review vintage car transfers, guest luggage tags, and security protocols.")
        ]

        for name, days_prior, desc in default_milestones:
            m_due = wedding_date - timedelta(days=days_prior)
            if m_due < date.today():
                m_due = date.today() + timedelta(days=7)

            ms = ProjectMilestone(
                id=f"MS-{uuid.uuid4().hex[:8].upper()}",
                project_id=db_project.id,
                milestone_name=name,
                description=desc,
                due_date=m_due,
                status="Pending"
            )
            db.add(ms)

        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def list_projects(
        db: Session,
        search: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WeddingProject], int]:
        """
        Lists projects with search, status filtering, and pagination.
        """
        query = db.query(WeddingProject).join(Client, WeddingProject.client_id == Client.id).filter(
            WeddingProject.is_deleted == False
        )

        if status and status != "All":
            query = query.filter(WeddingProject.status == status)

        if search:
            st = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    WeddingProject.project_code.ilike(st),
                    WeddingProject.project_name.ilike(st),
                    WeddingProject.location.ilike(st),
                    Client.partner1_name.ilike(st),
                    Client.partner2_name.ilike(st),
                )
            )

        total = query.count()
        offset = (page - 1) * page_size
        projects = query.order_by(WeddingProject.wedding_date.asc()).offset(offset).limit(page_size).all()
        return projects, total

    @staticmethod
    def get_project(db: Session, project_id: str) -> Optional[WeddingProject]:
        """
        Retrieves wedding project by ID or project_code with all relationships eagerly loaded.
        """
        return db.query(WeddingProject).options(
            joinedload(WeddingProject.client),
            joinedload(WeddingProject.functions),
            joinedload(WeddingProject.milestones),
            joinedload(WeddingProject.status_history)
        ).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()

    @staticmethod
    def update_project(db: Session, project_id: str, project_in: WeddingProjectUpdate) -> Optional[WeddingProject]:
        """
        Updates allowed project metadata.
        """
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()

        if not project:
            return None

        update_dict = project_in.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                setattr(project, field, value)

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def update_project_status(
        db: Session,
        project_id: str,
        status_in: ProjectStatusUpdate
    ) -> Optional[WeddingProject]:
        """
        Updates project status and records an audit log entry in ProjectStatusHistory.
        """
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()

        if not project:
            return None

        old_status = project.status
        new_status = status_in.status

        if old_status != new_status:
            project.status = new_status

            history_entry = ProjectStatusHistory(
                project_id=project.id,
                old_status=old_status,
                new_status=new_status,
                changed_by=status_in.changed_by or "Agency Staff",
                notes=status_in.notes or f"Status transitioned from '{old_status}' to '{new_status}'."
            )
            db.add(history_entry)
            db.commit()
            db.refresh(project)

        return project

    # =====================================================================
    # Functions Management & Cost Estimation
    # =====================================================================

    @staticmethod
    def calculate_estimated_cost(function_name: str) -> Decimal:
        """
        Calculates a realistic random estimated cost based on function name tiers,
        rounded to the nearest ₹5,000.
        - 'mehendi' or 'mehndi': ₹45,000 - ₹90,000
        - 'haldi': ₹40,000 - ₹85,000
        - 'sangeet' or 'cocktail': ₹1,20,000 - ₹2,50,000
        - 'wedding', 'muhurtham', or 'phera': ₹2,50,000 - ₹5,00,000
        - 'reception': ₹1,75,000 - ₹3,50,000
        - Other function name: ₹50,000 - ₹2,00,000
        """
        fn_lower = (function_name or "").lower().strip()
        if "mehendi" in fn_lower or "mehndi" in fn_lower:
            low, high = 45000, 90000
        elif "haldi" in fn_lower:
            low, high = 40000, 85000
        elif "sangeet" in fn_lower or "cocktail" in fn_lower:
            low, high = 120000, 250000
        elif "wedding" in fn_lower or "muhurtham" in fn_lower or "phera" in fn_lower or "varmala" in fn_lower:
            low, high = 250000, 500000
        elif "reception" in fn_lower:
            low, high = 175000, 350000
        else:
            low, high = 50000, 200000

        raw_val = random.randint(low, high)
        rounded_val = round(raw_val / 5000) * 5000
        rounded_val = max(low, min(high, rounded_val))
        return Decimal(str(rounded_val))

    @classmethod
    def add_function(cls, db: Session, project_id: str, func_in: WeddingFunctionCreate) -> WeddingFunction:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()

        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # Determine estimated cost: use provided if > 0, else auto-estimate
        cost = func_in.estimated_cost
        if cost is None or cost == Decimal("0.00") or cost == 0:
            cost = cls.calculate_estimated_cost(func_in.function_name)

        func_id = f"FUNC-{uuid.uuid4().hex[:8].upper()}"
        db_func = WeddingFunction(
            id=func_id,
            project_id=project.id,
            function_name=func_in.function_name,
            function_date=func_in.function_date,
            start_time=func_in.start_time,
            end_time=func_in.end_time,
            venue=func_in.venue or project.location,
            description=func_in.description,
            status=func_in.status,
            estimated_cost=cost
        )

        db.add(db_func)
        db.commit()
        db.refresh(db_func)
        return db_func

    @classmethod
    def backfill_function_costs(cls, db: Session) -> int:
        """
        Backfills existing functions having NULL or 0 estimated_cost with realistic tier costs.
        """
        functions = db.query(WeddingFunction).filter(
            or_(
                WeddingFunction.estimated_cost == None,
                WeddingFunction.estimated_cost == 0,
                WeddingFunction.estimated_cost == Decimal("0.00")
            )
        ).all()
        updated_count = 0
        for fn in functions:
            fn.estimated_cost = cls.calculate_estimated_cost(fn.function_name)
            updated_count += 1
        if updated_count > 0:
            db.commit()
        return updated_count

    @staticmethod
    def update_function(
        db: Session,
        project_id: str,
        func_id: str,
        func_in: WeddingFunctionUpdate
    ) -> Optional[WeddingFunction]:
        func_item = db.query(WeddingFunction).filter(
            WeddingFunction.id == func_id
        ).first()

        if not func_item:
            return None

        update_dict = func_in.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                setattr(func_item, field, value)

        db.commit()
        db.refresh(func_item)
        return func_item

    @staticmethod
    def delete_function(db: Session, project_id: str, func_id: str) -> bool:
        func_item = db.query(WeddingFunction).filter(
            WeddingFunction.id == func_id
        ).first()

        if not func_item:
            return False

        db.delete(func_item)
        db.commit()
        return True

    # =====================================================================
    # Milestones Management
    # =====================================================================

    @staticmethod
    def add_milestone(db: Session, project_id: str, ms_in: ProjectMilestoneCreate) -> ProjectMilestone:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()

        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        ms_id = f"MS-{uuid.uuid4().hex[:8].upper()}"
        completed_at = datetime.now(timezone.utc) if ms_in.status == "Completed" else None

        db_ms = ProjectMilestone(
            id=ms_id,
            project_id=project.id,
            milestone_name=ms_in.milestone_name,
            description=ms_in.description,
            due_date=ms_in.due_date,
            status=ms_in.status,
            completed_at=completed_at
        )

        db.add(db_ms)
        db.commit()
        db.refresh(db_ms)
        return db_ms

    @staticmethod
    def update_milestone(
        db: Session,
        project_id: str,
        ms_id: str,
        ms_in: ProjectMilestoneUpdate
    ) -> Optional[ProjectMilestone]:
        ms = db.query(ProjectMilestone).filter(
            ProjectMilestone.id == ms_id
        ).first()

        if not ms:
            return None

        update_dict = ms_in.model_dump(exclude_unset=True)

        if "status" in update_dict:
            new_status = update_dict["status"]
            if new_status == "Completed" and ms.status != "Completed":
                ms.completed_at = datetime.now(timezone.utc)
            elif new_status != "Completed":
                ms.completed_at = None

        for field, value in update_dict.items():
            if value is not None:
                setattr(ms, field, value)

        db.commit()
        db.refresh(ms)
        return ms

    @staticmethod
    def delete_milestone(db: Session, project_id: str, ms_id: str) -> bool:
        ms = db.query(ProjectMilestone).filter(
            ProjectMilestone.id == ms_id
        ).first()

        if not ms:
            return False

        db.delete(ms)
        db.commit()
        return True



    # =====================================================================
    # P0 Item 3: Deposit -> Plan Generation (Tasks & Payment Stages)
    # =====================================================================

    FULL_PACKAGE_TASKS = [
        # Venue (4)
        ("Venue Recce & Technical Feasibility Sign-off", "Venue", -90, "Maharani Gayatri Singh", "High", "Check load limits, power backups, and lawn drainage."),
        ("Palace Courtyard & Ballroom Floor Plan Approval", "Venue", -75, "Raghav Sharma", "High", "Finalize seating, stage buffer, and emergency egress corridors."),
        ("Hotel Room Block Allocation & Key Handover Protocol", "Venue", -45, "Pooja Verma", "Medium", "Allocate royal suites and guest wings with concierge desk."),
        ("Sound Decibel & Municipal Curfew Permits", "Venue", -30, "Aditya Rathore", "Urgent", "Obtain Rajasthan police and municipal sound clearance for outdoors."),
        # Design & Decor (4)
        ("Royal Rajasthani Moodboard & Theme Sign-off", "Design", -80, "Maharani Gayatri Singh", "High", "Finalize color palettes, fabrics, and heritage motif detailing."),
        ("Floral Architecture & Mandap 3D Render Sign-off", "Design", -60, "Raghav Sharma", "High", "Review marigold, lotus, and exotic tuberose installations."),
        ("Ambient Lighting & Palace Facade Projection Mapping", "Design", -40, "Aditya Rathore", "Medium", "Program moving heads and architectural warm wash gobos."),
        ("Custom Stationery, Welcome Hampers & Itinerary Print", "Design", -25, "Pooja Verma", "Medium", "Distribute gold-embossed wax-sealed cards in guest rooms."),
        # Vendors (4)
        ("Royal Catering Menu Tasting & Executive Chef Sign-off", "Vendors", -50, "Maharani Gayatri Singh", "High", "Approve live counters, chaat station, and thali sequences."),
        ("Celebrity Artist & Band Hospitality Riders Contract", "Vendors", -45, "Raghav Sharma", "High", "Coordinate green rooms, technical rider, and backstage security."),
        ("Lead Cinematographer & Drone Pilot Permitting", "Vendors", -35, "Aditya Rathore", "Medium", "Verify 4K camera crew positions and airspace authorization."),
        ("Bridal Hair & Makeup Artist Schedule Finalization", "Vendors", -20, "Pooja Verma", "High", "Coordinate staggered call times for bride, groom, and mothers."),
        # Mehendi Ceremony (4)
        ("Mehendi Master Artists Crew Briefing (15 Artists)", "Mehendi", -15, "Pooja Verma", "High", "Verify organic sojat heena cones and speed-artist stations."),
        ("Poolside Cabana & Colorful Diwan Seating Arrangement", "Mehendi", -10, "Raghav Sharma", "Medium", "Install bandhani drapes, umbrellas, and embroidered cushions."),
        ("Bangle Bar, Lac Craftsmen & Live Folk Dancers Booking", "Mehendi", -7, "Pooja Verma", "Medium", "Coordinate authentic Rajasthani cultural craft experiences."),
        ("Mehendi Cocktail & Mocktail Bar Menu Finalization", "Mehendi", -5, "Aditya Rathore", "Medium", "Approve summer coolers, spiced gin bar, and coconut water station."),
        # Sangeet Night (4)
        ("Concert Trussing & High-Res LED Screen Calibration", "Sangeet", -12, "Aditya Rathore", "High", "Setup 60ft stage truss and calibrate video playback."),
        ("Family Sangeet Choreographer Run-through & Cue Sheet", "Sangeet", -8, "Raghav Sharma", "High", "Rehearse 14 family group performances and lighting transitions."),
        ("DJ Console & Line-Array Audio Sound Check", "Sangeet", -4, "Aditya Rathore", "Urgent", "Conduct pink noise audio calibration across the ballroom."),
        ("Midnight Afterparty Bar & Snack Buffet Setup", "Sangeet", -2, "Pooja Verma", "Medium", "Finalize late night sliders, chaat, and coffee bar for 2 AM."),
        # Wedding Ceremony / Pheras (4)
        ("Royal Baraat Route, Elephants & Brass Band Coordination", "Wedding Day", -5, "Maharani Gayatri Singh", "High", "Escort vintage convertibles and royal nagada drummers."),
        ("Vedic Head Priest (Pandit Ji) & Samagri Inspection", "Wedding Day", -3, "Pooja Verma", "High", "Verify havan kund wood, pure ghee, and auspicious muhurat timing."),
        ("Varmala Floating Stage & Hydraulic Rose Shower Test", "Wedding Day", -2, "Aditya Rathore", "Urgent", "Test dual mechanical lifts and pneumatic rose petal cannons."),
        ("Mandap Sacred Fire Safety Protocol & Heritage Guards", "Wedding Day", -1, "Raghav Sharma", "Urgent", "Deploy heritage security and discrete water/sand safeguards."),
        # Reception (4)
        ("Formal Banquet Table Placement & VIP Card Embossing", "Reception", -3, "Pooja Verma", "Medium", "Seat 400 dignitaries with personalized menu cards and silver cutlery."),
        ("Symphony Orchestra & Jazz Quartet Warm-up", "Reception", -2, "Raghav Sharma", "Medium", "Acoustic balance for sit-down dinner and reception speeches."),
        ("5-Tier Royal Wedding Cake Transport & Cryo Storage", "Reception", -1, "Pooja Verma", "High", "Inspect sugar floral cascading and temperature-controlled room."),
        ("Cold Pyro Stage Sparklers & Grand Send-off Fireworks", "Reception", 0, "Aditya Rathore", "High", "Coordinate Rajasthan explosives clearance and cue sparklers."),
    ]

    PARTIAL_PACKAGE_TASKS = [
        # 25 tasks for Partial Planning
        ("Client Existing Vendor Contracts Audit & Gap Analysis", "Vendors", -60, "Maharani Gayatri Singh", "High", "Review scopes of client-hired vendors."),
        ("Master Event Day Run-of-Show Timeline Integration", "Venue", -45, "Raghav Sharma", "High", "Compile single minute-by-minute schedule."),
        ("Venue Access Windows & Loading Dock Clearances", "Venue", -40, "Aditya Rathore", "Medium", "Coordinate hotel banquet freight elevators."),
        ("Power & Generator Capacity Verification", "Venue", -35, "Aditya Rathore", "Urgent", "Validate backup power distribution."),
        ("Design Alignment & Production Floor Plan", "Design", -30, "Raghav Sharma", "Medium", "Verify decor measurements match venue ballroom."),
        ("Lighting & Audio Gear Technical Inspection", "Design", -25, "Aditya Rathore", "Medium", "Ensure sound checks don't clip amplifier limits."),
        ("Signage & Guest Directional Flow Verification", "Design", -20, "Pooja Verma", "Low", "Place entry arches and easel displays."),
        ("Catering Service Headcount Guarantee Confirmation", "Vendors", -18, "Maharani Gayatri Singh", "High", "Confirm final guest count."),
        ("Vendor Meal Passes & Backstage Crew Badges", "Vendors", -15, "Pooja Verma", "Medium", "Distribute crew identification tags."),
        ("Photography Shot List & VIP Group Photos Coordination", "Vendors", -12, "Raghav Sharma", "Medium", "Coordinate family coordinator for portraits."),
        ("Mehendi Staging & Seating Setup Audit", "Mehendi", -10, "Pooja Verma", "Medium", "Check cushions, shade, and heena tables."),
        ("Mehendi Music & Background Audio Setup", "Mehendi", -8, "Aditya Rathore", "Medium", "Ensure dhol and playlists are operational."),
        ("Mehendi Welcome Drinks & Refreshment Station Check", "Mehendi", -6, "Pooja Verma", "Medium", "Ensure cold drinks and water service."),
        ("Sangeet Sound & LED Video Cue Alignment", "Sangeet", -10, "Aditya Rathore", "High", "Verify multimedia audio/video sync."),
        ("Sangeet Stage Step Safety & Edge Lighting Check", "Sangeet", -7, "Raghav Sharma", "High", "Prevent trip hazards on performance riser."),
        ("Sangeet Green Room & Touch-up Room Setup", "Sangeet", -5, "Pooja Verma", "Medium", "Prepare dressing rooms with full mirrors."),
        ("Sangeet Emcee Script & Announcement Run-through", "Sangeet", -4, "Raghav Sharma", "High", "Review bridal party pronunciations."),
        ("Baraat Assembly & Traffic Management Plan", "Wedding Day", -5, "Maharani Gayatri Singh", "High", "Ensure guest parking and road clearance."),
        ("Mandap Seating Protocol & Religious Offerings Verification", "Wedding Day", -3, "Pooja Verma", "High", "Coordinate chairs and prayer cushions."),
        ("Varmala Stage Mic & Spotlights Cueing", "Wedding Day", -2, "Aditya Rathore", "Urgent", "Focus warm follow-spots on couple."),
        ("Bridal Entry Walkway & Chhatra Coordination", "Wedding Day", -1, "Raghav Sharma", "High", "Direct brothers carrying the phoolon ki chaadar."),
        ("Pheras Fire Safety Officer Standby", "Wedding Day", 0, "Aditya Rathore", "Urgent", "Verify fire extinguisher behind backdrop."),
        ("Reception Dinner Seating Gatekeeping", "Reception", -2, "Pooja Verma", "Medium", "Direct guests toward reserved tables."),
        ("Reception Stage Photo Session Queue Management", "Reception", -1, "Raghav Sharma", "Medium", "Smooth flow of greeting guests."),
        ("End-of-Night Vendor Load-out Supervision", "Reception", 0, "Aditya Rathore", "High", "Ensure no damage to palace property during breakdown."),
    ]

    @classmethod
    def mark_deposit_paid(cls, db: Session, project_id: str) -> dict:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()

        if not project:
            raise ValueError(f"Wedding project '{project_id}' not found.")

        now = datetime.now(timezone.utc)
        today = now.date()

        if not project.deposit_paid:
            project.deposit_paid = True
            project.deposit_paid_at = now

        # 1. Idempotent Planning Tasks Generation
        existing_tasks_count = db.query(PlanningTask).filter_by(project_id=project.id).count()

        if existing_tasks_count == 0:
            is_partial = "partial" in (project.package_tier or "").lower()
            template = cls.PARTIAL_PACKAGE_TASKS if is_partial else cls.FULL_PACKAGE_TASKS

            for task_title, category, day_offset, owner, priority, notes in template:
                task_due = project.wedding_date + timedelta(days=day_offset)
                task_id = f"TSK-{uuid.uuid4().hex[:8].upper()}"
                db_task = PlanningTask(
                    id=task_id,
                    project_id=project.id,
                    title=task_title,
                    category=category,
                    stage="To Plan",
                    assigned_to=owner,
                    priority=priority,
                    due_date=task_due,
                    notes=notes,
                    is_completed=False
                )
                db.add(db_task)

        # 2. Idempotent 3 Payment Stages Generation
        existing_stages_count = db.query(PaymentStage).filter_by(project_id=project.id).count()

        if existing_stages_count == 0:
            budget = project.estimated_budget or Decimal("5000000.00")
            
            # Advance due = wedding date - 30 days
            advance_due = project.wedding_date - timedelta(days=30)
            # Final after the event = wedding date + 3 days
            final_due = project.wedding_date + timedelta(days=3)

            stage1 = PaymentStage(
                id=f"PAY-{uuid.uuid4().hex[:8].upper()}",
                project_id=project.id,
                stage_name="Booking Retainer Deposit",
                percentage=Decimal("25.00"),
                amount=Decimal(str(round(budget * Decimal("0.25"), 2))),
                due_date=today,
                due_description="Booking confirmation retainer (25%) upon contract execution",
                status="Paid",
                paid_at=project.deposit_paid_at
            )
            stage2 = PaymentStage(
                id=f"PAY-{uuid.uuid4().hex[:8].upper()}",
                project_id=project.id,
                stage_name="Advance Production Milestone",
                percentage=Decimal("40.00"),
                amount=Decimal(str(round(budget * Decimal("0.40"), 2))),
                due_date=advance_due,
                due_description="Production advance (40%) due 30 days prior to event",
                status="Pending",
                paid_at=None
            )
            stage3 = PaymentStage(
                id=f"PAY-{uuid.uuid4().hex[:8].upper()}",
                project_id=project.id,
                stage_name="Final Settlement Balance",
                percentage=Decimal("35.00"),
                amount=Decimal(str(round(budget * Decimal("0.35"), 2))),
                due_date=final_due,
                due_description="Final settlement balance (35%) post-event completion",
                status="Pending",
                paid_at=None
            )
            db.add_all([stage1, stage2, stage3])

        db.commit()
        db.refresh(project)

        total_tasks = db.query(PlanningTask).filter_by(project_id=project.id).count()
        total_stages = db.query(PaymentStage).filter_by(project_id=project.id).count()

        return {
            "project_id": project.id,
            "project_code": project.project_code,
            "deposit_paid": project.deposit_paid,
            "deposit_paid_at": project.deposit_paid_at,
            "tasks_count": total_tasks,
            "payment_stages_count": total_stages,
            "package_tier": project.package_tier,
            "message": f"Deposit marked paid. {total_tasks} planning tasks and {total_stages} payment milestones active."
        }

    @staticmethod
    def list_tasks(
        db: Session,
        project_id: str,
        stage: Optional[str] = None,
        category: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> List[PlanningTask]:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        query = db.query(PlanningTask).filter(PlanningTask.project_id == project.id)
        if stage:
            query = query.filter(PlanningTask.stage == stage)
        if category:
            query = query.filter(PlanningTask.category == category)
        if assigned_to:
            query = query.filter(PlanningTask.assigned_to == assigned_to)

        return query.order_by(PlanningTask.due_date.asc()).all()

    @staticmethod
    def update_task(
        db: Session,
        project_id: str,
        task_id: str,
        task_in: PlanningTaskUpdate
    ) -> Optional[PlanningTask]:
        task = db.query(PlanningTask).filter(PlanningTask.id == task_id).first()
        if not task:
            return None

        update_dict = task_in.model_dump(exclude_unset=True)

        if "stage" in update_dict:
            new_stage = update_dict["stage"]
            if new_stage == "Done":
                task.is_completed = True
                task.completed_at = datetime.now(timezone.utc)
            else:
                if update_dict.get("is_completed") is not True:
                    task.is_completed = False
                    task.completed_at = None

        if "is_completed" in update_dict:
            if update_dict["is_completed"] and not task.is_completed:
                task.completed_at = datetime.now(timezone.utc)
                if task.stage != "Done":
                    task.stage = "Done"
            elif not update_dict["is_completed"]:
                task.completed_at = None

        for field, value in update_dict.items():
            if value is not None:
                setattr(task, field, value)

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def list_payment_stages(db: Session, project_id: str) -> List[PaymentStage]:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        return db.query(PaymentStage).filter(PaymentStage.project_id == project.id).order_by(PaymentStage.due_date.asc()).all()

    @staticmethod
    def update_payment_stage(
        db: Session,
        project_id: str,
        stage_id: str,
        stage_in: PaymentStageUpdate
    ) -> Optional[PaymentStage]:
        stage = db.query(PaymentStage).filter(PaymentStage.id == stage_id).first()
        if not stage:
            return None

        update_dict = stage_in.model_dump(exclude_unset=True)
        if "status" in update_dict:
            new_status = update_dict["status"]
            if new_status == "Paid" and stage.status != "Paid":
                stage.paid_at = datetime.now(timezone.utc)
            elif new_status != "Paid":
                stage.paid_at = None

        for field, value in update_dict.items():
            if value is not None:
                setattr(stage, field, value)

        db.commit()
        db.refresh(stage)
        return stage

    # =====================================================================
    # P0 Item 4: Team Time Entries & Founder Profitability
    # =====================================================================

    @staticmethod
    def add_time_entry(db: Session, project_id: str, entry_in: TeamTimeEntryCreate) -> TeamTimeEntry:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        entry_id = f"TME-{uuid.uuid4().hex[:8].upper()}"
        db_entry = TeamTimeEntry(
            id=entry_id,
            project_id=project.id,
            employee_name=entry_in.employee_name,
            role=entry_in.role,
            hours=entry_in.hours,
            hourly_rate=entry_in.hourly_rate,
            task_description=entry_in.task_description,
            entry_date=entry_in.entry_date
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        return db_entry

    @staticmethod
    def list_time_entries(db: Session, project_id: str) -> List[TeamTimeEntry]:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        return db.query(TeamTimeEntry).filter(TeamTimeEntry.project_id == project.id).order_by(TeamTimeEntry.entry_date.desc()).all()

    @classmethod
    def get_profitability(cls, db: Session, project_id: str) -> dict:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Wedding project '{project_id}' not found.")

        # 1. Client Payments Received (sum of Paid payment stages)
        paid_stages = db.query(PaymentStage).filter(
            PaymentStage.project_id == project.id,
            PaymentStage.status == "Paid"
        ).all()
        client_payments_received = sum([Decimal(str(p.amount)) for p in paid_stages], Decimal("0.00"))

        # Fallback: if deposit is paid but stages weren't created or paid yet
        if client_payments_received == Decimal("0.00") and project.deposit_paid:
            client_payments_received = Decimal(str(round((project.estimated_budget or Decimal("0.00")) * Decimal("0.25"), 2)))

        # 2. Vendor Contracted Costs (sum of ProjectVendor contract_amount)
        assigned_vendors = db.query(ProjectVendor).filter(
            ProjectVendor.project_id == project.id,
            ProjectVendor.status.in_(["Contracted", "Confirmed", "Completed"])
        ).all()
        vendor_contracted_costs = sum([Decimal(str(v.contract_amount)) for v in assigned_vendors], Decimal("0.00"))

        # If no ProjectVendor records, check CateringPlan agreed_cost
        if vendor_contracted_costs == Decimal("0.00"):
            c_plans = db.query(CateringPlan).filter(
                CateringPlan.project_id == project.id,
                CateringPlan.agreed_cost.isnot(None)
            ).all()
            vendor_contracted_costs = sum([Decimal(str(cp.agreed_cost)) for cp in c_plans], Decimal("0.00"))

        # 3. Team Labor Costs (sum of hours * hourly_rate)
        time_entries = db.query(TeamTimeEntry).filter(TeamTimeEntry.project_id == project.id).all()
        team_labor_costs = sum([Decimal(str(t.hours)) * Decimal(str(t.hourly_rate)) for t in time_entries], Decimal("0.00"))
        total_team_hours = sum([Decimal(str(t.hours)) for t in time_entries], Decimal("0.00"))

        # 4. Profit and Margin
        founder_gross_profit = client_payments_received - vendor_contracted_costs - team_labor_costs
        if client_payments_received > Decimal("0.00"):
            profit_margin_percentage = Decimal(str(round((founder_gross_profit / client_payments_received) * Decimal("100.00"), 2)))
        else:
            profit_margin_percentage = Decimal("0.00")

        return {
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "client_payments_received": client_payments_received,
            "vendor_contracted_costs": vendor_contracted_costs,
            "team_labor_costs": team_labor_costs,
            "founder_gross_profit": founder_gross_profit,
            "profit_margin_percentage": profit_margin_percentage,
            "time_entries_count": len(time_entries),
            "total_team_hours": total_team_hours
        }



    # =====================================================================
    # P1 Item 5: Big Day Live Schedule & Vendor Check-in
    # =====================================================================

    @classmethod
    def add_schedule_event(cls, db: Session, project_id: str, event_in: BigDayScheduleEventCreate) -> BigDayScheduleEvent:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        ev_id = f"SCH-{uuid.uuid4().hex[:8].upper()}"
        vendor_name = event_in.vendor_name
        if event_in.vendor_id and not vendor_name:
            v = db.query(Vendor).filter(Vendor.id == event_in.vendor_id).first()
            if v:
                vendor_name = v.name

        db_event = BigDayScheduleEvent(
            id=ev_id,
            project_id=project.id,
            vendor_id=event_in.vendor_id,
            title=event_in.title,
            event_time=event_in.event_time,
            expected_arrival_time=event_in.expected_arrival_time,
            owner_name=event_in.owner_name,
            vendor_name=vendor_name,
            grace_period_minutes=event_in.grace_period_minutes,
            status=event_in.status,
            notes=event_in.notes
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event

    @classmethod
    def list_schedule_events(cls, db: Session, project_id: str) -> dict:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        events = db.query(BigDayScheduleEvent).filter(
            BigDayScheduleEvent.project_id == project.id
        ).order_by(BigDayScheduleEvent.event_time.asc()).all()

        now = datetime.now(timezone.utc)
        items = []
        arrived_count = 0
        late_count = 0
        pending_count = 0

        for ev in events:
            is_late = False
            minutes_late = 0

            if ev.arrived_at:
                arrived_count += 1
            else:
                pending_count += 1
                if ev.expected_arrival_time:
                    exp = ev.expected_arrival_time if ev.expected_arrival_time.tzinfo else ev.expected_arrival_time.replace(tzinfo=timezone.utc)
                    deadline = exp + timedelta(minutes=ev.grace_period_minutes)
                    if now > deadline:
                        is_late = True
                        diff = now - deadline
                        minutes_late = int(diff.total_seconds() // 60)
                        late_count += 1

            items.append(BigDayScheduleEventResponse(
                id=ev.id,
                project_id=ev.project_id,
                title=ev.title,
                event_time=ev.event_time,
                expected_arrival_time=ev.expected_arrival_time,
                owner_name=ev.owner_name,
                vendor_id=ev.vendor_id,
                vendor_name=ev.vendor_name,
                grace_period_minutes=ev.grace_period_minutes,
                arrived_at=ev.arrived_at,
                is_late=is_late,
                minutes_late=minutes_late,
                status="Arrived" if ev.arrived_at else ("Late" if is_late else ev.status),
                notes=ev.notes,
                created_at=ev.created_at,
                updated_at=ev.updated_at
            ))

        return {
            "project_id": project.id,
            "total_events": len(events),
            "arrived_count": arrived_count,
            "late_count": late_count,
            "pending_count": pending_count,
            "server_time": now,
            "events": items
        }

    @classmethod
    def check_in_event(cls, db: Session, project_id: str, event_id: str) -> BigDayScheduleEvent:
        ev = db.query(BigDayScheduleEvent).filter(BigDayScheduleEvent.id == event_id).first()
        if not ev:
            raise ValueError(f"Schedule event '{event_id}' not found.")

        now = datetime.now(timezone.utc)
        ev.arrived_at = now
        ev.status = "Arrived"
        db.commit()
        db.refresh(ev)
        return ev

    # =====================================================================
    # P1 Item 6: Extras & Final Settlement
    # =====================================================================

    @classmethod
    def add_extra(cls, db: Session, project_id: str, extra_in: WeddingExtraCreate) -> WeddingExtra:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        extra_id = f"EXT-{uuid.uuid4().hex[:8].upper()}"
        client_amt = extra_in.client_amount if extra_in.client_amount > Decimal("0.00") else (extra_in.quantity * extra_in.unit_price)
        vendor_amt = extra_in.vendor_amount if extra_in.vendor_amount > Decimal("0.00") else client_amt

        db_extra = WeddingExtra(
            id=extra_id,
            project_id=project.id,
            vendor_id=extra_in.vendor_id,
            description=extra_in.description,
            category=extra_in.category,
            quantity=extra_in.quantity,
            unit_price=extra_in.unit_price,
            client_amount=client_amt,
            vendor_amount=vendor_amt,
            is_approved=extra_in.is_approved,
            approved_by=extra_in.approved_by
        )
        db.add(db_extra)
        db.commit()
        db.refresh(db_extra)
        return db_extra

    @classmethod
    def list_extras(cls, db: Session, project_id: str) -> List[WeddingExtra]:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        return db.query(WeddingExtra).filter(WeddingExtra.project_id == project.id).all()

    @classmethod
    def create_vendor_payout(cls, db: Session, project_id: str, payout_in: VendorPayoutCreate) -> VendorPayout:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # Unique idempotency key so a payout cannot be created twice
        idempotency_key = f"PAYOUT-{project.id}-{payout_in.vendor_id}"
        existing = db.query(VendorPayout).filter_by(idempotency_key=idempotency_key).first()
        if existing:
            raise ValueError(f"Duplicate payout rejected: Payout for vendor '{payout_in.vendor_id}' on project '{project.id}' already exists.")

        final_amount = payout_in.agreed_amount + payout_in.approved_extras - payout_in.advance_paid
        if final_amount < Decimal("0.00"):
            final_amount = Decimal("0.00")

        payout_id = f"VPO-{uuid.uuid4().hex[:8].upper()}"
        db_payout = VendorPayout(
            id=payout_id,
            project_id=project.id,
            vendor_id=payout_in.vendor_id,
            idempotency_key=idempotency_key,
            agreed_amount=payout_in.agreed_amount,
            approved_extras=payout_in.approved_extras,
            advance_paid=payout_in.advance_paid,
            final_payout_amount=final_amount,
            status="Approved",
            notes=payout_in.notes
        )
        db.add(db_payout)
        db.commit()
        db.refresh(db_payout)
        return db_payout

    @classmethod
    def get_final_settlement(cls, db: Session, project_id: str) -> dict:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # 1. Approved Extras for Client
        approved_extras = db.query(WeddingExtra).filter(
            WeddingExtra.project_id == project.id,
            WeddingExtra.is_approved == True
        ).all()
        client_extras_total = sum([Decimal(str(e.client_amount)) for e in approved_extras], Decimal("0.00"))

        package_budget = project.estimated_budget or Decimal("0.00")
        total_invoice = package_budget + client_extras_total

        paid_stages = db.query(PaymentStage).filter(
            PaymentStage.project_id == project.id,
            PaymentStage.status == "Paid"
        ).all()
        payments_received = sum([Decimal(str(p.amount)) for p in paid_stages], Decimal("0.00"))
        balance_due = max(total_invoice - payments_received, Decimal("0.00"))

        # 2. Vendor Payouts
        payouts = db.query(VendorPayout).filter(VendorPayout.project_id == project.id).all()
        payout_items = []
        for p in payouts:
            v_name = p.vendor.name if p.vendor else "Vendor"
            payout_items.append(VendorPayoutResponse(
                id=p.id,
                project_id=p.project_id,
                vendor_id=p.vendor_id,
                vendor_name=v_name,
                idempotency_key=p.idempotency_key,
                agreed_amount=p.agreed_amount,
                approved_extras=p.approved_extras,
                advance_paid=p.advance_paid,
                final_payout_amount=p.final_payout_amount,
                status=p.status,
                notes=p.notes,
                created_at=p.created_at,
                updated_at=p.updated_at
            ))

        total_vendor_payouts = sum([Decimal(str(p.final_payout_amount)) for p in payouts], Decimal("0.00"))
        agency_retainage = total_invoice - total_vendor_payouts

        return {
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "client_invoice": {
                "package_budget": package_budget,
                "approved_extras": client_extras_total,
                "total_invoice": total_invoice,
                "payments_received": payments_received,
                "balance_due": balance_due
            },
            "vendor_payouts": payout_items,
            "total_vendor_payouts": total_vendor_payouts,
            "agency_gross_retainage": agency_retainage,
            "is_settled": balance_due == Decimal("0.00") and len(payouts) > 0
        }

    # =====================================================================
    # P1 Item 7: Client Wedding Overview (Read-Only)
    # =====================================================================

    @classmethod
    def get_client_wedding_overview(cls, db: Session, project_id: str) -> dict:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()
        if not project:
            raise ValueError(f"Wedding project '{project_id}' not found.")

        # Events
        functions = [WeddingFunctionResponse.model_validate(f) for f in project.functions]

        # Live Schedule
        schedule_data = cls.list_schedule_events(db=db, project_id=project.id)
        live_schedule = schedule_data["events"]

        # Tasks Progress
        tasks = db.query(PlanningTask).filter(PlanningTask.project_id == project.id).all()
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.is_completed or t.stage == "Done"])
        completion_pct = Decimal(str(round((completed_tasks / total_tasks * 100), 1))) if total_tasks > 0 else Decimal("0.00")

        # Confirmed Vendors
        assigned_vendors = db.query(ProjectVendor).filter(
            ProjectVendor.project_id == project.id,
            ProjectVendor.status.in_(["Contracted", "Confirmed", "Completed"])
        ).all()
        confirmed_vendors = []
        for av in assigned_vendors:
            v = av.vendor
            if v:
                confirmed_vendors.append({
                    "vendor_id": v.id,
                    "name": v.name,
                    "category": av.category or v.category,
                    "status": av.status,
                    "contact_person": v.contact_person
                })

        # Payment Status
        stages = db.query(PaymentStage).filter(PaymentStage.project_id == project.id).order_by(PaymentStage.due_date.asc()).all()
        total_budget = project.estimated_budget or Decimal("0.00")
        paid_stages = [s for s in stages if s.status == "Paid"]
        total_paid = sum([Decimal(str(s.amount)) for s in paid_stages], Decimal("0.00"))
        balance_rem = max(total_budget - total_paid, Decimal("0.00"))

        # Final Costs & Extras
        approved_extras = db.query(WeddingExtra).filter(
            WeddingExtra.project_id == project.id,
            WeddingExtra.is_approved == True
        ).all()
        extras_total = sum([Decimal(str(e.client_amount)) for e in approved_extras], Decimal("0.00"))
        final_total_cost = total_budget + extras_total

        return {
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "wedding_date": project.wedding_date,
            "location": project.location,
            "guest_count": project.guest_count,
            "package_tier": project.package_tier,
            "events": functions,
            "live_schedule": live_schedule,
            "task_progress": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_percentage": completion_pct
            },
            "confirmed_vendors": confirmed_vendors,
            "payment_status": {
                "deposit_paid": project.deposit_paid,
                "total_budget": total_budget,
                "total_paid": total_paid,
                "balance_remaining": balance_rem,
                "stages": [PaymentStageResponse.model_validate(s) for s in stages]
            },
            "final_costs": {
                "base_budget": total_budget,
                "extras_total": extras_total,
                "final_total_cost": final_total_cost
            }
        }


project_service = ProjectService()
