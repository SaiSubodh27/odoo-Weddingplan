"""Seed script for Phase 3 live demonstration and testing."""
import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.database.base import Base
import app.models  # noqa: F401
from app.database.session import engine, SessionLocal
from app.models.client import Client
from app.schemas.project import WeddingProjectCreate, WeddingFunctionCreate, ProjectMilestoneUpdate
from app.services.project_service import project_service


def seed():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_client = db.query(Client).filter(Client.id == "CL-2026-001").first()
        if existing_client:
            print("Database already contains seed data.")
            return

        print("Seeding clients...")
        # 1. Client with active Project
        c1 = Client(
            id="CL-2026-001",
            partner1_name="Aanya Singhania",
            partner2_name="Kabir Oberoi",
            email="aanya.oberoi@example.com",
            phone="+91 98201 12345",
            wedding_date=date(2026, 12, 18),
            wedding_location="The Leela Palace, Udaipur",
            expected_guest_count=350,
            estimated_budget=Decimal("15000000.00"),
            service_package="Royal Bespoke",
            wedding_theme="Mewari Royal Heritage",
            status="Confirmed",
            notes="VIP family from Mumbai. Destination wedding at Lake Pichola.",
        )
        db.add(c1)

        # 2. Confirmed client ready to create a project via the UI modal
        c2 = Client(
            id="CL-2026-002",
            partner1_name="Rhea Kapoor",
            partner2_name="Devrat Mehta",
            email="rhea.devrat@example.com",
            phone="+91 98111 67890",
            wedding_date=date(2027, 2, 22),
            wedding_location="Rambagh Palace, Jaipur",
            expected_guest_count=450,
            estimated_budget=Decimal("25000000.00"),
            service_package="Imperial Grande",
            wedding_theme="Rajputana Grandeur",
            status="Confirmed",
            notes="Requires 3 days exclusive palace buyout and royal procession with vintage cars.",
        )
        db.add(c2)

        # 3. Third confirmed client
        c3 = Client(
            id="CL-2026-003",
            partner1_name="Meera Joshi",
            partner2_name="Arjun Rathore",
            email="meera.arjun@example.com",
            phone="+91 97000 54321",
            wedding_date=date(2026, 11, 28),
            wedding_location="Samode Palace, Jaipur",
            expected_guest_count=200,
            estimated_budget=Decimal("9500000.00"),
            service_package="Heritage Classic",
            wedding_theme="Boho Royal Fusion",
            status="Confirmed",
            notes="Intimate royal celebration with traditional folk musicians.",
        )
        db.add(c3)
        db.commit()

        print("Creating wedding project for Client 1 using project_service...")
        project = project_service.create_project(
            db=db,
            project_in=WeddingProjectCreate(
                client_id="CL-2026-001",
                project_name="The Oberoi & Singhania Royal Lake Wedding",
                project_manager_name="Gayatri Devi",
                notes="Multi-day destination wedding at Lake Pichola, Udaipur."
            )
        )

        print(f"Project created with code: {project.project_code}")

        # Add functions to the project
        print("Adding wedding functions...")
        project_service.add_function(
            db=db,
            project_id=project.id,
            func_in=WeddingFunctionCreate(
                functionName="Mehendi & Welcome Lunch",
                functionDate=date(2026, 12, 17),
                startTime="11:30",
                endTime="16:00",
                venue="The Guava Garden, The Leela Palace",
                description="Live bangle making counters, traditional ghoomar troupe and Rajasthani lunch.",
                status="Scheduled"
            )
        )
        project_service.add_function(
            db=db,
            project_id=project.id,
            func_in=WeddingFunctionCreate(
                functionName="Royal Sangeet & Cocktail Soiree",
                functionDate=date(2026, 12, 17),
                startTime="19:30",
                endTime="02:00",
                venue="Grand Ballroom & Courtyard, The Leela Palace",
                description="Celebrity DJ, 360-degree LED visual stage, curated mixology bar.",
                status="Scheduled"
            )
        )
        project_service.add_function(
            db=db,
            project_id=project.id,
            func_in=WeddingFunctionCreate(
                functionName="Haldi & Phoolon Ki Holi",
                functionDate=date(2026, 12, 18),
                startTime="10:00",
                endTime="13:00",
                venue="Lakeside Poolside Promenade",
                description="Organic turmeric cones, 500kg Marigold & Rose petal shower.",
                status="Scheduled"
            )
        )
        project_service.add_function(
            db=db,
            project_id=project.id,
            func_in=WeddingFunctionCreate(
                functionName="Royal Pheras & Gala Dinner",
                functionDate=date(2026, 12, 18),
                startTime="17:30",
                endTime="23:30",
                venue="Mewar Terrace Floating Mandap, Lake Pichola",
                description="Floating lotus mandap over Lake Pichola with fireworks symphony.",
                status="Scheduled"
            )
        )

        # Complete first 2 auto-seeded milestones
        if project.milestones and len(project.milestones) >= 2:
            print("Updating sample milestones to completed status...")
            project_service.update_milestone(
                db=db,
                project_id=project.id,
                ms_id=project.milestones[0].id,
                ms_in=ProjectMilestoneUpdate(status="Completed")
            )
            project_service.update_milestone(
                db=db,
                project_id=project.id,
                ms_id=project.milestones[1].id,
                ms_in=ProjectMilestoneUpdate(status="Completed")
            )

        print("Seed completed successfully!")
        print(f"Created project: {project.project_code} ({project.project_name})")
        print("Ready for live testing and demonstration!")
    except Exception as e:
        db.rollback()
        print(f"Error during seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
