import io
import csv
import re
import uuid
import hashlib
import logging
from datetime import datetime, timezone, date
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.enquiry import Enquiry, EnquiryNote
from app.models.registration import ClientRegistration
from app.models.user import UserAccount
from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """
    Handles ingestion, parsing, deduplication, and enquiry matching for Google Forms
    responses submitted directly via Webhook, Google Sheet CSV export, or manual CSV upload.
    """

    # Normalized field names mapped to possible Google Forms column headers (lowercase, stripped)
    COLUMN_MAPPINGS = {
        "timestamp": [
            "timestamp", "submitted at", "submission time", "time", "date"
        ],
        "full_name": [
            "full name", "client name", "name", "your name", "full name (primary contact)",
            "primary contact name", "bride / groom name", "client full name"
        ],
        "partner_name": [
            "partner's full name", "partner name", "groom / bride name", "spouse name",
            "fiancé / fiancée name", "partner's name"
        ],
        "email": [
            "email", "email address", "contact email", "primary email", "e-mail"
        ],
        "phone": [
            "phone", "phone number", "contact number", "mobile number", "mobile", "whatsapp number"
        ],
        "address": [
            "address", "current city / address", "city", "residence", "city / country", "current address"
        ],
        "wedding_date": [
            "wedding date", "tentative wedding date", "wedding date (or tentative date)",
            "event date", "date of celebration", "celebration date", "proposed date"
        ],
        "wedding_location": [
            "wedding location", "wedding destination / location", "preferred destination / venue",
            "venue / location", "destination", "city / venue", "wedding venue", "preferred venue"
        ],
        "expected_guest_count": [
            "expected guest count", "guest count", "approximate guest count", "number of guests",
            "estimated guest count", "guests"
        ],
        "estimated_budget": [
            "estimated budget", "budget", "wedding budget", "approximate budget",
            "estimated celebration budget", "budget range"
        ],
        "wedding_events": [
            "wedding events", "wedding events / ceremonies", "functions / events", "events",
            "wedding functions", "ceremonies", "selected events"
        ],
        "preferred_theme": [
            "preferred theme", "preferred theme / aesthetic", "theme & aesthetic",
            "theme", "wedding aesthetic", "decor & theme preference"
        ],
        "service_package": [
            "service package", "service tier", "preferred service package", "package", "services required"
        ],
        "preferences": [
            "special requests", "preferences", "additional notes", "special requirements",
            "preferences & requirements", "requirements", "notes", "tell us more"
        ],
        "enquiry_reference": [
            "enquiry reference id", "enquiry reference", "enquiry id", "reference id",
            "reference number", "enquiry ref", "booking ref", "ref id", "enquiry ref (if known)"
        ]
    }

    @classmethod
    def _normalize_header(cls, header: str) -> str:
        """Strips punctuation and extra spaces for resilient header matching."""
        clean = re.sub(r"[^\w\s]", " ", header).lower()
        return " ".join(clean.split())

    @classmethod
    def _map_row_dict(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """Maps varying Google Form question names into canonical schema fields."""
        mapped = {}
        row_normalized = {cls._normalize_header(k): v for k, v in row.items()}

        for canonical_field, aliases in cls.COLUMN_MAPPINGS.items():
            for alias in aliases:
                norm_alias = cls._normalize_header(alias)
                # Check exact match or substring match
                match_key = next((k for k in row_normalized.keys() if norm_alias == k or norm_alias in k), None)
                if match_key and row_normalized[match_key] not in (None, ""):
                    val = row_normalized[match_key]
                    mapped[canonical_field] = str(val).strip()
                    break

        return mapped

    @classmethod
    def _parse_date(cls, date_str: Optional[str]) -> Optional[date]:
        """Parses common date formats from Google Forms."""
        if not date_str or not date_str.strip():
            return None
        clean = date_str.strip()

        # Extract only date part if a full timestamp is passed
        clean = clean.split(" ")[0].split("T")[0]

        formats = [
            "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y",
            "%Y/%m/%d", "%d.%m.%Y", "%B %d, %Y", "%b %d, %Y"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(clean, fmt).date()
            except ValueError:
                continue

        # Try regex extraction of YYYY-MM-DD or DD/MM/YYYY
        m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", clean)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except Exception:
                pass

        m2 = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", clean)
        if m2:
            try:
                # Assume DD/MM/YYYY
                return date(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)))
            except Exception:
                pass

        return None

    @classmethod
    def _parse_guest_count(cls, count_str: Optional[str]) -> Optional[int]:
        """Extracts integer guest count from string values like '300-500 guests' or '450'."""
        if not count_str or not count_str.strip():
            return None
        clean = count_str.strip()

        # Handle ranges like 300 - 500 by taking average
        range_match = re.search(r"(\d+)\s*[-–to]+\s*(\d+)", clean, re.IGNORECASE)
        if range_match:
            try:
                low = int(range_match.group(1))
                high = int(range_match.group(2))
                return (low + high) // 2
            except Exception:
                pass

        # Extract first number
        nums = re.findall(r"\d+", clean)
        if nums:
            try:
                return int(nums[0])
            except Exception:
                pass
        return None

    @classmethod
    def _parse_budget(cls, budget_str: Optional[str]) -> Optional[Decimal]:
        """Parses budget values handling ₹, $, Cr, Lakh, and comma formatting."""
        if not budget_str or not budget_str.strip():
            return None
        clean = budget_str.strip().replace(",", "")

        # Check for Crore (Cr)
        cr_match = re.search(r"([\d\.]+)\s*(?:cr|crore|crores)", clean, re.IGNORECASE)
        if cr_match:
            try:
                val = float(cr_match.group(1)) * 10000000
                return Decimal(str(int(val)))
            except Exception:
                pass

        # Check for Lakh (L)
        lakh_match = re.search(r"([\d\.]+)\s*(?:lakh|lakhs|lac|lacs|l)", clean, re.IGNORECASE)
        if lakh_match:
            try:
                val = float(lakh_match.group(1)) * 100000
                return Decimal(str(int(val)))
            except Exception:
                pass

        # Raw number extraction
        raw_num_match = re.search(r"[\d]+(?:\.\d+)?", clean)
        if raw_num_match:
            try:
                return Decimal(raw_num_match.group(0))
            except Exception:
                pass

        return None

    @classmethod
    def _generate_response_id(cls, email: str, timestamp_str: Optional[str], full_name: str) -> str:
        """Generates a stable unique hash if Google Forms doesn't provide an explicit ID."""
        raw = f"{email.strip().lower()}|{timestamp_str or ''}|{full_name.strip().lower()}"
        return "GFR-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16].upper()

    @classmethod
    def match_enquiry(
        cls,
        db: Session,
        enquiry_reference: Optional[str],
        email: str
    ) -> Optional[Enquiry]:
        """
        Attempts to match a registration response to an existing enquiry:
        1. By Enquiry Reference ID (e.g. 'TRK-ENQ-2026-081', 'ENQ-081', or '081').
        2. Fallback: by Client Email address against active enquiries.
        """
        # 1. Match by Enquiry Reference
        if enquiry_reference and enquiry_reference.strip():
            clean_ref = enquiry_reference.strip().upper()
            # Try exact match on ID
            enq = db.query(Enquiry).filter(
                Enquiry.id == clean_ref,
                Enquiry.is_deleted == False
            ).first()
            if enq:
                return enq

            # Try partial search (e.g. if client entered '081' or 'ENQ-2026-081')
            enq_partial = db.query(Enquiry).filter(
                Enquiry.id.ilike(f"%{clean_ref}%"),
                Enquiry.is_deleted == False
            ).first()
            if enq_partial:
                return enq_partial

        # 2. Match by email
        clean_email = email.strip().lower()
        if clean_email:
            enq_by_email = db.query(Enquiry).filter(
                func.lower(Enquiry.email) == clean_email,
                Enquiry.is_deleted == False
            ).order_by(Enquiry.created_at.desc()).first()

            if enq_by_email:
                return enq_by_email

        return None

    @classmethod
    def ingest_single_response(
        cls,
        db: Session,
        raw_data: Dict[str, Any],
        response_id: Optional[str] = None,
        sheet_row: Optional[int] = None,
        source: str = "Google Forms"
    ) -> Dict[str, Any]:
        """
        Processes a single Google Forms response:
        - Maps fields flexibly.
        - Deduplicates.
        - Matches to Enquiry (or flags as UNMATCHED).
        - Persists in client_registrations and updates Enquiry state.
        """
        mapped = cls._map_row_dict(raw_data)

        email = mapped.get("email", "").strip().lower()
        full_name = mapped.get("full_name", "").strip()

        if not email or not full_name:
            return {
                "success": False,
                "reason": "Missing required fields (full_name and email).",
                "status": "SKIPPED"
            }

        timestamp_str = mapped.get("timestamp")
        resp_id = response_id or cls._generate_response_id(email, timestamp_str, full_name)

        # Deduplication check
        existing_reg = db.query(ClientRegistration).filter(
            ClientRegistration.google_form_response_id == resp_id
        ).first()

        if existing_reg:
            return {
                "success": True,
                "reason": "Response already imported.",
                "registration_id": existing_reg.id,
                "enquiry_id": existing_reg.enquiry_id,
                "status": "DUPLICATE_SKIPPED"
            }

        # Parse data values
        wedding_date = cls._parse_date(mapped.get("wedding_date"))
        guest_count = cls._parse_guest_count(mapped.get("expected_guest_count"))
        budget = cls._parse_budget(mapped.get("estimated_budget"))
        partner_name = mapped.get("partner_name")
        phone = mapped.get("phone", "+91 (Provided via Google Form)")
        address = mapped.get("address")
        wedding_location = mapped.get("wedding_location")
        wedding_events = mapped.get("wedding_events")
        preferred_theme = mapped.get("preferred_theme")
        service_package = mapped.get("service_package", "Full-Service")
        preferences = mapped.get("preferences")
        enquiry_ref = mapped.get("enquiry_reference")

        now = datetime.now(timezone.utc)

        # Match to an existing Enquiry
        matched_enquiry = cls.match_enquiry(db=db, enquiry_reference=enquiry_ref, email=email)

        reg_id = f"REG-{uuid.uuid4().hex[:8].upper()}"

        if matched_enquiry:
            enquiry_id = matched_enquiry.id
            reg_status = "SUBMITTED"

            # Check if this enquiry already had an existing registration record
            existing_for_enquiry = db.query(ClientRegistration).filter(
                ClientRegistration.enquiry_id == matched_enquiry.id
            ).first()

            if existing_for_enquiry:
                # Update existing registration record with new Google Forms data
                existing_for_enquiry.google_form_response_id = resp_id
                existing_for_enquiry.google_sheet_row = sheet_row
                existing_for_enquiry.enquiry_reference = enquiry_ref
                existing_for_enquiry.full_name = full_name
                existing_for_enquiry.partner_name = partner_name
                existing_for_enquiry.phone = phone
                existing_for_enquiry.address = address
                existing_for_enquiry.wedding_date = wedding_date
                existing_for_enquiry.wedding_location = wedding_location
                existing_for_enquiry.expected_guest_count = guest_count
                existing_for_enquiry.estimated_budget = budget
                existing_for_enquiry.wedding_events = wedding_events
                existing_for_enquiry.preferred_theme = preferred_theme
                existing_for_enquiry.service_package = service_package
                existing_for_enquiry.preferences = preferences
                existing_for_enquiry.status = "SUBMITTED"
                existing_for_enquiry.submitted_at = now
                reg_record = existing_for_enquiry
            else:
                reg_record = ClientRegistration(
                    id=reg_id,
                    enquiry_id=enquiry_id,
                    google_form_response_id=resp_id,
                    google_sheet_row=sheet_row,
                    enquiry_reference=enquiry_ref,
                    source=source,
                    full_name=full_name,
                    partner_name=partner_name,
                    email=email,
                    phone=phone,
                    address=address,
                    wedding_date=wedding_date,
                    wedding_location=wedding_location,
                    expected_guest_count=guest_count,
                    estimated_budget=budget,
                    wedding_events=wedding_events,
                    preferred_theme=preferred_theme,
                    service_package=service_package,
                    preferences=preferences,
                    status=reg_status,
                    submitted_at=now
                )
                db.add(reg_record)

            # Update Enquiry with verified parameters
            matched_enquiry.client_name = f"{full_name}{' & ' + partner_name if partner_name else ''}"
            matched_enquiry.phone = phone
            if wedding_date:
                matched_enquiry.wedding_date = wedding_date
            if wedding_location:
                matched_enquiry.wedding_location = wedding_location
            if guest_count:
                matched_enquiry.expected_guest_count = guest_count
            if budget:
                matched_enquiry.estimated_budget = budget
            if preferences:
                matched_enquiry.requirements = preferences

            matched_enquiry.status = "Registration Submitted"
            matched_enquiry.registration_received_at = now

            # Add internal activity note to enquiry
            note_content = (
                f"Google Forms registration received and associated with this enquiry.\n"
                f"Couple: {full_name} & {partner_name or 'Partner'}\n"
                f"Location: {wedding_location or 'TBD'} | Date: {wedding_date or 'TBD'}\n"
                f"Guest Count: {guest_count or 'TBD'} | Budget: ₹{budget:,.2f}" if budget else ""
            )
            db.add(EnquiryNote(
                enquiry_id=matched_enquiry.id,
                author="System (Google Forms Sync)",
                content=note_content
            ))

        else:
            # Unmatched registration
            enquiry_id = None
            reg_status = "UNMATCHED"

            reg_record = ClientRegistration(
                id=reg_id,
                enquiry_id=None,
                google_form_response_id=resp_id,
                google_sheet_row=sheet_row,
                enquiry_reference=enquiry_ref,
                source=source,
                full_name=full_name,
                partner_name=partner_name,
                email=email,
                phone=phone,
                address=address,
                wedding_date=wedding_date,
                wedding_location=wedding_location,
                expected_guest_count=guest_count,
                estimated_budget=budget,
                wedding_events=wedding_events,
                preferred_theme=preferred_theme,
                service_package=service_package,
                preferences=preferences,
                status=reg_status,
                submitted_at=now
            )
            db.add(reg_record)

        db.commit()
        db.refresh(reg_record)

        return {
            "success": True,
            "registration_id": reg_record.id,
            "enquiry_id": enquiry_id,
            "status": reg_status,
            "matched": enquiry_id is not None,
            "client_name": reg_record.full_name,
            "email": reg_record.email
        }

    @classmethod
    def ingest_csv_content(cls, db: Session, csv_text: str, source: str = "Google Forms CSV") -> Dict[str, Any]:
        """
        Parses a full CSV export from Google Forms / Google Sheets and ingests each row.
        """
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        stats = {
            "total_rows": 0,
            "imported": 0,
            "matched": 0,
            "unmatched": 0,
            "duplicates_skipped": 0,
            "errors": 0,
            "details": []
        }

        for row_index, row in enumerate(reader, start=2):
            stats["total_rows"] += 1
            try:
                res = cls.ingest_single_response(
                    db=db,
                    raw_data=row,
                    sheet_row=row_index,
                    source=source
                )
                if res.get("status") == "DUPLICATE_SKIPPED":
                    stats["duplicates_skipped"] += 1
                elif res.get("success"):
                    stats["imported"] += 1
                    if res.get("matched"):
                        stats["matched"] += 1
                    else:
                        stats["unmatched"] += 1
                    stats["details"].append(res)
                else:
                    stats["errors"] += 1
            except Exception as e:
                logger.error(f"Error importing row {row_index}: {str(e)}")
                stats["errors"] += 1

        return stats

    @classmethod
    def sync_google_sheet(
        cls,
        db: Session,
        sheet_id: Optional[str] = None,
        custom_csv_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetches the CSV export from Google Sheets and imports responses.
        URL format: https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv
        """
        target_sheet_id = sheet_id or settings.GOOGLE_SHEET_ID
        csv_url = custom_csv_url or settings.GOOGLE_SHEET_CSV_URL

        if not csv_url:
            if not target_sheet_id:
                return {
                    "success": False,
                    "message": "Google Sheet ID or CSV export URL is not configured. Please set GOOGLE_SHEET_ID in settings or .env."
                }
            csv_url = f"https://docs.google.com/spreadsheets/d/{target_sheet_id}/export?format=csv"

        try:
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                resp = client.get(csv_url)
                if resp.status_code != 200:
                    return {
                        "success": False,
                        "status_code": resp.status_code,
                        "message": (
                            f"Failed to fetch Google Sheet CSV (HTTP {resp.status_code}). "
                            "Ensure the Google Sheet is shared as 'Anyone with the link can view' or published to the web."
                        )
                    }

                csv_text = resp.text
                if not csv_text or "<html" in csv_text.lower():
                    return {
                        "success": False,
                        "message": (
                            "Received HTML instead of CSV data. Please verify the Google Sheet sharing settings "
                            "or use File > Share > Publish to web > CSV."
                        )
                    }

                import_stats = cls.ingest_csv_content(db=db, csv_text=csv_text, source="Google Sheets Sync")
                return {
                    "success": True,
                    "message": f"Google Sheets sync completed. {import_stats['imported']} imported, {import_stats['duplicates_skipped']} duplicates skipped.",
                    "stats": import_stats
                }

        except Exception as e:
            logger.error(f"Failed to sync Google Sheet: {str(e)}")
            return {
                "success": False,
                "message": f"Network or parsing error syncing Google Sheet: {str(e)}"
            }

    @classmethod
    def associate_unmatched_registration(
        cls,
        db: Session,
        registration_id: str,
        enquiry_id: str,
        staff_name: str = "Agency Staff"
    ) -> Dict[str, Any]:
        """
        Manually links an UNMATCHED Google Forms registration to an existing Enquiry.
        """
        reg = db.query(ClientRegistration).filter(ClientRegistration.id == registration_id).first()
        if not reg:
            return {"success": False, "message": f"Registration '{registration_id}' not found."}

        enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id, Enquiry.is_deleted == False).first()
        if not enquiry:
            return {"success": False, "message": f"Enquiry '{enquiry_id}' not found."}

        now = datetime.now(timezone.utc)
        reg.enquiry_id = enquiry.id
        reg.status = "SUBMITTED"
        reg.updated_at = now

        # Synchronize enquiry fields
        enquiry.client_name = f"{reg.full_name}{' & ' + reg.partner_name if reg.partner_name else ''}"
        enquiry.phone = reg.phone
        if reg.wedding_date:
            enquiry.wedding_date = reg.wedding_date
        if reg.wedding_location:
            enquiry.wedding_location = reg.wedding_location
        if reg.expected_guest_count:
            enquiry.expected_guest_count = reg.expected_guest_count
        if reg.estimated_budget:
            enquiry.estimated_budget = reg.estimated_budget
        if reg.preferences:
            enquiry.requirements = reg.preferences

        enquiry.status = "Registration Submitted"
        enquiry.registration_received_at = now

        note = EnquiryNote(
            enquiry_id=enquiry.id,
            author=staff_name,
            content=f"Manually associated unmatched Google Forms registration {reg.id} ({reg.full_name}) with this enquiry."
        )
        db.add(note)

        db.commit()
        db.refresh(reg)
        db.refresh(enquiry)

        return {
            "success": True,
            "message": f"Successfully associated registration with enquiry {enquiry.id}.",
            "registration_id": reg.id,
            "enquiry_id": enquiry.id,
            "status": reg.status
        }
