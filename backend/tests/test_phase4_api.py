"""Route registration, project isolation, and validation tests for Phase 4."""
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.wedding_plan import TaskCreate
from app.routes.planning_resources import AccommodationIn, AllocationIn, LogisticsIn
from pydantic import ValidationError
import pytest

client = TestClient(app)

def test_phase4_routes_are_registered():
    paths = app.openapi()['paths']
    assert '/api/v1/projects/{project_id}/plan/tasks' in paths
    assert '/api/v1/projects/{project_id}/planning/{resource}' in paths
    assert '/api/v1/projects/{project_id}/planning-summary' in paths

def test_missing_project_cannot_access_resources():
    assert client.get('/api/v1/projects/missing/plan').status_code == 404
    assert client.get('/api/v1/projects/missing/planning/expenses').status_code == 404
    assert client.get('/api/v1/projects/missing/planning-summary').status_code == 404

def test_task_priority_is_validated():
    with pytest.raises(ValidationError):
        TaskCreate(title='Book photographer', priority='Invalid')

def test_money_and_vehicle_count_cannot_be_negative():
    with pytest.raises(ValidationError):
        AllocationIn(category='Decor', amount=-10)
    with pytest.raises(ValidationError):
        LogisticsIn(service_type='Transfer', vehicle_type='Car', vehicle_count=0, pickup_location='Airport', dropoff_location='Hotel', scheduled_at='2026-11-10T10:00:00')

def test_project_scoped_crud_and_budget_summary():
    from datetime import date
    from uuid import uuid4
    from decimal import Decimal
    from app.models.client import Client
    from app.models.project import WeddingProject
    from conftest import TestSessionLocal
    unique = uuid4().hex[:10]
    project_id = 'p-' + unique
    with TestSessionLocal() as db:
        db.add(Client(id='c-' + unique, partner1_name='A', partner2_name='B', email=unique + '@example.com', phone='000', wedding_date=date(2027,1,5), wedding_location='Jaipur'))
        db.flush()
        db.add(WeddingProject(id=project_id, project_code='PR-' + unique, client_id='c-' + unique, project_name='Test Wedding', wedding_date=date(2027,1,5), location='Jaipur', guest_count=100, estimated_budget=Decimal('10000.00')))
        db.commit()
    root = '/api/v1/projects/' + project_id
    task = client.post(root + '/plan/tasks', json={'title':'Confirm venue', 'priority':'High'})
    assert task.status_code == 201, task.text
    task_id = task.json()['id']
    assert client.patch(root + '/plan/tasks/' + task_id, json={'status':'Completed'}).json()['completed_at'] is not None
    allocation = client.post(root + '/planning/allocations', json={'category':'Venue','amount':'5000'})
    assert allocation.status_code == 201, allocation.text
    expense = client.post(root + '/planning/expenses', json={'category':'Venue','description':'Deposit','amount':'1500','expense_date':'2026-11-01'})
    assert expense.status_code == 201, expense.text
    summary = client.get(root + '/planning-summary')
    assert summary.status_code == 200, summary.text
    assert float(summary.json()['allocated']) == 5000
    assert float(summary.json()['spent']) == 1500
    assert float(summary.json()['remaining_budget']) == 8500
    assert client.delete(root + '/plan/tasks/' + task_id).status_code == 204
    assert client.delete(root + '/planning/expenses/' + expense.json()['id']).status_code == 204

def test_vendor_accommodation_logistics_and_cross_project_isolation():
    from datetime import date
    from uuid import uuid4
    from app.models.client import Client
    from app.models.project import WeddingProject
    from app.models.vendor import Vendor
    from conftest import TestSessionLocal
    key = uuid4().hex[:10]
    project_id, vendor_id = 'p-' + key, 'v-' + key
    with TestSessionLocal() as db:
        db.add(Client(id='c-' + key, partner1_name='A', partner2_name='B', email=key+'@example.com', phone='000', wedding_date=date(2027,1,5), wedding_location='Jaipur'))
        db.flush()
        db.add(WeddingProject(id=project_id, project_code='PR-'+key, client_id='c-'+key, project_name='Test', wedding_date=date(2027,1,5), location='Jaipur', estimated_budget=10000))
        db.add(Vendor(id=vendor_id, name='Photographer', category='Photography', phone='1234567890'))
        db.commit()
    root = '/api/v1/projects/' + project_id
    cases = {
        'vendors': {'vendor_id':vendor_id,'category':'Photography','contract_amount':'500','status':'Confirmed'},
        'accommodations': {'hotel_name':'Palace','room_type':'Suite','room_count':2,'nightly_rate':'300','check_in':'2027-01-04','check_out':'2027-01-07'},
        'logistics': {'service_type':'Airport transfer','vehicle_type':'SUV','vehicle_count':2,'pickup_location':'Airport','dropoff_location':'Palace','scheduled_at':'2027-01-04T09:00:00'},
    }
    for resource, data in cases.items():
        created = client.post(root + '/planning/' + resource, json=data)
        assert created.status_code == 201, created.text
        record_id = created.json()['id']
        assert len(client.get(root + '/planning/' + resource).json()) == 1
        assert client.patch(root + '/planning/' + resource + '/' + record_id, json={'notes':'Checked'} if resource != 'vendors' else {'responsibility':'Photo team'}).status_code == 200
        assert client.patch('/api/v1/projects/other/planning/' + resource + '/' + record_id, json={'status':'Changed'}).status_code == 404
        assert client.delete(root + '/planning/' + resource + '/' + record_id).status_code == 204
    assert client.post(root + '/planning/allocations', json={'category':'Venue','amount':-1}).status_code == 422
    audit = client.get(root + '/planning-audit')
    assert audit.status_code == 200
    assert len(audit.json()) >= 9

def test_function_guest_override_and_milestone_fields():
    from datetime import date
    from uuid import uuid4
    from app.models.client import Client
    from app.models.project import WeddingProject
    from conftest import TestSessionLocal
    key = uuid4().hex[:10]
    with TestSessionLocal() as db:
        db.add(Client(id='c-'+key, partner1_name='A', partner2_name='B', email=key+'@example.com', phone='000', wedding_date=date(2027,1,5), wedding_location='Jaipur'))
        db.flush()
        db.add(WeddingProject(id='p-'+key, project_code='PR-'+key, client_id='c-'+key, project_name='Test', wedding_date=date(2027,1,5), location='Jaipur', estimated_budget=10000))
        db.commit()
    root = '/api/v1/projects/p-' + key
    created = client.post(root + '/functions', json={'functionName':'Sangeet','functionDate':'2027-01-04','guestCountOverride':125,'eventNotes':'Outdoor stage'})
    assert created.status_code == 201, created.text
    assert created.json()['guestCountOverride'] == 125
    function_id = created.json()['id']
    changed = client.put(root + '/functions/' + function_id, json={'guestCountOverride':150})
    assert changed.status_code in (200, 204), changed.text
    milestone = client.post(root + '/milestones', json={'milestoneName':'Confirm venue','dueDate':'2027-01-02','category':'Venue','functionId':function_id})
    assert milestone.status_code == 201, milestone.text
    assert milestone.json()['category'] == 'Venue'
