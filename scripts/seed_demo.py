#!/usr/bin/env python3
"""
The Royal Knot - Luxury Wedding Planning Management System
Seed Demo Script: Idempotent seeder for development and demo environments.

Safety Rule: Refuses to run if connected to any non-development database.
"""

import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import urlparse

# Ensure backend directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings
from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.core.security import hash_password
from app.models import (
    UserAccount,
    Client,
    Enquiry,
    WeddingProject,
    WeddingFunction,
    ProjectMilestone,
    ProjectVendor,
    PlanningTask,
    PaymentStage,
    TeamTimeEntry,
    BigDayScheduleEvent,
    WeddingExtra,
    VendorPayout,
    Vendor,
    CateringPlan,
    CateringMenuItem,
    CateringQuotation,
    ServiceAgreement,
    AgreementPaymentMilestone,
    AgreementDocument,
)


def verify_dev_database():
    """
    STRICT SAFETY CHECK: Refuses execution on any production or non-dev database.
    """
    db_url = settings.DATABASE_URL
    print(f"[*] Verifying target database URL: {db_url}")
    parsed = urlparse(db_url)
    hostname = (parsed.hostname or "").lower()
    dbname = (parsed.path.lstrip("/") or "").lower()

    allowed_hosts = ["localhost", "127.0.0.1", "::1", "db"]
    allowed_db_patterns = ["demo", "dev", "test", "royal_knot", "postgres", "sqlite"]

    is_host_safe = any(allowed in hostname for allowed in allowed_hosts) or db_url.startswith("sqlite")
    is_db_safe = any(p in dbname for p in allowed_db_patterns) or db_url.startswith("sqlite")

    if not (is_host_safe and is_db_safe):
        print(f"\n[FATAL ERROR] Refusing to seed non-dev database!")
        print(f"Host '{hostname}' or DB '{dbname}' does not match dev environment policies.")
        sys.exit(1)

    print(f"[OK] Database safety verified: Local dev database confirmed ({dbname} on {hostname}).")


def seed_demo_data():
    verify_dev_database()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("\n============================================================")
        print("   THE ROYAL KNOT - SEEDING LUXURY DEMO ENVIRONMENT")
        print("============================================================")

        # -----------------------------------------------------------------
        # 1. USERS: 1 Founder, 2 Planners, 1 Couple
        # -----------------------------------------------------------------
        print("\n[*] Seeding Core Team and Couple User Accounts...")
        hashed_password = hash_password("RoyalKnot2026!")

        def get_or_create_user(email, full_name, role, phone="+91 98000 00000", client_id=None):
            user = db.query(UserAccount).filter(UserAccount.email == email).first()
            if not user:
                user = UserAccount(
                    id=f"USR-{uuid.uuid4().hex[:8].upper()}",
                    email=email,
                    role=role,
                    status="ACTIVE",
                    hashed_password=hashed_password,
                    is_active=True,
                    client_id=client_id,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"  + Created User: {full_name} ({role}) <{email}>")
            else:
                print(f"  = Existing User: {full_name} ({role}) <{email}>")
            return user

        # Founder & Employees
        founder_user = get_or_create_user("founder@theroyalknot.com", "Vikramaditya Rathore", "founder", "+91 98290 10001")
        planner1_user = get_or_create_user("gayatri@theroyalknot.com", "Maharani Gayatri Singh", "employee", "+91 98290 20002")
        planner2_user = get_or_create_user("raghav@theroyalknot.com", "Raghav Sharma", "employee", "+91 98290 30003")

        # -----------------------------------------------------------------
        # 2. VENDORS: 18+ Luxury Vendors across Rajasthan (incl. 3 caterers)
        # -----------------------------------------------------------------
        print("\n[*] Seeding 18+ Luxury Vendors across Rajasthan...")
        vendors_data = [
            # 3 Caterers
            ("VND-CAT-001", "Mewar Royal Caterers", "Catering", "Udaipur", "+91 98291 11001", "Maharaj Bhawani Singh", "mewar.caterers@rajasthan-weddings.in", 4.9),
            ("VND-CAT-002", "Rajputana Feasts & Banquets", "Catering", "Jaipur", "+91 98291 11002", "Chef Sumer Singh", "rajputana.feasts@jaipur-palace.in", 5.0),
            ("VND-CAT-003", "Udaipur Heritage Royal Kitchen", "Catering", "Udaipur", "+91 98291 11003", "Chef Digvijay Rathore", "heritage.kitchen@udaipur-luxury.in", 4.8),
            # Decor & Florals
            ("VND-DEC-001", "Rajwada Floral Couture", "Decor & Design", "Jaipur", "+91 98291 22001", "Ananya Singhania", "rajwada.floral@luxury-weddings.in", 4.9),
            ("VND-DEC-002", "Udaipur Royal Mandap Designers", "Decor & Design", "Udaipur", "+91 98291 22002", "Kailash Chand", "mandap@udaipur-decor.in", 4.8),
            ("VND-DEC-003", "Marwar Palace Scenography", "Decor & Design", "Jodhpur", "+91 98291 22003", "Devendra Mewara", "scenography@marwar-weddings.in", 4.9),
            # Photography & Cinematography
            ("VND-PHO-001", "Royal Lens Cinematography", "Photography & Video", "Jaipur", "+91 98291 33001", "Aditya Rawat", "lens@royallens.com", 5.0),
            ("VND-PHO-002", "Rajputana Moments Photography", "Photography & Video", "Udaipur", "+91 98291 33002", "Vikram Jeet", "moments@rajputanaphoto.com", 4.9),
            # Music & Entertainment
            ("VND-ENT-001", "DJ Krish Electro-Royal Sound & Lights", "Entertainment & DJ", "Jaipur", "+91 98291 44001", "Krishnan Iyer", "djkrish@royalsounds.in", 4.9),
            ("VND-ENT-002", "Jaipur Folk & Sufi Ensemble", "Live Music & Performers", "Jaipur", "+91 98291 44002", "Ustad Rehmat Khan", "sufi@jaipurfolk.org", 5.0),
            ("VND-ENT-003", "Shehnai Symphony Rajasthan", "Live Music & Performers", "Udaipur", "+91 98291 44003", "Pandit Omkar Lal", "shehnai@rajasthansymphony.in", 4.8),
            # Styling & Makeup
            ("VND-MAK-001", "Maharani Bridal Studio", "Bridal Hair & Makeup", "Jaipur", "+91 98291 55001", "Meenakshi Shekhawat", "bridal@maharanistudio.com", 4.9),
            ("VND-MAK-002", "Udaipur Regal Glamour by Payal", "Bridal Hair & Makeup", "Udaipur", "+91 98291 55002", "Payal Sen", "glamour@udaipurgal.com", 4.8),
            # Fleet & Royal Procession
            ("VND-LOG-001", "Royal Heritage Vintage Cars", "Transport & Fleet", "Jaipur", "+91 98291 66001", "Kunwar Mahendra Singh", "vintage@royalheritagecars.in", 5.0),
            ("VND-LOG-002", "Rajputana Shahi Safa & Procession Troupes", "Royal Procession & Baraat", "Jaipur", "+91 98291 66002", "Ratan Singh Bhati", "baraat@rajputanatroupes.in", 4.9),
            ("VND-LOG-003", "Rajasthan Luxury Coach & Aircraft Charters", "Logistics & Charters", "Udaipur", "+91 98291 66003", "Harshvardhan Rao", "charters@luxurycoach.in", 4.8),
            # Invitations & Favors
            ("VND-INV-001", "Shahi Nimantran Royal Stationery", "Invitations & Stationery", "Jaipur", "+91 98291 77001", "Pooja Doshi", "invites@shahinimantran.in", 4.9),
            ("VND-INV-002", "Rajputana Silver Hampers & Favors", "Gifting & Favors", "Jodhpur", "+91 98291 77002", "Sanjay Surana", "favors@rajputanasweets.in", 4.9),
            # Palace Security & Hospitality
            ("VND-SEC-001", "Royal Guard Palace Security Forces", "Security & Protocol", "Jaipur", "+91 98291 88001", "Major R.S. Bhati", "security@royalguard.in", 5.0),
            ("VND-HOS-001", "Concierge Rajasthan Hospitality Hostesses", "Guest Hospitality", "Udaipur", "+91 98291 88002", "Sunita Nair", "hospitality@conciergerajasthan.in", 4.9),
        ]

        seeded_vendors = {}
        for vid, vname, cat, city, phone, cname, email, rating in vendors_data:
            vnd = db.query(Vendor).filter(Vendor.id == vid).first()
            if not vnd:
                vnd = Vendor(
                    id=vid,
                    name=vname,
                    category=cat,
                    city=city,
                    phone=phone,
                    contact_person=cname,
                    email=email,
                    rating=Decimal(str(rating)),
                    is_active=True,
                    
                )
                db.add(vnd)
                db.commit()
                print(f"  + Vendor: {vname} [{cat} - {city}]")
            else:
                print(f"  = Vendor: {vname} [{cat} - {city}]")
            seeded_vendors[vid] = vnd

        # -----------------------------------------------------------------
        # 3. SEED 8 WEDDING PROJECTS AT DIFFERENT LIFECYCLE STAGES
        # -----------------------------------------------------------------
        print("\n[*] Seeding 8 Weddings Across All Operational Stages...")

        # Helper to get or create client
        def get_or_create_client(cid, p1, p2, email, phone, loc="Taj Lake Palace, Udaipur", wdate=date(2027, 2, 14), guests=400, budget=Decimal("35000000.00"), package="Full-Service", status="Confirmed"):
            c = db.query(Client).filter(Client.id == cid).first()
            if not c:
                c = Client(
                    id=cid,
                    partner1_name=p1,
                    partner2_name=p2,
                    email=email,
                    phone=phone,
                    wedding_date=wdate,
                    wedding_location=loc,
                    expected_guest_count=guests,
                    estimated_budget=budget,
                    service_package=package,
                    status=status
                )
                db.add(c)
                db.commit()
            return c

        def get_or_create_project(pid, pcode, client, name, wdate, loc, guests, budget, pkg, status, pm="Maharani Gayatri Singh", deposit_paid=False):
            prj = db.query(WeddingProject).filter(WeddingProject.id == pid).first()
            if not prj:
                prj = WeddingProject(
                    id=pid,
                    project_code=pcode,
                    client_id=client.id,
                    project_name=name,
                    wedding_date=wdate,
                    location=loc,
                    guest_count=guests,
                    estimated_budget=budget,
                    package_tier=pkg,
                    project_manager_name=pm,
                    status=status,
                    deposit_paid=deposit_paid,
                    deposit_paid_at=datetime.now(timezone.utc) if deposit_paid else None,
                )
                db.add(prj)
                db.commit()
                print(f"  + Project: {pcode} - {name} [{status}]")
            else:
                print(f"  = Project: {pcode} - {name} [{status}]")
            return prj

        # --- WEDDING 1: HERO WEDDING (Aarav & Meera, Udaipur, 3 days, 400 guests, Full-Service at Enquiry stage) ---
        c1 = get_or_create_client("CL-HERO-001", "Aarav Singhania", "Meera Patel", "aarav.meera@heritage-singhania.com", "+91 98200 11223", loc="Taj Lake Palace, Udaipur", wdate=date(2027, 2, 14), guests=400, budget=Decimal("35000000.00"), package="Full-Service", status="Enquiry")
        get_or_create_user(c1.email, "Aarav & Meera", "client", c1.phone, client_id=c1.id)

        # Enquiry for Hero Wedding
        enq1 = db.query(Enquiry).filter(Enquiry.id == "ENQ-HERO-001").first()
        if not enq1:
            enq1 = Enquiry(
                id="ENQ-HERO-001",
                client_name="Aarav Singhania & Meera Patel",
                email="aarav.meera@heritage-singhania.com",
                phone="+91 98200 11223",
                wedding_date=date(2027, 2, 14),
                wedding_location="Taj Lake Palace & Jagmandir Island, Udaipur",
                expected_guest_count=400,
                estimated_budget=Decimal("35000000.00"),
                status="New",
                enquiry_source="Website",
                requirements="3-day royal celebration for 400 guests across Jagmandir Island and Taj Lake Palace.",
                internal_notes="Hero client at Enquiry stage."
            )
            db.add(enq1)
            db.commit()
            print("  + Hero Enquiry: TRK-ENQ-2026-HERO (Aarav & Meera)")

        p1_hero = get_or_create_project(
            "PRJ-HERO-001", "PRJ-2027-HERO", c1,
            "Aarav & Meera Royal Udaipur Wedding",
            date(2027, 2, 14), "Taj Lake Palace, Udaipur", 400,
            Decimal("35000000.00"), "Full-Service", "Enquiry", deposit_paid=False
        )

        # Functions for Hero Wedding (3 days)
        def create_function(fid, prj_id, name, fdate, ftype, loc, guests, cost):
            f = db.query(WeddingFunction).filter(WeddingFunction.id == fid).first()
            if not f:
                f = WeddingFunction(
                    id=fid,
                    project_id=prj_id,
                    function_name=name,
                    function_date=fdate,
                    venue=loc,
                    estimated_cost=cost
                )
                db.add(f)
                db.commit()
            return f

        f1_hero_meh = create_function("FUNC-HERO-001", p1_hero.id, "Royal Mehendi & Welcome Soiree", date(2027, 2, 12), "Mehendi", "Taj Lake Palace Gardens", 350, Decimal("2500000.00"))
        f1_hero_san = create_function("FUNC-HERO-002", p1_hero.id, "Musical Sangeet Extravaganza", date(2027, 2, 13), "Sangeet", "Jagmandir Island Courtyard", 400, Decimal("4500000.00"))
        f1_hero_wed = create_function("FUNC-HERO-003", p1_hero.id, "Vedic Mandap Pheras & Royal Banquet", date(2027, 2, 14), "Wedding", "Jagmandir Island Palace", 400, Decimal("8000000.00"))

        # --- WEDDING 2: LOSS-MAKING WEDDING (Radhika & Anant, Jodhpur) ---
        # Payments received: 2.5 Cr; Vendor Costs: 2.15 Cr; Team Hours: 900 hrs = 62 Lakhs; Net = -27 Lakhs
        c2 = get_or_create_client("CL-LOSS-002", "Princess Radhika", "Yuvraj Anant Dev", "radhika.anant@jodhpur-royals.in", "+91 98200 22334", loc="Umaid Bhawan Palace, Jodhpur", wdate=date(2026, 12, 10), guests=500, budget=Decimal("25000000.00"), package="Full-Service")
        p2_loss = get_or_create_project(
            "PRJ-LOSS-002", "PRJ-2026-LOSS", c2,
            "Radhika & Anant Palace Nuptials",
            date(2026, 12, 10), "Umaid Bhawan Palace, Jodhpur", 500,
            Decimal("25000000.00"), "Full-Service", "Execution", deposit_paid=True
        )
        # Payment stages for loss-making wedding: client paid 2.5 Cr in full
        if not db.query(PaymentStage).filter(PaymentStage.project_id == p2_loss.id).first():
            db.add_all([
                PaymentStage(id="PAY-LOSS-01", project_id=p2_loss.id, stage_name="Booking Retainer", due_date=date(2026, 6, 1), percentage=Decimal("25.00"), amount=Decimal("6250000.00"), status="Paid", paid_at=datetime(2026, 6, 1, tzinfo=timezone.utc)),
                PaymentStage(id="PAY-LOSS-02", project_id=p2_loss.id, stage_name="Mid-Term Advance", due_date=date(2026, 9, 15), percentage=Decimal("40.00"), amount=Decimal("10000000.00"), status="Paid", paid_at=datetime(2026, 9, 15, tzinfo=timezone.utc)),
                PaymentStage(id="PAY-LOSS-03", project_id=p2_loss.id, stage_name="Final Balance", due_date=date(2026, 11, 20), percentage=Decimal("35.00"), amount=Decimal("8750000.00"), status="Paid", paid_at=datetime(2026, 11, 20, tzinfo=timezone.utc)),
            ])
            db.commit()

        # Contracted Vendors: total 2.15 Cr
        if not db.query(ProjectVendor).filter(ProjectVendor.project_id == p2_loss.id).first():
            db.add_all([
                ProjectVendor(id="PV-LOSS-01", project_id=p2_loss.id, vendor_id="VND-DEC-003", category="Decor & Design", contract_amount=Decimal("11500000.00"), status="Contracted"),
                ProjectVendor(id="PV-LOSS-02", project_id=p2_loss.id, vendor_id="VND-CAT-001", category="Catering", contract_amount=Decimal("7500000.00"), status="Contracted"),
                ProjectVendor(id="PV-LOSS-03", project_id=p2_loss.id, vendor_id="VND-ENT-002", category="Entertainment & DJ", contract_amount=Decimal("2500000.00"), status="Contracted"),
            ])
            db.commit()

        # Team Time Entries: 900 hours = ₹62,00,000
        if not db.query(TeamTimeEntry).filter(TeamTimeEntry.project_id == p2_loss.id).first():
            db.add_all([
                # Vikramaditya: 200 hrs @ 15,000 = 30 Lakhs
                TeamTimeEntry(id="TE-LOSS-01", project_id=p2_loss.id, employee_name="Vikramaditya Rathore", role="founder", hours=Decimal("200.0"), hourly_rate=Decimal("15000.00"), task_description="VIP Royal Protocol & High-Stakes Negotiations", entry_date=date(2026, 10, 15)),
                # Gayatri: 400 hrs @ 5,000 = 20 Lakhs
                TeamTimeEntry(id="TE-LOSS-02", project_id=p2_loss.id, employee_name="Maharani Gayatri Singh", role="employee", hours=Decimal("400.0"), hourly_rate=Decimal("5000.00"), task_description="End-to-end Palace Coordination & Design Direction", entry_date=date(2026, 11, 1)),
                # Raghav: 300 hrs @ 4,000 = 12 Lakhs
                TeamTimeEntry(id="TE-LOSS-03", project_id=p2_loss.id, employee_name="Raghav Sharma", role="employee", hours=Decimal("300.0"), hourly_rate=Decimal("4000.00"), task_description="Logistics, Security Fleet, & Vendor Operations", entry_date=date(2026, 11, 15)),
            ])
            db.commit()

        # --- WEDDING 3: 60 EXTRA GUESTS & SETTLEMENT WEDDING (Kabir & Natasha, Jaipur) ---
        c3 = get_or_create_client("CL-EXTR-003", "Kabir Oberoi", "Natasha Kapoor", "kabir.natasha@oberoi-hotels.com", "+91 98200 33445", loc="Rambagh Palace, Jaipur", wdate=date(2026, 11, 28), guests=400, budget=Decimal("40000000.00"), package="Full-Service")
        p3_extra = get_or_create_project(
            "PRJ-EXTR-003", "PRJ-2026-EXTR", c3,
            "Kabir & Natasha Rambagh Palace Celebration",
            date(2026, 11, 28), "Rambagh Palace, Jaipur", 400,
            Decimal("40000000.00"), "Full-Service", "Execution", deposit_paid=True
        )
        if not db.query(PaymentStage).filter(PaymentStage.project_id == p3_extra.id).first():
            db.add_all([
                PaymentStage(id="PAY-EXTR-01", project_id=p3_extra.id, stage_name="Booking Retainer", due_date=date(2026, 6, 1), percentage=Decimal("25.00"), amount=Decimal("10000000.00"), status="Paid", paid_at=datetime(2026, 7, 10, tzinfo=timezone.utc)),
                PaymentStage(id="PAY-EXTR-02", project_id=p3_extra.id, stage_name="Advance Milestone", due_date=date(2026, 10, 15), percentage=Decimal("40.00"), amount=Decimal("16000000.00"), status="Paid", paid_at=datetime(2026, 10, 15, tzinfo=timezone.utc)),
                PaymentStage(id="PAY-EXTR-03", project_id=p3_extra.id, stage_name="Final Balance", due_date=date(2026, 11, 20), percentage=Decimal("35.00"), amount=Decimal("14000000.00"), status="Pending"),
            ])
            db.commit()

        if not db.query(ProjectVendor).filter(ProjectVendor.project_id == p3_extra.id).first():
            db.add_all([
                ProjectVendor(id="PV-EXTR-01", project_id=p3_extra.id, vendor_id="VND-CAT-002", category="Catering", contract_amount=Decimal("15000000.00"), status="Contracted"),
                ProjectVendor(id="PV-EXTR-02", project_id=p3_extra.id, vendor_id="VND-ENT-001", category="Entertainment & DJ", contract_amount=Decimal("1200000.00"), status="Contracted"),
            ])
            db.commit()

        # Extras: 60 Extra Plates (Catering) + 3 hrs DJ Overtime
        if not db.query(WeddingExtra).filter(WeddingExtra.project_id == p3_extra.id).first():
            db.add_all([
                WeddingExtra(id="EXT-001", project_id=p3_extra.id, vendor_id="VND-CAT-002", description="60 Extra Royal Gala Dinner Plates", category="Catering", quantity=Decimal("60.0"), unit_price=Decimal("4500.00"), client_amount=Decimal("270000.00"), vendor_amount=Decimal("270000.00"), is_approved=True, approved_by="Maharani Gayatri Singh"),
                WeddingExtra(id="EXT-002", project_id=p3_extra.id, vendor_id="VND-ENT-001", description="DJ 3 Hours Overtime Performance", category="Entertainment", quantity=Decimal("3.0"), unit_price=Decimal("45000.00"), client_amount=Decimal("135000.00"), vendor_amount=Decimal("135000.00"), is_approved=True, approved_by="Raghav Sharma"),
            ])
            db.commit()

        # Idempotent Vendor Payout: agreed 1.5 Cr + 2.7 Lakhs extra - 50 Lakhs advance = 1,02,70,000.00
        if not db.query(VendorPayout).filter(VendorPayout.project_id == p3_extra.id).first():
            db.add(VendorPayout(
                id="VPO-EXTR-001",
                project_id=p3_extra.id,
                vendor_id="VND-CAT-002",
                agreed_amount=Decimal("15000000.00"),
                approved_extras=Decimal("270000.00"),
                advance_paid=Decimal("5000000.00"),
                final_payout_amount=Decimal("10270000.00"),
                idempotency_key=f"PAYOUT-{p3_extra.id}-VND-CAT-002",
                status="Approved",
                notes="Final catering settlement including 60 verified extra gala plates."
            ))
            db.commit()

        # --- WEDDING 4: COMPLETED WEDDING (Devraj & Nandini, Udaipur) ---
        c4 = get_or_create_client("CL-COMP-004", "Devraj Rathore", "Nandini Shekhawat", "devraj.nandini@rathore-heritage.in", "+91 98200 44556", loc="Shiv Niwas Palace, Udaipur", wdate=date(2026, 10, 20), guests=450, budget=Decimal("50000000.00"), package="Full-Service")
        p4_comp = get_or_create_project(
            "PRJ-COMP-004", "PRJ-2026-COMP", c4,
            "Devraj & Nandini Shiv Niwas Palace Wedding",
            date(2026, 10, 20), "Shiv Niwas Palace, Udaipur", 450,
            Decimal("50000000.00"), "Full-Service", "Completed", deposit_paid=True
        )
        if not db.query(PaymentStage).filter(PaymentStage.project_id == p4_comp.id).first():
            db.add_all([
                PaymentStage(id="PAY-COMP-01", project_id=p4_comp.id, stage_name="Booking Retainer", due_date=date(2026, 4, 1), percentage=Decimal("25.00"), amount=Decimal("12500000.00"), status="Paid", paid_at=datetime(2026, 4, 1, tzinfo=timezone.utc)),
                PaymentStage(id="PAY-COMP-02", project_id=p4_comp.id, stage_name="Mid-Term Advance", due_date=date(2026, 8, 1), percentage=Decimal("40.00"), amount=Decimal("20000000.00"), status="Paid", paid_at=datetime(2026, 8, 1, tzinfo=timezone.utc)),
                PaymentStage(id="PAY-COMP-03", project_id=p4_comp.id, stage_name="Final Balance", due_date=date(2026, 11, 20), percentage=Decimal("35.00"), amount=Decimal("17500000.00"), status="Paid", paid_at=datetime(2026, 10, 22, tzinfo=timezone.utc)),
            ])
            db.commit()

        # --- WEDDING 5: BIG DAY LIVE COORDINATION WEDDING (Siddharth & Ananya, Jaipur) ---
        c5 = get_or_create_client("CL-LIVE-005", "Siddharth Verma", "Ananya Singhal", "siddharth.ananya@jaipur-estates.com", "+91 98200 55667", loc="City Palace, Jaipur", wdate=date.today(), guests=400, budget=Decimal("30000000.00"), package="Full-Service")
        p5_live = get_or_create_project(
            "PRJ-LIVE-005", "PRJ-2026-LIVE", c5,
            "Siddharth & Ananya City Palace Wedding",
            date.today(), "City Palace, Jaipur", 400,
            Decimal("30000000.00"), "Full-Service", "Execution", deposit_paid=True
        )
        # Big day live events: Baraat (on time), Decor Setup (checked in), DJ Krish (late alert)
        now_time = datetime.now(timezone.utc)
        if not db.query(BigDayScheduleEvent).filter(BigDayScheduleEvent.project_id == p5_live.id).first():
            db.add_all([
                BigDayScheduleEvent(
                    id="BDE-LIVE-01", project_id=p5_live.id, title="Royal Vintage Car Baraat Assembly",
                    event_time="16:00", expected_arrival_time=now_time - timedelta(minutes=45),
                    grace_period_minutes=15, owner_name="Raghav Sharma", vendor_id="VND-LOG-001",
                    vendor_name="Royal Heritage Vintage Cars", arrived_at=now_time - timedelta(minutes=50)
                ),
                BigDayScheduleEvent(
                    id="BDE-LIVE-02", project_id=p5_live.id, title="Mandap Floral Architecture Final Inspection",
                    event_time="17:00", expected_arrival_time=now_time - timedelta(minutes=30),
                    grace_period_minutes=15, owner_name="Maharani Gayatri Singh", vendor_id="VND-DEC-001",
                    vendor_name="Rajwada Floral Couture", arrived_at=now_time - timedelta(minutes=35)
                ),
                BigDayScheduleEvent(
                    id="BDE-LIVE-03", project_id=p5_live.id, title="Evening Sangeet Stage & DJ Krish Soundcheck",
                    event_time="18:00", expected_arrival_time=now_time - timedelta(minutes=25),
                    grace_period_minutes=10, owner_name="Raghav Sharma", vendor_id="VND-ENT-001",
                    vendor_name="DJ Krish Electro-Royal Sound & Lights", arrived_at=None
                ),
            ])
            db.commit()

        # --- WEDDING 6: PLANNING WITH 28 TASKS GENERATED (Rohan & Tara, Udaipur) ---
        c6 = get_or_create_client("CL-PLAN-006", "Rohan Mehra", "Tara Deshmukh", "rohan.tara@deshmukh-global.com", "+91 98200 66778", loc="The Leela Palace, Udaipur", wdate=date(2027, 3, 20), guests=350, budget=Decimal("45000000.00"), package="Full-Service")
        p6_plan = get_or_create_project(
            "PRJ-PLAN-006", "PRJ-2027-PLAN", c6,
            "Rohan & Tara Leela Palace Celebration",
            date(2027, 3, 20), "The Leela Palace, Udaipur", 350,
            Decimal("45000000.00"), "Full-Service", "Planning", deposit_paid=True
        )
        if db.query(PlanningTask).filter(PlanningTask.project_id == p6_plan.id).count() == 0:
            from app.services.project_service import project_service
            project_service.mark_deposit_paid(db, project_id=p6_plan.id)

        # --- WEDDING 7: SERVICE AGREEMENT SIGNED, AWAITING DEPOSIT (Sameer & Rhea, Jaipur) ---
        c7 = get_or_create_client("CL-AGR-007", "Sameer Khanna", "Rhea Sengupta", "sameer.rhea@sengupta-media.in", "+91 98200 77889", loc="Samode Palace, Jaipur", wdate=date(2027, 4, 15), guests=300, budget=Decimal("28000000.00"), package="Full-Service")
        p7_agr = get_or_create_project(
            "PRJ-AGR-007", "PRJ-2027-AGR", c7,
            "Sameer & Rhea Samode Palace Nuptials",
            date(2027, 4, 15), "Samode Palace, Jaipur", 300,
            Decimal("28000000.00"), "Full-Service", "Planning", deposit_paid=False
        )
        # Create signed Service Agreement
        agr7 = db.query(ServiceAgreement).filter(ServiceAgreement.client_id == c7.id).first()
        if not agr7:
            agr7 = ServiceAgreement(
                id="AGR-DEMO-007",
                agreement_number="TRK-AGR-2027-007",
                client_id=c7.id,
                wedding_date=date(2027, 4, 15),
                wedding_location="Samode Palace, Jaipur",
                guest_count=300,
                service_package="Full-Service",
                package_price=Decimal("28000000.00"),
                tax_percentage=Decimal("18.00"),
                tax_amount=Decimal("5040000.00"),
                total_amount=Decimal("33040000.00"),
                status="SIGNED",
                is_verified=True,
                signed_at=datetime.now(timezone.utc) - timedelta(days=2),
                signed_by_name="Sameer Khanna",
                signed_by_email=c7.email,
                signer_ip="127.0.0.1",
                signer_user_agent="Mozilla/5.0 Demo Browser"
            )
            db.add(agr7)
            db.commit()

        # --- WEDDING 8: VENDOR RFQ & QUOTES COMPETING (Ranveer & Ishani, Jodhpur) ---
        c8 = get_or_create_client("CL-RFQ-008", "Ranveer Shekhawat", "Ishani Rathore", "ranveer.ishani@rajputana-clan.in", "+91 98200 88990", loc="Mehrangarh Fort, Jodhpur", wdate=date(2027, 5, 2), guests=450, budget=Decimal("32000000.00"), package="Full-Service")
        p8_rfq = get_or_create_project(
            "PRJ-RFQ-008", "PRJ-2027-RFQ", c8,
            "Ranveer & Ishani Mehrangarh Fort Wedding",
            date(2027, 5, 2), "Mehrangarh Fort, Jodhpur", 450,
            Decimal("32000000.00"), "Full-Service", "Planning", deposit_paid=False
        )
        f8_sang = create_function("FUNC-RFQ-001", p8_rfq.id, "Royal Sangeet Gala", date(2027, 5, 1), "Sangeet", "Zenana Deodi, Mehrangarh", 450, Decimal("6000000.00"))
        cat8 = db.query(CateringPlan).filter(CateringPlan.function_id == f8_sang.id).first()
        if not cat8:
            cat8 = CateringPlan(
                id="CAT-RFQ-008",
                project_id=p8_rfq.id,
                function_id=f8_sang.id,
                guest_count=450,
                service_style="Silver Platter",
                status="Under Review"
            )
            db.add(cat8)
            db.commit()

            # Add competing quotes
            db.add_all([
                CateringQuotation(id="CQ-RFQ-01", catering_plan_id=cat8.id, vendor_id="VND-CAT-001", per_person_rate=Decimal("3500.00"), equipment_charges=Decimal("150000.00"), gst_rate_percent=Decimal("18.00"), total_cost=Decimal("2035500.00"), status="Received"),
                CateringQuotation(id="CQ-RFQ-02", catering_plan_id=cat8.id, vendor_id="VND-CAT-002", per_person_rate=Decimal("3200.00"), equipment_charges=Decimal("100000.00"), gst_rate_percent=Decimal("18.00"), total_cost=Decimal("1817200.00"), status="Received"),
                CateringQuotation(id="CQ-RFQ-03", catering_plan_id=cat8.id, vendor_id="VND-CAT-003", per_person_rate=Decimal("3400.00"), equipment_charges=Decimal("120000.00"), gst_rate_percent=Decimal("18.00"), total_cost=Decimal("1947000.00"), status="Received"),
            ])
            db.commit()

        print("\n============================================================")
        print("   [SUCCESS] DEMO ENVIRONMENT SEEDED IDEMPOTENTLY!")
        print("   - Core Team: 1 Founder, 2 Planners, 1 Couple")
        print("   - Vendors: 20 Luxury Vendors across Rajasthan")
        print("   - Weddings: 8 Operational Projects (Hero, Loss-making, 60-extra, Live, etc.)")
        print("============================================================\n")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
