from sqlalchemy import Column, String, Integer, Text, Numeric, Date, DateTime, Boolean, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class ServiceAgreement(Base):
    __tablename__ = "service_agreements"

    id = Column(String(50), primary_key=True, index=True)
    agreement_number = Column(String(50), nullable=False, unique=True, index=True)
    client_id = Column(String(50), ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)

    # Status: DRAFT, PENDING_SIGNATURE, SIGNED, VERIFIED, CANCELLED
    status = Column(String(50), nullable=False, default="DRAFT", index=True)

    # Core Wedding Details Snapshot
    wedding_date = Column(Date, nullable=False)
    wedding_location = Column(String(255), nullable=False)
    venue = Column(String(255), nullable=True)
    guest_count = Column(Integer, nullable=False, default=100)
    wedding_functions = Column(JSON, nullable=True)  # List of functions [{name, date, venue, guest_count, notes}]

    # Scope & Services
    service_package = Column(String(100), nullable=False, default="Royal Palace Grandeur")
    included_services = Column(JSON, nullable=True)   # List of strings
    excluded_services = Column(JSON, nullable=True)   # List of strings
    deliverables = Column(JSON, nullable=True)        # List of deliverables
    additional_terms = Column(Text, nullable=True)

    # Financial breakdown (NUMERIC decimal-safe)
    package_price = Column(Numeric(15, 2), nullable=False, default=0.00)
    tax_percentage = Column(Numeric(5, 2), nullable=False, default=18.00)  # GST standard 18%
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    discount_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    currency = Column(String(10), nullable=False, default="INR")

    # Version Tracking
    current_version_number = Column(Integer, nullable=False, default=1)
    agreement_version = Column(String(20), nullable=False, default="v1.0")

    # Internal Approval Tracking
    is_internally_approved = Column(Boolean, nullable=False, default=True)
    approved_by = Column(String(150), nullable=True, default="Maharani Gayatri Singh")
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Verification Tracking
    is_verified = Column(Boolean, nullable=False, default=False)
    verified_by = Column(String(150), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)

    # In-App OTP & Digital Signing Audit Trail
    signed_at = Column(DateTime(timezone=True), nullable=True)
    signed_by_name = Column(String(150), nullable=True)
    signed_by_email = Column(String(255), nullable=True)
    signature_data = Column(Text, nullable=True)  # Base64 digital signature string/canvas data
    signer_ip = Column(String(50), nullable=True)
    signer_user_agent = Column(String(500), nullable=True)
    signed_pdf_path = Column(String(500), nullable=True)
    
    # OTP verification state
    signing_otp_hash = Column(String(64), nullable=True)
    signing_otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    signing_otp_attempts = Column(Integer, nullable=False, default=0)
    signing_otp_verified = Column(Boolean, nullable=False, default=False)
    consent_confirmed = Column(Boolean, nullable=False, default=False)

    # Timestamps & Soft Deletion
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_by = Column(String(150), nullable=False, default="Agency Concierge")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    client = relationship("Client", backref="service_agreements")
    milestones = relationship("AgreementPaymentMilestone", back_populates="agreement", cascade="all, delete-orphan", order_by="AgreementPaymentMilestone.sequence_order")
    documents = relationship("AgreementDocument", back_populates="agreement", cascade="all, delete-orphan", order_by="desc(AgreementDocument.created_at)")
    status_history = relationship("AgreementStatusHistory", back_populates="agreement", cascade="all, delete-orphan", order_by="desc(AgreementStatusHistory.created_at)")

    def __repr__(self):
        return f"<ServiceAgreement {self.agreement_number} ({self.status}) for Client {self.client_id}>"


class AgreementPaymentMilestone(Base):
    __tablename__ = "agreement_payment_milestones"

    id = Column(String(50), primary_key=True, index=True)
    agreement_id = Column(String(50), ForeignKey("service_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    milestone_name = Column(String(100), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    due_description = Column(String(255), nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING | PAID | OVERDUE | WAIVED
    sequence_order = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    agreement = relationship("ServiceAgreement", back_populates="milestones")

    def __repr__(self):
        return f"<AgreementPaymentMilestone {self.milestone_name}: {self.percentage}% ({self.amount})>"


class AgreementDocument(Base):
    __tablename__ = "agreement_documents"

    id = Column(String(50), primary_key=True, index=True)
    agreement_id = Column(String(50), ForeignKey("service_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)  # DRAFT_CONTRACT | SIGNED_CONTRACT
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(100), nullable=False, default="application/pdf")
    version_number = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    agreement = relationship("ServiceAgreement", back_populates="documents")

    def __repr__(self):
        return f"<AgreementDocument {self.file_name} ({self.document_type})>"


class AgreementStatusHistory(Base):
    __tablename__ = "agreement_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agreement_id = Column(String(50), ForeignKey("service_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    changed_by = Column(String(150), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    agreement = relationship("ServiceAgreement", back_populates="status_history")

