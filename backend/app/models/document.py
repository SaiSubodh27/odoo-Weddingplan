from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class RegistrationDocument(Base):
    __tablename__ = "registration_documents"

    id = Column(String(50), primary_key=True, index=True)
    enquiry_id = Column(String(50), ForeignKey("enquiries.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(50), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)

    # Document type: 'sent_to_client' | 'completed_by_client' | 'blank_template'
    document_type = Column(String(50), nullable=False)

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String(100), nullable=False)
    uploaded_by = Column(String(100), nullable=False, default="Agency Staff")

    # Review status
    is_reviewed = Column(Boolean, nullable=False, default=False)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    enquiry = relationship("Enquiry", back_populates="documents")
    client = relationship("Client", backref="documents")

    def __repr__(self):
        return f"<RegistrationDocument {self.id}: {self.original_filename} ({self.document_type})>"
