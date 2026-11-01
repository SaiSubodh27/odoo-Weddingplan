"""
Seed Four Distinct Personas and Interactive Data for The Royal Knot:
1. Principal Wedding Planner (Staff) - planner@theroyalknot.in
2. Agency Founder & Director (Founder) - founder@theroyalknot.com
3. Luxury Wedding Client (Couple) - aarav.meera@heritage-singhania.com
4. Luxury Vendor Partner (Vendor) - vendor@theroyalknot.com

Password for all four: RoyalKnot2026!
"""

import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# Ensure backend directory is in sys.path
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database.session import SessionLocal
from app.core.security import hash_password
from app.models import (
    UserAccount, Client, Enquiry, EnquiryNote,
    ServiceAgreement, AgreementPaymentMilestone,
    WeddingProject, WeddingFunction, PlanningTask, PaymentStage,
    TeamTimeEntry, BigDayScheduleEvent, WeddingExtra, VendorPayout,
    Vendor, CateringPlan, CateringMenuItem, CateringQuotation
)

def seed_four_personas():
    db = SessionLocal()
    default_hash = hash_password("RoyalKnot2026!")
    now = datetime.now(timezone.utc)

    print("==================================================")
    print("   SEEDING 4 LUXURY PERSONAS & MANIPULABLE DATA   ")
    print("==================================================")

    # ----------------------------------------------------
    # 1. PERSONA 1: PRINCIPAL WEDDING PLANNER (Staff)
    # ----------------------------------------------------
    planner_email = "planner@theroyalknot.in"
    planner_user = db.query(UserAccount).filter(UserAccount.email == planner_email).first()
    if not planner_user:
        planner_user = UserAccount(
            id="USR-STAFF-LEAD",
            email=planner_email,
            role="staff",
            hashed_password=default_hash,
            status="ACTIVE",
            is_active=True
        )
        db.add(planner_user)
        print(f" [+] Created Staff User: {planner_email}")
    else:
        planner_user.hashed_password = default_hash
        planner_user.is_active = True
        planner_user.status = "ACTIVE"
        print(f" [=] Updated Staff User: {planner_email}")

    # Also ensure Gayatri employee account is active
    gayatri = db.query(UserAccount).filter(UserAccount.email == "gayatri@theroyalknot.com").first()
    if gayatri:
        gayatri.hashed_password = default_hash
        gayatri.is_active = True
        gayatri.status = "ACTIVE"

    # Add rich enquiries for Planner to manipulate
    enquiry_data = [
        {
            "id": "ENQ-DEMO-01",
            "client_name": "Devendra & Shreya Singhal",
            "email": "devendra.shreya@singhal-industries.in",
            "phone": "+91 98290 55441",
            "wedding_date": date.today() + timedelta(days=90),
            "wedding_location": "Alila Fort Bishangarh, Jaipur",
            "expected_guest_count": 320,
            "estimated_budget": Decimal("28000000.00"),
            "status": "New",
            "enquiry_source": "Website",
            "requirements": "Heritage fortress wedding with illuminated ramparts, Rajasthani folk qawwali night, and silver plate banquet.",
        },
        {
            "id": "ENQ-DEMO-02",
            "client_name": "Rohan & Priyamvada Bhati",
            "email": "rohan.priyamvada@bhati-exports.com",
            "phone": "+91 98290 66552",
            "wedding_date": date.today() + timedelta(days=120),
            "wedding_location": "Jagmandir Island Palace, Udaipur",
            "expected_guest_count": 450,
            "estimated_budget": Decimal("42000000.00"),
            "status": "Consultation Scheduled",
            "enquiry_source": "Referral",
            "requirements": "Floating mandap over Lake Pichola, royal boat guest arrivals, bespoke drone light show over Lake Palace.",
        },
        {
            "id": "ENQ-DEMO-03",
            "client_name": "Dr. Aditya & Dr. Rhea Malviya",
            "email": "aditya.rhea@malviya-health.org",
            "phone": "+91 98290 77663",
            "wedding_date": date.today() + timedelta(days=150),
            "wedding_location": "Samode Palace, Jaipur",
            "expected_guest_count": 280,
            "estimated_budget": Decimal("22000000.00"),
            "status": "Proposal Sent",
            "enquiry_source": "Instagram Luxury",
            "requirements": "Sheesh Mahal royal mirror aesthetic, royal Sufi mehfil night, and authentic royal Mewari thali curation.",
        }
    ]

    for ed in enquiry_data:
        enq = db.query(Enquiry).filter(Enquiry.id == ed["id"]).first()
        if not enq:
            enq = Enquiry(**ed)
            db.add(enq)
            db.flush()
            db.add(EnquiryNote(
                enquiry_id=enq.id,
                author="Maharani Gayatri Singh",
                content="Initial consultation notes: Client requested dedicated palace suite block for VIP guests."
            ))
            print(f" [+] Seeded Planner Enquiry: {enq.id} ({enq.client_name})")

    # ----------------------------------------------------
    # 2. PERSONA 2: AGENCY FOUNDER (Founder)
    # ----------------------------------------------------
    founder_email = "founder@theroyalknot.com"
    founder_user = db.query(UserAccount).filter(UserAccount.email == founder_email).first()
    if not founder_user:
        founder_user = UserAccount(
            id="USR-FOUNDER-01",
            email=founder_email,
            role="founder",
            hashed_password=default_hash,
            status="ACTIVE",
            is_active=True
        )
        db.add(founder_user)
        print(f" [+] Created Founder User: {founder_email}")
    else:
        founder_user.hashed_password = default_hash
        founder_user.is_active = True
        founder_user.status = "ACTIVE"
        founder_user.role = "founder"
        print(f" [=] Updated Founder User: {founder_email}")

    # ----------------------------------------------------
    # 3. PERSONA 3: LUXURY WEDDING CLIENT (Couple)
    # ----------------------------------------------------
    client_email = "aarav.meera@heritage-singhania.com"
    hero_client = db.query(Client).filter(Client.email == client_email).first()
    if not hero_client:
        hero_client = Client(
            id="CL-HERO-001",
            partner1_name="Aarav Singhania",
            partner2_name="Meera Patel",
            email=client_email,
            phone="+91 98200 11223",
            wedding_date=date(2027, 2, 14),
            wedding_location="Taj Lake Palace & Jagmandir Island, Udaipur",
            expected_guest_count=400,
            estimated_budget=Decimal("35000000.00"),
            service_package="Full-Service Royal Production",
            status="Registered"
        )
        db.add(hero_client)
        db.flush()
        print(f" [+] Created Client Record: {hero_client.id}")
    else:
        hero_client.partner1_name = "Aarav Singhania"
        hero_client.partner2_name = "Meera Patel"
        hero_client.status = "Registered"

    client_user = db.query(UserAccount).filter(UserAccount.email == client_email).first()
    if not client_user:
        client_user = UserAccount(
            id="USR-HERO-COUPLE-01",
            email=client_email,
            role="client",
            client_id=hero_client.id,
            hashed_password=default_hash,
            status="ACTIVE",
            is_active=True
        )
        db.add(client_user)
        print(f" [+] Created Couple User: {client_email}")
    else:
        client_user.hashed_password = default_hash
        client_user.client_id = hero_client.id
        client_user.role = "client"
        client_user.is_active = True
        client_user.status = "ACTIVE"
        print(f" [=] Updated Couple User: {client_email}")

    # Ensure hero agreement is ready for OTP verification and digital signature
    hero_agr = db.query(ServiceAgreement).filter(ServiceAgreement.client_id == hero_client.id).first()
    if not hero_agr:
        hero_agr = ServiceAgreement(
            id="AGR-HERO-001",
            agreement_number="TRK-AGR-2027-HERO",
            client_id=hero_client.id,
            wedding_date=hero_client.wedding_date,
            wedding_location=hero_client.wedding_location,
            guest_count=hero_client.expected_guest_count,
            service_package="Full-Service Royal Production",
            package_price=Decimal("35000000.00"),
            tax_percentage=Decimal("18.00"),
            tax_amount=Decimal("6300000.00"),
            total_amount=Decimal("41300000.00"),
            currency="INR",
            status="PENDING_SIGNATURE",
            is_verified=False,
            signing_otp_verified=False,
            agreement_version="v1.0",
            current_version_number=1,
            is_internally_approved=True,
            approved_by="Maharani Gayatri Singh",
            approved_at=now
        )
        db.add(hero_agr)
        db.flush()

        # Add Milestones
        milestones = [
            ("Initial Booking Retainer (25%)", Decimal("25.00"), Decimal("10325000.00"), "Due upon contract signing"),
            ("Design & Palace Logistics Advance (40%)", Decimal("40.00"), Decimal("16520000.00"), "Due 60 days before celebration"),
            ("Final Execution & Vendor Balance (35%)", Decimal("35.00"), Decimal("14455000.00"), "Due 14 days before big day")
        ]
        for idx, (name, pct, amt, due_desc) in enumerate(milestones, start=1):
            db.add(AgreementPaymentMilestone(
                id=f"AGR-M-HERO-{idx:02d}",
                agreement_id=hero_agr.id,
                sequence_order=idx,
                milestone_name=name,
                percentage=pct,
                amount=amt,
                due_description=due_desc,
                status="PENDING"
            ))
        print(f" [+] Created Hero Agreement: {hero_agr.agreement_number} (Pending OTP & Signature)")

    # ----------------------------------------------------
    # 4. PERSONA 4: LUXURY VENDOR PARTNER (Vendor)
    # ----------------------------------------------------
    vendor_email = "vendor@theroyalknot.com"
    vendor_obj = db.query(Vendor).filter(Vendor.id == "VND-DEC-001").first()
    if not vendor_obj:
        vendor_obj = Vendor(
            id="VND-DEC-001",
            name="Rajwada Floral Couture",
            category="Decor & Design",
            city="Jaipur",
            phone="+91 98291 22001",
            contact_person="Ananya Singhania",
            email=vendor_email,
            rating=Decimal("4.9"),
            is_active=True
        )
        db.add(vendor_obj)
        db.flush()
        print(" [+] Created Premier Vendor Record: Rajwada Floral Couture")
    else:
        vendor_obj.email = vendor_email
        print(" [=] Linked Vendor: Rajwada Floral Couture")

    vendor_user = db.query(UserAccount).filter(UserAccount.email == vendor_email).first()
    if not vendor_user:
        vendor_user = UserAccount(
            id="USR-VND-DEMO-01",
            email=vendor_email,
            role="vendor",
            hashed_password=default_hash,
            status="ACTIVE",
            is_active=True
        )
        db.add(vendor_user)
        print(f" [+] Created Vendor User: {vendor_email}")
    else:
        vendor_user.hashed_password = default_hash
        vendor_user.role = "vendor"
        vendor_user.is_active = True
        vendor_user.status = "ACTIVE"
        print(f" [=] Updated Vendor User: {vendor_email}")

    # Commit all changes
    db.commit()
    db.close()
    print("\n[OK] All 4 Personas and interactive data successfully seeded into database!")

if __name__ == "__main__":
    seed_four_personas()
