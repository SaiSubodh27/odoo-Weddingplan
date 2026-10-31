import uuid
from typing import Optional, List, Tuple
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func

from app.models.client import Client
from app.models.project import WeddingProject, WeddingFunction, ProjectMilestone, ProjectStatusHistory
from app.schemas.project import (
    WeddingProjectCreate,
    WeddingProjectUpdate,
    ProjectStatusUpdate,
    WeddingFunctionCreate,
    WeddingFunctionUpdate,
    ProjectMilestoneCreate,
    ProjectMilestoneUpdate,
    EligibleBookingResponse,
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
    # Functions Management
    # =====================================================================

    @staticmethod
    def add_function(db: Session, project_id: str, func_in: WeddingFunctionCreate) -> WeddingFunction:
        project = db.query(WeddingProject).filter(
            or_(WeddingProject.id == project_id, WeddingProject.project_code == project_id),
            WeddingProject.is_deleted == False
        ).first()

        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

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
            status=func_in.status
        )

        db.add(db_func)
        db.commit()
        db.refresh(db_func)
        return db_func

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


project_service = ProjectService()
