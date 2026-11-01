from sqlalchemy import Column, String, Integer, Text, Numeric, Date, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship, backref
from app.database.base import Base


class WeddingProject(Base):
    __tablename__ = "wedding_projects"

    id = Column(String(50), primary_key=True, index=True)
    project_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g. PRJ-2026-001

    # Client reference (1:1 confirmed client dossier -> wedding project)
    client_id = Column(String(50), ForeignKey("clients.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)

    # Future Phase 2 booking reference
    booking_id = Column(String(50), nullable=True, index=True)

    # Project Information
    project_name = Column(String(255), nullable=False)
    wedding_date = Column(Date, nullable=False)
    location = Column(String(255), nullable=False)
    guest_count = Column(Integer, nullable=False, default=100)
    estimated_budget = Column(Numeric(15, 2), nullable=False, default=0.00)
    package_tier = Column(String(50), nullable=False, default="Full-Service")
    project_manager_name = Column(String(100), nullable=False, default="Maharani Gayatri Singh")

    # Status: Planning, In Progress, On Hold, Completed, Cancelled
    status = Column(String(50), nullable=False, default="Planning", index=True)
    notes = Column(Text, nullable=True)

    # Booking Deposit State
    deposit_paid = Column(Boolean, nullable=False, default=False)
    deposit_paid_at = Column(DateTime(timezone=True), nullable=True)

    # Audit & Soft Delete
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    client = relationship("Client", backref=backref("wedding_project", uselist=False))
    functions = relationship("WeddingFunction", back_populates="project", cascade="all, delete-orphan", order_by="WeddingFunction.function_date")
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan", order_by="ProjectMilestone.due_date")
    status_history = relationship("ProjectStatusHistory", back_populates="project", cascade="all, delete-orphan", order_by="desc(ProjectStatusHistory.id)")
    catering_plans = relationship("CateringPlan", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("PlanningTask", back_populates="project", cascade="all, delete-orphan", order_by="PlanningTask.due_date")
    payment_stages = relationship("PaymentStage", back_populates="project", cascade="all, delete-orphan", order_by="PaymentStage.due_date")
    time_entries = relationship("TeamTimeEntry", back_populates="project", cascade="all, delete-orphan", order_by="desc(TeamTimeEntry.entry_date)")

    def __repr__(self):
        return f"<WeddingProject {self.project_code}: {self.project_name} ({self.status})>"


class WeddingFunction(Base):
    __tablename__ = "wedding_functions"

    id = Column(String(50), primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("wedding_projects.id", ondelete="CASCADE"), nullable=False, index=True)

    function_name = Column(String(100), nullable=False)  # e.g. Mehendi, Haldi, Sangeet, Wedding, Reception
    function_date = Column(Date, nullable=False)
    start_time = Column(String(20), nullable=True)  # e.g. "17:00"
    end_time = Column(String(20), nullable=True)    # e.g. "22:00"
    venue = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Scheduled")  # Scheduled, In Progress, Completed, Cancelled
    estimated_cost = Column(Numeric(15, 2), nullable=False, default=0.00)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("WeddingProject", back_populates="functions")

    def __repr__(self):
        return f"<WeddingFunction {self.id}: {self.function_name} ({self.function_date})>"


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(String(50), primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("wedding_projects.id", ondelete="CASCADE"), nullable=False, index=True)

    milestone_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="Pending")  # Pending, In Progress, Completed
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("WeddingProject", back_populates="milestones")

    def __repr__(self):
        return f"<ProjectMilestone {self.id}: {self.milestone_name} ({self.status})>"


class ProjectStatusHistory(Base):
    __tablename__ = "project_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(50), ForeignKey("wedding_projects.id", ondelete="CASCADE"), nullable=False, index=True)

    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(100), nullable=False, default="Agency Staff")
    notes = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("WeddingProject", back_populates="status_history")

    def __repr__(self):
        return f"<ProjectStatusHistory {self.id}: {self.old_status} -> {self.new_status} at {self.changed_at}>"


class ProjectVendor(Base):
    __tablename__ = "project_vendors"

    id = Column(String(50), primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("wedding_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(String(50), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)

    category = Column(String(50), nullable=False, default="Catering")
    contract_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    status = Column(String(50), nullable=False, default="Contracted")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("WeddingProject", backref=backref("assigned_vendors", cascade="all, delete-orphan"))
    vendor = relationship("Vendor", backref=backref("project_assignments", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ProjectVendor {self.id}: Vendor {self.vendor_id} on Project {self.project_id} ({self.status})>"


class PlanningTask(Base):
    __tablename__ = "planning_tasks"

    id = Column(String(50), primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("wedding_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    function_id = Column(String(50), ForeignKey("wedding_functions.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)  # Venue, Design, Vendors, Mehendi, Sangeet, Wedding Day, Reception
    stage = Column(String(50), nullable=False, default="To Plan", index=True)  # To Plan, In Progress, Review, Done
    assigned_to = Column(String(150), nullable=False, default="Maharani Gayatri Singh")
    priority = Column(String(50), nullable=False, default="Medium")
    due_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    is_completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("WeddingProject", back_populates="tasks")
    function = relationship("WeddingFunction")

    def __repr__(self):
        return f"<PlanningTask {self.id}: {self.title} [{self.stage}] ({self.assigned_to})>"


class PaymentStage(Base):
    __tablename__ = "payment_stages"

    id = Column(String(50), primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("wedding_projects.id", ondelete="CASCADE"), nullable=False, index=True)

    stage_name = Column(String(150), nullable=False)  # Retainer, Advance, Final
    percentage = Column(Numeric(5, 2), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    due_date = Column(Date, nullable=False)
    due_description = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="Pending")  # Pending, Paid, Overdue
    paid_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("WeddingProject", back_populates="payment_stages")

    def __repr__(self):
        return f"<PaymentStage {self.id}: {self.stage_name} ({self.amount} INR - {self.status})>"


class TeamTimeEntry(Base):
    __tablename__ = "team_time_entries"

    id = Column(String(50), primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("wedding_projects.id", ondelete="CASCADE"), nullable=False, index=True)

    employee_name = Column(String(150), nullable=False)
    role = Column(String(100), nullable=False, default="Wedding Planner")
    hours = Column(Numeric(6, 2), nullable=False)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    task_description = Column(Text, nullable=True)
    entry_date = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("WeddingProject", back_populates="time_entries")

    def __repr__(self):
        return f"<TeamTimeEntry {self.id}: {self.employee_name} ({self.hours}h @ {self.hourly_rate})>"
