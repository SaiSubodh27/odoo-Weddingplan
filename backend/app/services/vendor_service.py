import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from fastapi import HTTPException, status

from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorStatusUpdate


class VendorService:

    @staticmethod
    def generate_vendor_id(db: Session) -> str:
        """Generates a unique vendor ID (e.g. VND-A1B2C3)."""
        uid = uuid.uuid4().hex[:6].upper()
        return f"VND-{uid}"

    def list_vendors(
        self,
        db: Session,
        category: Optional[str] = None,
        city: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[int, List[Vendor]]:
        """Lists registered vendors with filtering, search, and pagination."""
        query = db.query(Vendor)

        if category and category.lower() != "all":
            query = query.filter(Vendor.category.ilike(category))

        if city and city.lower() != "all":
            query = query.filter(Vendor.city.ilike(city))

        if is_active is not None:
            query = query.filter(Vendor.is_active == is_active)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Vendor.name.ilike(pattern),
                    Vendor.contact_person.ilike(pattern),
                    Vendor.phone.ilike(pattern),
                    Vendor.email.ilike(pattern),
                    Vendor.city.ilike(pattern),
                )
            )

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(Vendor.name.asc()).offset(offset).limit(page_size).all()
        return total, items

    def get_vendor_by_id(self, db: Session, vendor_id: str) -> Optional[Vendor]:
        """Retrieves vendor by ID."""
        return db.query(Vendor).filter(Vendor.id == vendor_id).first()

    def create_vendor(self, db: Session, vendor_in: VendorCreate) -> Vendor:
        """
        Creates a new vendor record.
        Prevents accidental duplicates by checking for existing active vendors with identical phone.
        """
        clean_phone = vendor_in.phone.strip()
        existing = db.query(Vendor).filter(
            func.replace(func.replace(Vendor.phone, " ", ""), "-", "") == clean_phone.replace(" ", "").replace("-", "")
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor with telephone '{vendor_in.phone}' already exists: '{existing.name}' ({existing.id})."
            )

        # Check duplicate name in same city
        existing_name = db.query(Vendor).filter(
            func.lower(Vendor.name) == vendor_in.name.strip().lower(),
            func.lower(Vendor.city) == vendor_in.city.strip().lower()
        ).first()

        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor named '{vendor_in.name}' already registered in {vendor_in.city} ({existing_name.id})."
            )

        vendor = Vendor(
            id=self.generate_vendor_id(db),
            name=vendor_in.name.strip(),
            category=vendor_in.category.strip(),
            contact_person=vendor_in.contact_person.strip() if vendor_in.contact_person else None,
            phone=clean_phone,
            email=vendor_in.email.strip().lower() if vendor_in.email else None,
            city=vendor_in.city.strip(),
            address=vendor_in.address.strip() if vendor_in.address else None,
            rating=vendor_in.rating,
            notes=vendor_in.notes.strip() if vendor_in.notes else None,
            is_active=vendor_in.is_active,
        )

        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor

    def update_vendor(self, db: Session, vendor_id: str, vendor_in: VendorUpdate) -> Vendor:
        """Updates vendor details."""
        vendor = self.get_vendor_by_id(db, vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor '{vendor_id}' not found."
            )

        # Check phone conflict if phone is being updated
        if vendor_in.phone:
            clean_phone = vendor_in.phone.strip()
            conflict = db.query(Vendor).filter(
                Vendor.id != vendor_id,
                func.replace(func.replace(Vendor.phone, " ", ""), "-", "") == clean_phone.replace(" ", "").replace("-", "")
            ).first()
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Telephone '{vendor_in.phone}' is already registered to another vendor: '{conflict.name}'."
                )
            vendor.phone = clean_phone

        if vendor_in.name is not None:
            vendor.name = vendor_in.name.strip()
        if vendor_in.category is not None:
            vendor.category = vendor_in.category.strip()
        if vendor_in.contact_person is not None:
            vendor.contact_person = vendor_in.contact_person.strip() or None
        if vendor_in.email is not None:
            vendor.email = vendor_in.email.strip().lower() or None
        if vendor_in.city is not None:
            vendor.city = vendor_in.city.strip()
        if vendor_in.address is not None:
            vendor.address = vendor_in.address.strip() or None
        if vendor_in.rating is not None:
            vendor.rating = vendor_in.rating
        if vendor_in.notes is not None:
            vendor.notes = vendor_in.notes.strip() or None
        if vendor_in.is_active is not None:
            vendor.is_active = vendor_in.is_active

        db.commit()
        db.refresh(vendor)
        return vendor

    def set_vendor_status(self, db: Session, vendor_id: str, is_active: bool, notes: Optional[str] = None) -> Vendor:
        """Activates or deactivates a vendor."""
        vendor = self.get_vendor_by_id(db, vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor '{vendor_id}' not found."
            )

        vendor.is_active = is_active
        if notes:
            existing_notes = vendor.notes or ""
            vendor.notes = f"{existing_notes}\n[Status Update] Active={is_active}: {notes}".strip()

        db.commit()
        db.refresh(vendor)
        return vendor


vendor_service = VendorService()

