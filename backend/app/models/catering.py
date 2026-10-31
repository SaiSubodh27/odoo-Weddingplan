from sqlalchemy import Column, String, Integer, Text, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, backref
from app.database.base import Base


class CateringPlan(Base):
    __tablename__ = "catering_plans"

    id = Column(String(50), primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("wedding_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    function_id = Column(String(50), ForeignKey("wedding_functions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Culinary Requirements
    service_style = Column(String(100), nullable=False, default="Silver Platter Degustation")
    cuisine_preferences = Column(Text, nullable=True)

    # Guest Counts (Project default with event-specific override permitted; flexible dietary estimates)
    guest_count = Column(Integer, nullable=False, default=100)
    veg_count = Column(Integer, nullable=False, default=0)
    non_veg_count = Column(Integer, nullable=False, default=0)
    jain_count = Column(Integer, nullable=False, default=0)
    dietary_notes = Column(Text, nullable=True)

    # Logistics & Financials
    service_timings = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    budget = Column(Numeric(15, 2), nullable=False, default=0.00)

    # Vendor Selection & Agreed Pricing
    selected_vendor_id = Column(String(50), ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    agreed_cost = Column(Numeric(15, 2), nullable=True)

    # Lifecycle Status: Draft, Requirements Confirmed, Vendor Selected, Menu Finalized, Sent to Vendor, Vendor Confirmed
    status = Column(String(50), nullable=False, default="Draft", index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("WeddingProject", back_populates="catering_plans")
    function = relationship("WeddingFunction", backref=backref("catering_plan", uselist=False, cascade="all, delete-orphan"))
    selected_vendor = relationship("Vendor", back_populates="catering_plans")

    menu_items = relationship(
        "CateringMenuItem",
        back_populates="catering_plan",
        cascade="all, delete-orphan",
        order_by="CateringMenuItem.display_order"
    )
    quotations = relationship(
        "CateringQuotation",
        back_populates="catering_plan",
        cascade="all, delete-orphan",
        order_by="desc(CateringQuotation.created_at)"
    )
    communications = relationship(
        "CateringCommunicationLog",
        back_populates="catering_plan",
        cascade="all, delete-orphan",
        order_by="desc(CateringCommunicationLog.created_at)"
    )

    def __repr__(self):
        return f"<CateringPlan {self.id}: Function {self.function_id} ({self.status})>"


class CateringMenuItem(Base):
    __tablename__ = "catering_menu_items"

    id = Column(String(50), primary_key=True, index=True)
    catering_plan_id = Column(String(50), ForeignKey("catering_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    # Course: Welcome Drinks, Royal Appetizers & Starters, Main Degustation Courses, Live Artisanal Counters, Breads & Dal, Dessert Atelier, Late Night Bites
    course_category = Column(String(100), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dietary_tag = Column(String(50), nullable=False, default="Vegetarian")  # Vegetarian, Non-Vegetarian, Jain, Gluten-Free, Chef Signature
    quantity_note = Column(String(150), nullable=True)
    display_order = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    catering_plan = relationship("CateringPlan", back_populates="menu_items")

    def __repr__(self):
        return f"<CateringMenuItem {self.id}: [{self.course_category}] {self.item_name} ({self.dietary_tag})>"


class CateringQuotation(Base):
    __tablename__ = "catering_quotations"

    id = Column(String(50), primary_key=True, index=True)
    catering_plan_id = Column(String(50), ForeignKey("catering_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(String(50), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)

    quotation_reference = Column(String(100), nullable=True)  # e.g. QUO-MEWAR-2027-01
    per_person_rate = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_guest_count = Column(Integer, nullable=False, default=100)
    food_subtotal = Column(Numeric(15, 2), nullable=False, default=0.00)
    equipment_charges = Column(Numeric(15, 2), nullable=False, default=0.00)

    # Configurable GST rate per quotation (e.g. 0%, 5%, 12%, 18%)
    gst_rate_percent = Column(Numeric(5, 2), nullable=False, default=18.00)
    gst_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0.00)

    status = Column(String(50), nullable=False, default="Received", index=True)  # Received, Under Review, Accepted, Rejected
    validity_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    catering_plan = relationship("CateringPlan", back_populates="quotations")
    vendor = relationship("Vendor", back_populates="quotations")

    def __repr__(self):
        return f"<CateringQuotation {self.id}: Vendor {self.vendor_id} - Total {self.total_amount} ({self.status})>"


class CateringCommunicationLog(Base):
    __tablename__ = "catering_communications"

    id = Column(String(50), primary_key=True, index=True)
    catering_plan_id = Column(String(50), ForeignKey("catering_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(String(50), ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)

    communication_type = Column(String(50), nullable=False, default="WhatsApp Manual Share")
    recipient_phone = Column(String(50), nullable=True)
    message_text = Column(Text, nullable=True)
    pdf_download_url = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="Initiated", index=True)  # Initiated, Sent, Delivered, Failed
    initiated_by = Column(String(100), nullable=False, default="Agency Staff")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    catering_plan = relationship("CateringPlan", back_populates="communications")
    vendor = relationship("Vendor", back_populates="communications")

    def __repr__(self):
        return f"<CateringCommunicationLog {self.id}: {self.communication_type} to {self.recipient_phone} ({self.status})>"

