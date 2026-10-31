from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="Catering", index=True)  # Catering, Decor, Photography, Floral, Sound, etc.
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=False, index=True)  # WhatsApp-enabled telephone
    email = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False, default="Jaipur")
    address = Column(Text, nullable=True)
    rating = Column(Numeric(3, 2), nullable=True, default=5.00)
    notes = Column(Text, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    catering_plans = relationship("CateringPlan", back_populates="selected_vendor")
    quotations = relationship("CateringQuotation", back_populates="vendor", cascade="all, delete-orphan")
    communications = relationship("CateringCommunicationLog", back_populates="vendor")

    def __repr__(self):
        return f"<Vendor {self.id}: {self.name} ({self.category})>"

