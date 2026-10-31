"""Phase 4 operational wedding planning records."""
from sqlalchemy import Column, String, Integer, Text, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class WeddingPlan(Base):
    __tablename__ = "wedding_plans"
    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("wedding_projects.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    status = Column(String(30), nullable=False, default="Planning")
    planning_start_date = Column(Date, nullable=True)
    team_lead_id = Column(String(50), ForeignKey("user_accounts.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    project = relationship("WeddingProject", backref="wedding_plan", uselist=False)
    tasks = relationship("WeddingPlanTask", back_populates="plan", cascade="all, delete-orphan")


class WeddingPlanTask(Base):
    __tablename__ = "wedding_plan_tasks"
    id = Column(String(50), primary_key=True)
    plan_id = Column(String(50), ForeignKey("wedding_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    function_id = Column(String(50), ForeignKey("wedding_functions.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(80), nullable=False, default="General")
    priority = Column(String(20), nullable=False, default="Medium")
    status = Column(String(30), nullable=False, default="To Do")
    assigned_to = Column(String(50), ForeignKey("user_accounts.id", ondelete="SET NULL"), nullable=True)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    plan = relationship("WeddingPlan", back_populates="tasks")
