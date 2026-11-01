# Blocking Bugs Log - The Royal Knot

- [FIXED] SQLite OperationalError no such column agreement_version: Resolved by syncing schema and fresh test initialization.
- [FIXED] Pydantic validation on PaymentMilestoneInput: Added alias validator supporting name/milestone_name and description/due_description.
- [FIXED] ReportLab PdfService got multiple values for agreement_data: Converted generate_service_agreement_pdf to @staticmethod.
- [FIXED] OperationalError table wedding_projects has no column named deposit_paid: Removed stale test SQLite database to re-initialize with current schema.
- [FIXED] IntegrityError NOT NULL constraint failed vendors.phone: Added phone number to vendor fixtures in profitability test.
