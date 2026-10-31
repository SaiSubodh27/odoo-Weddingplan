import sys
from pathlib import Path
from datetime import datetime, timezone, date
from decimal import Decimal

# Ensure backend path is on sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models.client import Client
from app.models.enquiry import Enquiry, EnquiryNote
from app.models.document import RegistrationDocument
from app.models.registration import ClientRegistration
from app.models.user import UserAccount, ActivationToken
from app.models.email_message import EmailMessage, EmailAttachment

db = SessionLocal()

print("=" * 60)
print("PURGING FAKE DATA — KEEPING ONLY REAL CLIENT & AGENCY DATA")
print("=" * 60)

real_emails = ["saisubodh618@gmail.com", "saisubodh6@gmail.com"]

# 1. Identify real enquiry IDs
real_enquiries = db.query(Enquiry).filter(Enquiry.email.in_(real_emails)).all()
real_enq_ids = [e.id for e in real_enquiries]
print(f"Real Enquiries identified: {real_enq_ids}")

# 2. Delete EmailAttachments for fake email messages
fake_emails = db.query(EmailMessage).filter(
    ~EmailMessage.recipient_email.in_(real_emails),
    ~EmailMessage.sender_email.in_(real_emails)
).all()
fake_msg_ids = [m.id for m in fake_emails]
att_deleted = db.query(EmailAttachment).filter(EmailAttachment.email_message_id.in_(fake_msg_ids)).delete(synchronize_session=False)
print(f"Deleted {att_deleted} attachments of fake emails.")

# 3. Delete fake EmailMessages
emails_deleted = db.query(EmailMessage).filter(EmailMessage.id.in_(fake_msg_ids)).delete(synchronize_session=False)
print(f"Deleted {emails_deleted} fake email messages.")

# 4. Delete EnquiryNotes for fake enquiries
notes_deleted = db.query(EnquiryNote).filter(~EnquiryNote.enquiry_id.in_(real_enq_ids)).delete(synchronize_session=False)
print(f"Deleted {notes_deleted} fake enquiry notes.")

# 5. Delete RegistrationDocuments for fake enquiries
docs_deleted = db.query(RegistrationDocument).filter(~RegistrationDocument.enquiry_id.in_(real_enq_ids)).delete(synchronize_session=False)
print(f"Deleted {docs_deleted} fake registration documents.")

# 6. Delete fake ClientRegistrations
regs_deleted = db.query(ClientRegistration).filter(~ClientRegistration.email.in_(real_emails)).delete(synchronize_session=False)
print(f"Deleted {regs_deleted} fake client registrations.")

# 7. Delete ActivationTokens for fake users
fake_users = db.query(UserAccount).filter(~UserAccount.email.in_(real_emails)).all()
fake_user_ids = [u.id for u in fake_users]
tokens_deleted = db.query(ActivationToken).filter(ActivationToken.user_id.in_(fake_user_ids)).delete(synchronize_session=False)
print(f"Deleted {tokens_deleted} fake activation tokens.")

# 8. Delete fake UserAccounts
users_deleted = db.query(UserAccount).filter(UserAccount.id.in_(fake_user_ids)).delete(synchronize_session=False)
print(f"Deleted {users_deleted} fake user accounts.")

# 9. Delete fake Enquiries
enqs_deleted = db.query(Enquiry).filter(~Enquiry.id.in_(real_enq_ids)).delete(synchronize_session=False)
print(f"Deleted {enqs_deleted} fake enquiries.")

# 10. Delete fake Clients
clients_deleted = db.query(Client).filter(~Client.email.in_(real_emails)).delete(synchronize_session=False)
print(f"Deleted {clients_deleted} fake clients.")

db.commit()

# 11. Create or ensure clean real Client record for saisubodh618@gmail.com
now = datetime.now(timezone.utc)
real_client = db.query(Client).filter(Client.email == "saisubodh618@gmail.com").first()
if not real_client:
    real_client = Client(
        id="TRK-2026-001",
        partner1_name="Sai Subodh",
        partner2_name="Sru",
        email="saisubodh618@gmail.com",
        phone="6300548249",
        wedding_date=date(2026, 10, 9),
        wedding_location="Rambagh Palace, Jaipur",
        expected_guest_count=350,
        estimated_budget=Decimal("20000000.00"),
        wedding_theme="Regal Rajputana",
        service_package="Full-Service Royal Production",
        additional_requirements="Special royal procession, heritage palace decor, lakeside Sangeet.",
        enquiry_source="Website",
        status="Registered",
        created_at=now,
        updated_at=now
    )
    db.add(real_client)
    db.flush()
    print("Created real Client record: TRK-2026-001 (Sai Subodh & Sru)")
else:
    real_client.partner1_name = "Sai Subodh"
    real_client.partner2_name = "Sru"
    real_client.phone = "6300548249"
    real_client.wedding_date = date(2026, 10, 9)
    real_client.wedding_location = "Rambagh Palace, Jaipur"
    real_client.expected_guest_count = 350
    real_client.estimated_budget = Decimal("20000000.00")
    real_client.wedding_theme = "Regal Rajputana"
    real_client.service_package = "Full-Service Royal Production"
    real_client.status = "Registered"
    real_client.updated_at = now
    print(f"Updated real Client record: {real_client.id} (Sai Subodh & Sru)")

# 12. Link UserAccount to real Client
user = db.query(UserAccount).filter(UserAccount.email == "saisubodh618@gmail.com").first()
if user:
    user.client_id = real_client.id
    user.status = "ACTIVE"
    user.is_active = True
    print(f"Linked UserAccount {user.id} to Client {real_client.id}")

# 13. Link real Enquiries to real Client
for enq in db.query(Enquiry).filter(Enquiry.email == "saisubodh618@gmail.com").all():
    enq.client_id = real_client.id
    print(f"Linked Enquiry {enq.id} to Client {real_client.id}")

db.commit()

print("=" * 60)
print("DATABASE CLEANUP COMPLETE!")
print(f"Current Clients: {db.query(Client).count()}")
for c in db.query(Client).all():
    print(f"  • [{c.id}] {c.partner1_name} & {c.partner2_name} | {c.email} | {c.wedding_location} | Status: {c.status}")

print(f"Current Enquiries: {db.query(Enquiry).count()}")
for e in db.query(Enquiry).all():
    print(f"  • [{e.id}] {e.client_name} | {e.email} | Status: {e.status}")

print(f"Current Registrations: {db.query(ClientRegistration).count()}")
for r in db.query(ClientRegistration).all():
    print(f"  • [{r.id}] {r.full_name} | {r.email} | Status: {r.status}")

print(f"Current Users: {db.query(UserAccount).count()}")
for u in db.query(UserAccount).all():
    print(f"  • [{u.id}] {u.email} | Role: {u.role} | Status: {u.status} | ClientID: {u.client_id}")

db.close()

