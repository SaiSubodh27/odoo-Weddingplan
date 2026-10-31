"""Phase 4 wedding resource models."""
from sqlalchemy import Column, String, Text, Integer, Numeric, Date, DateTime, ForeignKey, func
from app.database.base import Base

class WeddingBudgetAllocation(Base):
    __tablename__ = 'wedding_budget_allocations'
    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey('wedding_projects.id'), nullable=False, index=True)
    category = Column(String(80), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    notes = Column(Text)

class WeddingExpense(Base):
    __tablename__ = 'wedding_expenses'
    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey('wedding_projects.id'), nullable=False, index=True)
    category = Column(String(80), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    expense_date = Column(Date, nullable=False)
    notes = Column(Text)

class WeddingVendorAssignment(Base):
    __tablename__ = 'wedding_vendor_assignments'
    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey('wedding_projects.id'), nullable=False, index=True)
    function_id = Column(String(50), ForeignKey('wedding_functions.id'))
    vendor_id = Column(String(50), ForeignKey('vendors.id'), nullable=False)
    category = Column(String(80), nullable=False)
    responsibility = Column(Text)
    contract_amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String(40), nullable=False, default='Proposed')

class WeddingAccommodation(Base):
    __tablename__ = 'wedding_accommodations'
    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey('wedding_projects.id'), nullable=False, index=True)
    hotel_name = Column(String(255), nullable=False)
    room_type = Column(String(100), nullable=False)
    room_count = Column(Integer, nullable=False)
    nightly_rate = Column(Numeric(15, 2), nullable=False)
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    status = Column(String(40), nullable=False, default='Tentative')
    notes = Column(Text)

class WeddingLogistics(Base):
    __tablename__ = 'wedding_logistics'
    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey('wedding_projects.id'), nullable=False, index=True)
    function_id = Column(String(50), ForeignKey('wedding_functions.id'))
    service_type = Column(String(100), nullable=False)
    vehicle_type = Column(String(100), nullable=False)
    vehicle_count = Column(Integer, nullable=False)
    pickup_location = Column(String(255), nullable=False)
    dropoff_location = Column(String(255), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    driver_contact = Column(String(100))
    status = Column(String(40), nullable=False, default='Planned')
    notes = Column(Text)

class WeddingPlanningAudit(Base):
    __tablename__ = 'wedding_planning_audit'
    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey('wedding_projects.id'), nullable=False, index=True)
    resource_type = Column(String(80), nullable=False)
    record_id = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    actor = Column(String(100), nullable=False, default='Agency Staff')
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
