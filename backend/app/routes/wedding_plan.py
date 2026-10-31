"""Phase 4 operational planning API. All records are scoped to their wedding project."""
from datetime import datetime, timezone
from uuid import uuid4
import json
from app.models.planning_resources import WeddingPlanningAudit
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.project import WeddingProject, WeddingFunction
from app.models.user import UserAccount
from app.models.wedding_plan import WeddingPlan, WeddingPlanTask
from app.schemas.wedding_plan import PlanUpdate, PlanResponse, TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(tags=['Wedding Planning'])

def project_or_404(db: Session, project_id: str):
    project = db.get(WeddingProject, project_id)
    if project is None or project.is_deleted:
        raise HTTPException(404, 'Wedding project not found')
    return project

def plan_for(db: Session, project_id: str):
    project_or_404(db, project_id)
    plan = db.query(WeddingPlan).filter(WeddingPlan.project_id == project_id).first()
    if plan is None:
        plan = WeddingPlan(id='WP-' + uuid4().hex[:20], project_id=project_id)
        db.add(plan)
        db.commit()
        db.refresh(plan)
    return plan

def check_refs(db: Session, project_id: str, data: dict):
    if data.get('function_id') is not None:
        function = db.get(WeddingFunction, data['function_id'])
        if function is None or function.project_id != project_id:
            raise HTTPException(422, 'Function must belong to this wedding project')
    for key in ('assigned_to', 'team_lead_id'):
        if data.get(key) is not None and db.get(UserAccount, data[key]) is None:
            raise HTTPException(422, f'Unknown staff account: {key}')

@router.get('/{project_id}/plan', response_model=PlanResponse)
def get_plan(project_id: str, db: Session = Depends(get_db)):
    return plan_for(db, project_id)

@router.patch('/{project_id}/plan', response_model=PlanResponse)
def update_plan(project_id: str, payload: PlanUpdate, db: Session = Depends(get_db)):
    plan = plan_for(db, project_id)
    changes = payload.model_dump(exclude_unset=True)
    check_refs(db, project_id, changes)
    for field, value in changes.items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan

@router.get('/{project_id}/plan/tasks', response_model=list[TaskResponse])
def list_tasks(project_id: str, db: Session = Depends(get_db)):
    plan = plan_for(db, project_id)
    return db.query(WeddingPlanTask).filter(WeddingPlanTask.plan_id == plan.id).order_by(WeddingPlanTask.created_at.desc()).all()

@router.post('/{project_id}/plan/tasks', response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(project_id: str, payload: TaskCreate, db: Session = Depends(get_db)):
    plan = plan_for(db, project_id)
    data = payload.model_dump()
    check_refs(db, project_id, data)
    if data['status'] == 'Completed':
        data['completed_at'] = datetime.now(timezone.utc)
    task = WeddingPlanTask(id='WT-' + uuid4().hex[:20], plan_id=plan.id, **data)
    db.add(task)
    db.add(WeddingPlanningAudit(id="AUD-" + uuid4().hex[:20], project_id=project_id, resource_type="tasks", record_id=task.id, action="CREATE", details=json.dumps(data, default=str)))
    db.commit()
    db.refresh(task)
    return task

def task_or_404(db: Session, project_id: str, task_id: str):
    plan = plan_for(db, project_id)
    task = db.query(WeddingPlanTask).filter(WeddingPlanTask.id == task_id, WeddingPlanTask.plan_id == plan.id).first()
    if task is None:
        raise HTTPException(404, 'Task not found in this wedding project')
    return task

@router.get('/{project_id}/plan/tasks/{task_id}', response_model=TaskResponse)
def get_task(project_id: str, task_id: str, db: Session = Depends(get_db)):
    return task_or_404(db, project_id, task_id)

@router.patch('/{project_id}/plan/tasks/{task_id}', response_model=TaskResponse)
def update_task(project_id: str, task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = task_or_404(db, project_id, task_id)
    changes = payload.model_dump(exclude_unset=True)
    check_refs(db, project_id, changes)
    for field, value in changes.items():
        setattr(task, field, value)
    if 'status' in changes:
        task.completed_at = datetime.now(timezone.utc) if task.status == 'Completed' else None
    db.add(WeddingPlanningAudit(id="AUD-" + uuid4().hex[:20], project_id=project_id, resource_type="tasks", record_id=task.id, action="UPDATE", details=json.dumps(changes, default=str)))
    db.commit()
    db.refresh(task)
    return task

@router.delete('/{project_id}/plan/tasks/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_task(project_id: str, task_id: str, db: Session = Depends(get_db)):
    task = task_or_404(db, project_id, task_id)
    db.add(WeddingPlanningAudit(id="AUD-" + uuid4().hex[:20], project_id=project_id, resource_type="tasks", record_id=task.id, action="DELETE", details=json.dumps({"title": task.title})))
    db.delete(task)
    db.commit()
