"""Project-scoped operational resource CRUD and financial summary."""
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.planning_resources import WeddingBudgetAllocation, WeddingExpense, WeddingVendorAssignment, WeddingAccommodation, WeddingLogistics, WeddingPlanningAudit
from app.models.vendor import Vendor
from app.models.project import WeddingFunction
from app.models.catering import CateringPlan
from app.routes.wedding_plan import project_or_404

router = APIRouter(tags=['Wedding Planning Resources'])

class AllocationIn(BaseModel):
    category: str = Field(min_length=1, max_length=80)
    amount: Decimal = Field(ge=0)
    notes: str | None = None

class ExpenseIn(AllocationIn):
    description: str = Field(min_length=1, max_length=255)
    expense_date: date

class VendorIn(BaseModel):
    vendor_id: str
    function_id: str | None = None
    category: str
    responsibility: str | None = None
    contract_amount: Decimal = Field(ge=0)
    status: str = 'Proposed'

class AccommodationIn(BaseModel):
    hotel_name: str
    room_type: str
    room_count: int = Field(ge=0)
    nightly_rate: Decimal = Field(ge=0)
    check_in: date
    check_out: date
    status: str = 'Tentative'
    notes: str | None = None

class LogisticsIn(BaseModel):
    function_id: str | None = None
    service_type: str
    vehicle_type: str
    vehicle_count: int = Field(ge=1)
    pickup_location: str
    dropoff_location: str
    scheduled_at: datetime
    driver_contact: str | None = None
    status: str = 'Planned'
    notes: str | None = None

RESOURCES = {
    'allocations': (WeddingBudgetAllocation, AllocationIn),
    'expenses': (WeddingExpense, ExpenseIn),
    'vendors': (WeddingVendorAssignment, VendorIn),
    'accommodations': (WeddingAccommodation, AccommodationIn),
    'logistics': (WeddingLogistics, LogisticsIn),
}

def verify(db, project_id, values):
    if values.get('vendor_id') and db.get(Vendor, values['vendor_id']) is None:
        raise HTTPException(422, 'Vendor not found')
    if values.get('function_id'):
        function = db.get(WeddingFunction, values['function_id'])
        if function is None or function.project_id != project_id:
            raise HTTPException(422, 'Function does not belong to project')
    if 'check_in' in values and values['check_out'] <= values['check_in']:
        raise HTTPException(422, 'Check-out must be after check-in')

def audit(db, project_id, resource, record_id, action, details):
    db.add(WeddingPlanningAudit(id="AUD-" + uuid4().hex[:20], project_id=project_id, resource_type=resource, record_id=record_id, action=action, details=json.dumps(details, default=str)))

def to_dict(obj):
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}

@router.get('/{project_id}/planning/{resource}')
def list_resource(project_id: str, resource: str, db: Session = Depends(get_db)):
    project_or_404(db, project_id)
    if resource not in RESOURCES:
        raise HTTPException(404, 'Unknown planning resource')
    model, _ = RESOURCES[resource]
    return [to_dict(row) for row in db.query(model).filter(model.project_id == project_id).all()]

@router.post('/{project_id}/planning/{resource}', status_code=201)
def create_resource(project_id: str, resource: str, payload: dict, db: Session = Depends(get_db)):
    project_or_404(db, project_id)
    if resource not in RESOURCES:
        raise HTTPException(404, 'Unknown planning resource')
    model, schema = RESOURCES[resource]
    try:
        data = schema.model_validate(payload).model_dump()
    except ValidationError as exc:
        raise HTTPException(422, jsonable_encoder(exc.errors(include_url=False))) from exc
    verify(db, project_id, data)
    obj = model(id='PR-' + uuid4().hex[:20], project_id=project_id, **data)
    db.add(obj)
    audit(db, project_id, resource, obj.id, 'CREATE', data)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)

@router.patch('/{project_id}/planning/{resource}/{record_id}')
def update_resource(project_id: str, resource: str, record_id: str, payload: dict, db: Session = Depends(get_db)):
    project_or_404(db, project_id)
    if resource not in RESOURCES:
        raise HTTPException(404, 'Unknown planning resource')
    model, schema = RESOURCES[resource]
    obj = db.query(model).filter(model.id == record_id, model.project_id == project_id).first()
    if obj is None:
        raise HTTPException(404, 'Resource not found')
    try:
        data = schema.model_validate({**to_dict(obj), **payload}).model_dump()
    except ValidationError as exc:
        raise HTTPException(422, jsonable_encoder(exc.errors(include_url=False))) from exc
    verify(db, project_id, data)
    for key, value in data.items():
        setattr(obj, key, value)
    audit(db, project_id, resource, obj.id, 'UPDATE', payload)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)

@router.delete('/{project_id}/planning/{resource}/{record_id}', status_code=204)
def delete_resource(project_id: str, resource: str, record_id: str, db: Session = Depends(get_db)):
    project_or_404(db, project_id)
    if resource not in RESOURCES:
        raise HTTPException(404, 'Unknown planning resource')
    model, _ = RESOURCES[resource]
    obj = db.query(model).filter(model.id == record_id, model.project_id == project_id).first()
    if obj is None:
        raise HTTPException(404, 'Resource not found')
    audit(db, project_id, resource, obj.id, 'DELETE', to_dict(obj))
    db.delete(obj)
    db.commit()

@router.get('/{project_id}/planning-summary')
def planning_summary(project_id: str, db: Session = Depends(get_db)):
    project = project_or_404(db, project_id)
    def total(model, field):
        return db.query(func.coalesce(func.sum(field), 0)).filter(model.project_id == project_id).scalar() or Decimal(0)
    allocated = total(WeddingBudgetAllocation, WeddingBudgetAllocation.amount)
    spent = total(WeddingExpense, WeddingExpense.amount)
    vendor_commitments = db.query(func.coalesce(func.sum(WeddingVendorAssignment.contract_amount), 0)).filter(WeddingVendorAssignment.project_id == project_id, WeddingVendorAssignment.status.in_(['Confirmed', 'Contracted', 'Booked'])).scalar() or Decimal(0)
    catering_commitments = total(CateringPlan, CateringPlan.agreed_cost)
    committed = vendor_commitments + catering_commitments
    return {'project_id': project_id, 'estimated_budget': project.estimated_budget, 'allocated': allocated, 'spent': spent, 'committed': committed, 'remaining_budget': project.estimated_budget - spent, 'uncommitted_budget': project.estimated_budget - committed}

@router.get('/{project_id}/planning-audit')
def planning_audit(project_id: str, db: Session = Depends(get_db)):
    project_or_404(db, project_id)
    rows = db.query(WeddingPlanningAudit).filter(WeddingPlanningAudit.project_id == project_id).order_by(WeddingPlanningAudit.created_at.desc()).limit(250).all()
    return [to_dict(row) for row in rows]

@router.get('/{project_id}/planning-staff')
def planning_staff(project_id: str, db: Session = Depends(get_db)):
    from app.models.user import UserAccount
    project_or_404(db, project_id)
    staff = db.query(UserAccount).filter(UserAccount.role.in_(['staff', 'admin']), UserAccount.is_active == True).all()
    return [{'id': member.id, 'label': member.email, 'role': member.role} for member in staff]
