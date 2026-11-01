from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate


class ClientService:
    @staticmethod
    def generate_next_id(db: Session) -> str:
        """Generates the next sequential luxury client reference ID (e.g. TRK-2026-081)."""
        count = db.query(func.count(Client.id)).scalar() or 0
        return f"TRK-2026-0{80 + count + 1}"

    @classmethod
    def create_client(cls, db: Session, client_in: ClientCreate) -> Client:
        client_id = cls.generate_next_id(db)

        # Convert schema fields to dict
        client_data = client_in.model_dump()

        db_client = Client(
            id=client_id,
            **client_data
        )

        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client

    @staticmethod
    def get_client(db: Session, client_id: str) -> Optional[Client]:
        return db.query(Client).filter(
            Client.id == client_id,
            Client.is_deleted == False
        ).first()

    @staticmethod
    def list_clients(
        db: Session,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        status: Optional[str] = None,
        enquiry_source: Optional[str] = None
    ) -> Tuple[List[Client], int]:
        query = db.query(Client).filter(Client.is_deleted == False)

        if status and status != "All":
            query = query.filter(Client.status == status)

        if enquiry_source and enquiry_source != "All":
            query = query.filter(Client.enquiry_source == enquiry_source)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Client.partner1_name.ilike(search_term),
                    Client.partner2_name.ilike(search_term),
                    Client.email.ilike(search_term),
                    Client.phone.ilike(search_term),
                    Client.wedding_location.ilike(search_term),
                    Client.id.ilike(search_term)
                )
            )

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(Client.created_at.desc()).offset(offset).limit(page_size).all()

        return items, total

    @staticmethod
    def update_client(db: Session, client_id: str, client_in: ClientUpdate) -> Optional[Client]:
        db_client = db.query(Client).filter(
            Client.id == client_id,
            Client.is_deleted == False
        ).first()

        if not db_client:
            return None

        update_data = client_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_client, field, value)

        db.commit()
        db.refresh(db_client)

        # Synchronize or generate ServiceAgreement snapshot with updated client wedding details
        try:
            from app.models.agreement import ServiceAgreement, AgreementPaymentMilestone
            from decimal import Decimal
            agreement = db.query(ServiceAgreement).filter(
                ServiceAgreement.client_id == client_id,
                ServiceAgreement.is_deleted == False
            ).order_by(ServiceAgreement.created_at.desc()).first()

            if not agreement:
                from app.services.agreement_service import agreement_service
                agreement_service.get_or_create_agreement_for_client(db, client_id)
            elif agreement.status in ("DRAFT", "PENDING_SIGNATURE"):
                if db_client.wedding_date:
                    agreement.wedding_date = db_client.wedding_date
                if db_client.wedding_location:
                    agreement.wedding_location = db_client.wedding_location
                    agreement.venue = db_client.wedding_location
                if db_client.expected_guest_count:
                    agreement.guest_count = db_client.expected_guest_count
                if db_client.service_package:
                    agreement.service_package = db_client.service_package
                if db_client.estimated_budget and db_client.estimated_budget > 0:
                    tax_pct = Decimal("18.00")
                    agreement.package_price = db_client.estimated_budget
                    agreement.tax_amount = (agreement.package_price * (tax_pct / Decimal("100.00"))).quantize(Decimal("0.01"))
                    agreement.total_amount = agreement.package_price + agreement.tax_amount

                    # Re-create milestones
                    db.query(AgreementPaymentMilestone).filter(AgreementPaymentMilestone.agreement_id == agreement.id).delete()
                    from app.services.agreement_service import agreement_service
                    agreement_service._create_default_milestones(db, agreement)
                db.commit()
        except Exception:
            db.rollback()

        return db_client

    @staticmethod
    def soft_delete_client(db: Session, client_id: str) -> bool:
        db_client = db.query(Client).filter(
            Client.id == client_id,
            Client.is_deleted == False
        ).first()

        if not db_client:
            return False

        db_client.is_deleted = True
        db.commit()
        return True


client_service = ClientService()

