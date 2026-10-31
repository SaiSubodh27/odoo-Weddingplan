"""Validated request/response schemas for Phase 4 wedding plans and tasks."""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

PlanStatus = Literal['Draft', 'Planning', 'In Progress', 'Ready for Execution', 'Completed', 'Cancelled']
TaskStatus = Literal['To Do', 'In Progress', 'Blocked', 'Completed', 'Cancelled']
TaskPriority = Literal['Low', 'Medium', 'High', 'Critical']

class PlanUpdate(BaseModel):
    status: PlanStatus | None = None
    planning_start_date: date | None = None
    team_lead_id: str | None = None

class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    status: str
    planning_start_date: date | None
    team_lead_id: str | None
    created_at: datetime
    updated_at: datetime

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    function_id: str | None = None
    category: str = Field(default='General', min_length=1, max_length=80)
    priority: TaskPriority = 'Medium'
    status: TaskStatus = 'To Do'
    assigned_to: str | None = None
    due_date: date | None = None

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    function_id: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=80)
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    assigned_to: str | None = None
    due_date: date | None = None

class TaskResponse(TaskCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    plan_id: str
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
