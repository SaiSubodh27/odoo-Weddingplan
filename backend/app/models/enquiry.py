from sqlalchemy import Column, String, Integer, Text, Numeric, Date, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(String(50), primary_key=True, index=True)

    # Lead Information
    client_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=False, index=True)
    enquiry_source = Column(String(50), nullable=False, default="Email")  # Email, Phone, Website

    # Wedding Parameters
    wedding_date = Column(Date, nullable=True)
    wedding_location = Column(String(255), nullable=True)
    expected_guest_count = Column(Integer, nullable=True)
    estimated_budget = Column(Numeric(15, 2), nullable=True)
    requirements = Column(Text, nullable=True)

    # Staff Assignment & Workflow Status
    assigned_staff = Column(String(100), nullable=True, default="Maharani Gayatri Singh")
    status = Column(String(50), nullable=False, default="New")
    # Statuses: New, Contacted, Registration Document Sent, Registration Received, Under Review, Registered, Closed

    internal_notes = Column(Text, nullable=True)

    # Online Registration Token & Expiry
    registration_token = Column(String(100), unique=True, index=True, nullable=True)
    registration_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Document Timestamps
    registration_sent_at = Column(DateTime(timezone=True), nullable=True)
    registration_received_at = Column(DateTime(timezone=True), nullable=True)
    registration_reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Linked Client Record (created upon explicit registration)
    client_id = Column(String(50), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)

    # Soft Delete & Timestamps
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    client = relationship("Client", backref="enquiries")
    registration = relationship("ClientRegistration", back_populates="enquiry", uselist=False, cascade="all, delete-orphan")
    documents = relationship("RegistrationDocument", back_populates="enquiry", cascade="all, delete-orphan")
    messages = relationship("EmailMessage", back_populates="enquiry", cascade="all, delete-orphan", order_by="EmailMessage.created_at")
    notes_history = relationship("EnquiryNote", back_populates="enquiry", cascade="all, delete-orphan", order_by="desc(EnquiryNote.created_at)")

    def __repr__(self):
        return f"<Enquiry {self.id}: {self.client_name} ({self.status})>"


class EnquiryNote(Base):
    __tablename__ = "enquiry_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enquiry_id = Column(String(50), ForeignKey("enquiries.id", ondelete="CASCADE"), nullable=False, index=True)
    author = Column(String(100), nullable=False, default="Agency Staff")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    enquiry = relationship("Enquiry", back_populates="notes_history")
