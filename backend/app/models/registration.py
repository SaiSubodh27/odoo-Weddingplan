from sqlalchemy import Column, String, Integer, Text, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class ClientRegistration(Base):
    __tablename__ = "client_registrations"

    id = Column(String(50), primary_key=True, index=True)
    enquiry_id = Column(String(50), ForeignKey("enquiries.id", ondelete="CASCADE"), nullable=True, index=True)

    # Google Forms & Source Tracking
    google_form_response_id = Column(String(100), unique=True, nullable=True, index=True)
    google_sheet_row = Column(Integer, nullable=True)
    enquiry_reference = Column(String(100), nullable=True, index=True)
    source = Column(String(50), nullable=False, default="Google Forms")

    # Couple Information
    full_name = Column(String(150), nullable=False)
    partner_name = Column(String(150), nullable=True)

    # Contact Details
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    address = Column(Text, nullable=True)

    # Wedding Parameters
    wedding_date = Column(Date, nullable=True)
    wedding_location = Column(String(255), nullable=True)
    expected_guest_count = Column(Integer, nullable=True)
    estimated_budget = Column(Numeric(15, 2), nullable=True)

    # Events & Preferences
    wedding_events = Column(Text, nullable=True)  # Comma-separated or JSON string
    preferred_theme = Column(String(255), nullable=True)
    service_package = Column(String(50), nullable=False, default="Full-Service")
    preferences = Column(Text, nullable=True)

    # Review & Approval Workflow
    status = Column(String(50), nullable=False, default="SUBMITTED")  # SUBMITTED | UNDER_REVIEW | APPROVED | CORRECTIONS_REQUESTED
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    correction_notes = Column(Text, nullable=True)

    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    enquiry = relationship("Enquiry", back_populates="registration")

    def __repr__(self):
        return f"<ClientRegistration {self.id} for Enquiry {self.enquiry_id} ({self.status})>"

