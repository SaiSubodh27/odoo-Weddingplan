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

    # Audit & Soft Delete
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    client = relationship("Client", backref=backref("wedding_project", uselist=False))
    functions = relationship("WeddingFunction", back_populates="project", cascade="all, delete-orphan", order_by="WeddingFunction.function_date")
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan", order_by="ProjectMilestone.due_date")
    status_history = relationship("ProjectStatusHistory", back_populates="project", cascade="all, delete-orphan", order_by="desc(ProjectStatusHistory.id)")

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
