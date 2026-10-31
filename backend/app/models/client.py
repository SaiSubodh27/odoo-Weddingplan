from sqlalchemy import Column, String, Integer, Text, Numeric, Date, DateTime, Boolean, func
from app.database.base import Base


class Client(Base):
    __tablename__ = "clients"

    # System Identification
    id = Column(String(50), primary_key=True, index=True)

    # Couple Information
    partner1_name = Column(String(150), nullable=False)
    partner2_name = Column(String(150), nullable=False)

    # Contact Information
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=False, index=True)

    # Wedding Information
    wedding_date = Column(Date, nullable=False)
    wedding_location = Column(String(255), nullable=False)
    expected_guest_count = Column(Integer, nullable=False, default=100)
    estimated_budget = Column(Numeric(15, 2), nullable=False, default=0.00)
    wedding_theme = Column(String(255), nullable=True)

    # Service Information
    service_package = Column(String(50), nullable=False, default="Full-Service")
    additional_requirements = Column(Text, nullable=True)

    # Enquiry & Status
    enquiry_source = Column(String(50), nullable=False, default="Email")
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Enquiry")

    # Soft Delete & Audit Timestamps
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Client {self.id}: {self.partner1_name} & {self.partner2_name}>"

