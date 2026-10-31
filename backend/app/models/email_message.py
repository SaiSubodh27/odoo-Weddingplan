from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(String(50), primary_key=True, index=True)
    enquiry_id = Column(String(50), ForeignKey("enquiries.id", ondelete="SET NULL"), nullable=True, index=True)

    # Direction: 'incoming' or 'outgoing'
    direction = Column(String(20), nullable=False, index=True)

    # Participants
    sender_name = Column(String(150), nullable=True)
    sender_email = Column(String(255), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)

    # Content
    subject = Column(String(500), nullable=False)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)

    # Threading and Provider Identifiers
    message_id = Column(String(255), nullable=True, unique=True, index=True)
    thread_id = Column(String(255), nullable=True, index=True)
    in_reply_to = Column(String(255), nullable=True)
    references = Column(Text, nullable=True)

    # Workflow Status
    # Incoming: UNCLASSIFIED, ENQUIRY_CREATED, ASSOCIATED, IGNORED, RECEIVED
    # Outgoing: SENT, FAILED, PENDING
    status = Column(String(50), nullable=False, default="RECEIVED", index=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    received_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    enquiry = relationship("Enquiry", back_populates="messages")
    attachments = relationship("EmailAttachment", back_populates="email_message", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EmailMessage {self.id}: {self.direction} '{self.subject[:30]}' ({self.status})>"


class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id = Column(String(50), primary_key=True, index=True)
    email_message_id = Column(String(50), ForeignKey("email_messages.id", ondelete="CASCADE"), nullable=False, index=True)

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String(100), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    email_message = relationship("EmailMessage", back_populates="attachments")

    def __repr__(self):
        return f"<EmailAttachment {self.id}: {self.original_filename} ({self.file_size} bytes)>"

