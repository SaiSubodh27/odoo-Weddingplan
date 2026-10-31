from sqlalchemy import Column, String, Integer, Text, Numeric, Date, DateTime, Boolean, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class ServiceAgreement(Base):
    __tablename__ = "service_agreements"

    id = Column(String(50), primary_key=True, index=True)
    agreement_number = Column(String(50), nullable=False, unique=True, index=True)
    client_id = Column(String(50), ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)

    # Status: DRAFT, PENDING_INTERNAL_APPROVAL, APPROVED_TO_SEND, SIGNING_REQUEST_CREATING,
    # SIGNING_PENDING, SIGNED, UNDER_VERIFICATION, NEEDS_CORRECTION, VERIFIED, BOOKING_CONFIRMED,
    # EXPIRED, CANCELLED, SUPERSEDED, REJECTED
    status = Column(String(50), nullable=False, default="DRAFT", index=True)

    # Signing Provider Status: NOT_CREATED, SENT, PARTIALLY_SIGNED, COMPLETED, DECLINED, EXPIRED, CANCELLED, FAILED
    signing_status = Column(String(50), nullable=False, default="NOT_CREATED", index=True)

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

    # Internal Approval Tracking
    is_internally_approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(150), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Verification Tracking
    is_verified = Column(Boolean, nullable=False, default=False)
    verified_by = Column(String(150), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)

    # Timestamps & Soft Deletion
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_by = Column(String(150), nullable=False, default="Agency Concierge")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    client = relationship("Client", backref="service_agreements")
    versions = relationship("ServiceAgreementVersion", back_populates="agreement", cascade="all, delete-orphan", order_by="ServiceAgreementVersion.version_number")
    milestones = relationship("AgreementPaymentMilestone", back_populates="agreement", cascade="all, delete-orphan", order_by="AgreementPaymentMilestone.sequence_order")
    signature_requests = relationship("AgreementSignatureRequest", back_populates="agreement", cascade="all, delete-orphan", order_by="desc(AgreementSignatureRequest.created_at)")
    documents = relationship("AgreementDocument", back_populates="agreement", cascade="all, delete-orphan", order_by="desc(AgreementDocument.created_at)")
    status_history = relationship("AgreementStatusHistory", back_populates="agreement", cascade="all, delete-orphan", order_by="desc(AgreementStatusHistory.created_at)")
    reviews = relationship("AgreementReview", back_populates="agreement", cascade="all, delete-orphan", order_by="desc(AgreementReview.created_at)")
    booking = relationship("WeddingBooking", back_populates="agreement", uselist=False)

    def __repr__(self):
        return f"<ServiceAgreement {self.agreement_number} ({self.status}) for Client {self.client_id}>"


class ServiceAgreementVersion(Base):
    __tablename__ = "service_agreement_versions"

    id = Column(String(50), primary_key=True, index=True)
    agreement_id = Column(String(50), ForeignKey("service_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)

    # Immutable Snapshot JSON of the exact contract terms, client data, and financial lines
    snapshot_data = Column(JSON, nullable=False)

    # Document Reference & SHA-256 Hash of the Generated PDF
    pdf_document_id = Column(String(50), nullable=True)
    pdf_hash_sha256 = Column(String(64), nullable=True)
    pdf_file_path = Column(String(255), nullable=True)

    # Version Lifecycle Status: DRAFT, SENT_FOR_SIGNING, SIGNED, SUPERSEDED, CANCELLED
    status = Column(String(50), nullable=False, default="DRAFT")
    revision_reason = Column(Text, nullable=True)

    created_by = Column(String(150), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    agreement = relationship("ServiceAgreement", back_populates="versions")

    def __repr__(self):
        return f"<ServiceAgreementVersion {self.agreement_id} v{self.version_number} ({self.status})>"


class AgreementPaymentMilestone(Base):
    __tablename__ = "agreement_payment_milestones"

    id = Column(String(50), primary_key=True, index=True)
    agreement_id = Column(String(50), ForeignKey("service_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    sequence_order = Column(Integer, nullable=False, default=1)

    name = Column(String(150), nullable=False)  # e.g. Advance Booking Fee (25%)
    percentage = Column(Numeric(5, 2), nullable=False)  # e.g. 25.00
    amount = Column(Numeric(15, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    description = Column(String(255), nullable=True)

    agreement = relationship("ServiceAgreement", back_populates="milestones")

    def __repr__(self):
        return f"<AgreementPaymentMilestone {self.name}: {self.amount}>"


class AgreementDocument(Base):
    __tablename__ = "agreement_documents"

    id = Column(String(50), primary_key=True, index=True)
    agreement_id = Column(String(50), ForeignKey("service_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)

    # Document type: 'generated_unsigned_pdf', 'signed_agreement_pdf', 'leegality_audit_trail', 'completion_certificate'
    document_type = Column(String(50), nullable=False, index=True)

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_hash_sha256 = Column(String(64), nullable=False, index=True)
    mime_type = Column(String(100), nullable=False, default="application/pdf")

    source = Column(String(100), nullable=False, default="System")  # 'System', 'Leegality Webhook', 'Leegality API'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    agreement = relationship("ServiceAgreement", back_populates="documents")

    def __repr__(self):
        return f"<AgreementDocument {self.id}: {self.original_filename} ({self.document_type})>"


class AgreementSignatureRequest(Base):
    __tablename__ = "agreement_signature_requests"

    id = Column(String(50), primary_key=True, index=True)
    agreement_id = Column(String(50), ForeignKey("service_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)

    # Leegality official transaction references
    leegality_document_id = Column(String(100), nullable=True, unique=True, index=True)
    leegality_request_id = Column(String(100), nullable=True, index=True)

    # Provider & Environment
    provider = Column(String(50), nullable=False, default="Leegality")
    environment = Column(String(50), nullable=False, default="sandbox")  # sandbox | production | mock

    # Signer Details
    signer_name = Column(String(150), nullable=False)
    signer_email = Column(String(255), nullable=False)
    signer_phone = Column(String(50), nullable=True)

    # Unique Client Signing URL provided by Leegality
    signing_url = Column(Text, nullable=True)
    signing_url_expires_at = Column(DateTime(timezone=True), nullable=True)

    # State: NOT_SENT, SENT, SIGNED, EXPIRED, REJECTED, CANCELLED, FAILED
    status = Column(String(50), nullable=False, default="NOT_SENT", index=True)

    # Raw metadata returned from Leegality API
    raw_response = Column(JSON, nullable=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    agreement = relationship("ServiceAgreement", back_populates="signature_requests")
    webhook_events = relationship("AgreementWebhookEvent", back_populates="signature_request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AgreementSignatureRequest {self.id} for doc {self.leegality_document_id} ({self.status})>"


class AgreementWebhookEvent(Base):
    __tablename__ = "agreement_webhook_events"

    id = Column(String(50), primary_key=True, index=True)
    signature_request_id = Column(String(50), ForeignKey("agreement_signature_requests.id", ondelete="CASCADE"), nullable=True, index=True)
    document_id = Column(String(100), nullable=False, index=True)

    event_type = Column(String(100), nullable=False)  # success | failure | status_update
    mac_received = Column(String(150), nullable=True)
    mac_verified = Column(Boolean, nullable=False, default=False)

    # Idempotency fingerprint (SHA-256 of canonical payload + timestamp)
    event_fingerprint = Column(String(64), nullable=False, unique=True, index=True)

    raw_payload = Column(JSON, nullable=False)
    is_processed = Column(Boolean, nullable=False, default=False)
    processing_notes = Column(Text, nullable=True)

    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    signature_request = relationship("AgreementSignatureRequest", back_populates="webhook_events")

    def __repr__(self):
        return f"<AgreementWebhookEvent {self.id} (type: {self.event_type}, verified: {self.mac_verified})>"


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


class AgreementReview(Base):
    __tablename__ = "agreement_reviews"

    id = Column(String(50), primary_key=True, index=True)
    agreement_id = Column(String(50), ForeignKey("service_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)

    reviewer_name = Column(String(150), nullable=False)
    decision = Column(String(50), nullable=False)  # VERIFIED | REJECTED | NEEDS_CORRECTION
    remarks = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    agreement = relationship("ServiceAgreement", back_populates="reviews")


class WeddingBooking(Base):
    __tablename__ = "wedding_bookings"

    id = Column(String(50), primary_key=True, index=True)
    booking_reference = Column(String(50), nullable=False, unique=True, index=True)
    client_id = Column(String(50), ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)
    agreement_id = Column(String(50), ForeignKey("service_agreements.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    confirmed_version_number = Column(Integer, nullable=False)

    # Booking parameters confirmed
    couple_title = Column(String(255), nullable=False)
    wedding_date = Column(Date, nullable=False)
    wedding_location = Column(String(255), nullable=False)
    venue = Column(String(255), nullable=True)
    package_name = Column(String(100), nullable=False)
    confirmed_total_amount = Column(Numeric(15, 2), nullable=False)
    advance_amount_agreed = Column(Numeric(15, 2), nullable=False)

    # Booking confirmation details
    confirmed_by = Column(String(150), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmation_notes = Column(Text, nullable=True)

    # Status: CONFIRMED | TRANSFERRED_TO_PROJECT_MANAGEMENT | CANCELLED
    status = Column(String(50), nullable=False, default="CONFIRMED", index=True)

    # Phase 3 Project Handoff marker
    phase3_handoff_ready = Column(Boolean, nullable=False, default=True)
    phase3_handoff_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    agreement = relationship("ServiceAgreement", back_populates="booking")
    client = relationship("Client", backref="wedding_bookings")

    def __repr__(self):
        return f"<WeddingBooking {self.booking_reference}: {self.couple_title} ({self.status})>"

