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


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def override_get_db():
    def _get_test_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)
