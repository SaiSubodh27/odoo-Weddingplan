import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

test_db_path = backend_dir / "test_royal_knot.db"
sqlite_url = f"sqlite:///{test_db_path.as_posix()}"
os.environ["DATABASE_URL"] = sqlite_url

from app.core.config import settings
settings.DATABASE_URL = sqlite_url

from app.database.base import Base
import app.models  # ensure all models are registered
import app.database.session as session_module
from app.database.session import get_db
from app.main import app

test_engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

session_module.engine = test_engine
session_module.SessionLocal = TestSessionLocal


@pytest.fixture(autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture(autouse=True)
def override_get_db():
    if get_db in app.dependency_overrides:
        yield
        return
    def _get_test_db():
        db = session_module.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = _get_test_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)

