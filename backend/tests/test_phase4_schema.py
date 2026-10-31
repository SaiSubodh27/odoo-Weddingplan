"""Phase 4 schema smoke test, independent of the configured production database."""
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool
from app.models import Base


def test_phase4_tables_create_with_foreign_keys():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    assert {"wedding_plans", "wedding_plan_tasks"}.issubset(inspector.get_table_names())
    plan_columns = {column["name"] for column in inspector.get_columns("wedding_plans")}
    task_columns = {column["name"] for column in inspector.get_columns("wedding_plan_tasks")}
    assert {"project_id", "team_lead_id", "status"}.issubset(plan_columns)
    assert {"plan_id", "function_id", "assigned_to", "due_date", "priority"}.issubset(task_columns)
    engine.dispose()
