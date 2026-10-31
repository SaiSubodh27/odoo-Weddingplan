import io
import os
import base64
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    Image as RLImage
)
from reportlab.pdfgen import canvas

from app.models.agreement import ServiceAgreement


def format_inr(val: Optional[Decimal | float | int]) -> str:
    if val is None:
        return "₹0.00"
    return f"₹{Decimal(str(val)):,.2f}"


class NumberedCanvas(canvas.Canvas):
    """Adds luxury running header, gold divider, and running pagination to each page."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#736F68"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 800, "THE ROYAL KNOT — BESPOKE SERVICE AGREEMENT & WEDDING DOSSIER")
            self.setStrokeColor(colors.HexColor("#E5E0D8"))
            self.setLineWidth(0.5)
            self.line(54, 792, 541, 792)

        # Running footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(541, 36, page_str)
        self.drawString(54, 36, "Strictly Confidential — Authorized Agency Execution")
        self.setStrokeColor(colors.HexColor("#C9A67D"))
        self.setLineWidth(0.5)
        self.line(54, 48, 541, 48)
        self.restoreState()


def generate_service_agreement_pdf(agreement: ServiceAgreement, output_path: Optional[str] = None) -> bytes:
    """Generates an authentic luxury PDF for a Service Agreement with full legal terms and execution block."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        output_path if output_path else buffer,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Luxury Typography Styles
    style_supertitle = ParagraphStyle(
        'DocSuperTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#9E7D3B'),
        alignment=1,
        spaceAfter=4
    )

    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1F2421'),
        alignment=1,
        spaceAfter=6
    )

    style_subtitle = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#5C5850'),
        alignment=1,
        spaceAfter=18
    )

    style_h1 = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1F2421'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6
    )

    style_legal = ParagraphStyle(
        'LegalClause',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor('#4A4A4A'),
        spaceAfter=5
    )

    story = []

    # Title & Header
    story.append(Paragraph("✦ THE ROYAL KNOT ✦", style_supertitle))
    story.append(Paragraph("LUXURY WEDDING PLANNING SERVICE AGREEMENT", style_title))
    status_label = "EXECUTED & DIGITALLY SIGNED" if agreement.status == "SIGNED" else "OFFICIAL DRAFT"
    story.append(Paragraph(f"Agreement Reference: <b>{agreement.agreement_number}</b> · Version: <b>{agreement.agreement_version}</b> · Status: <b>{status_label}</b>", style_subtitle))
    story.append(Spacer(1, 10))

    # Section 1: Parties to this Agreement
    client = agreement.client
    couple_name = f"{client.partner1_name} & {client.partner2_name}" if client else "Distinguished Clients"
    client_email = client.email if client else "client@domain.com"
    client_phone = client.phone if client else "N/A"

    story.append(Paragraph("1. PARTIES TO THIS AGREEMENT", style_h1))
    parties_data = [
        [
            Paragraph("<b>SERVICE PROVIDER</b>", style_body),
            Paragraph("<b>CLIENT / COUPLE</b>", style_body)
        ],
        [
            Paragraph("<b>The Royal Knot Wedding Planning LLC</b><br/>Heritage Wing, Rambagh Enclave, Jaipur, Rajasthan<br/>Contact: concierge@theroyalknot.in | +91 141 289 4000<br/>Principal: Maharani Gayatri Singh", style_body),
            Paragraph(f"<b>{couple_name}</b><br/>Email: {client_email}<br/>Phone: {client_phone}<br/>Client Code: {agreement.client_id}", style_body)
        ]
    ]
    t_parties = Table(parties_data, colWidths=[240, 240])
    t_parties.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FAF8F5')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#FFFFFF')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E0D8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E0D8')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_parties)
    story.append(Spacer(1, 14))

    # Section 2: Wedding Scope & Itinerary
    story.append(Paragraph("2. WEDDING SCOPE & ITINERARY", style_h1))
    scope_data = [
        [Paragraph("<b>Wedding Date:</b>", style_body), Paragraph(str(agreement.wedding_date), style_body)],
        [Paragraph("<b>Destination & City:</b>", style_body), Paragraph(agreement.wedding_location, style_body)],
        [Paragraph("<b>Primary Palace Venue:</b>", style_body), Paragraph(agreement.venue or "Heritage Palace Grounds", style_body)],
        [Paragraph("<b>Expected Guest Count:</b>", style_body), Paragraph(f"{agreement.guest_count} Guests", style_body)],
        [Paragraph("<b>Service Tier / Package:</b>", style_body), Paragraph(agreement.service_package, style_body)],
    ]
    t_scope = Table(scope_data, colWidths=[160, 320])
    t_scope.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FAF8F5')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E0D8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E0D8')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_scope)
    story.append(Spacer(1, 14))

    # Section 3: Deliverables & Included Services
    story.append(Paragraph("3. SCOPE OF SERVICES & DELIVERABLES", style_h1))
    included = agreement.included_services or [
        "End-to-end Palace venue booking, royal heritage permissions, and logistics coordination",
        "Design concept, royal Rajputana thematic decor styling, bespoke floral curation",
        "Curated royal catering coordination, bespoke tasting sessions, and banquet management",
        "Entertainment artist booking, royal welcome bagpipes, manganiyar folk troupes",
        "Guest concierge desk, luxury vintage fleet transfer management, hospitality lounges"
    ]
    inc_paragraphs = [Paragraph(f"• {item}", style_body) for item in included]
    for p in inc_paragraphs:
        story.append(p)
    story.append(Spacer(1, 14))

    # Section 4: Commercial Terms & Payment Milestones
    story.append(Paragraph("4. COMMERCIAL TERMS & PAYMENT MILESTONES", style_h1))
    comm_summary = [
        [Paragraph("<b>Package Price (Net):</b>", style_body), Paragraph(format_inr(agreement.package_price), style_body)],
        [Paragraph(f"<b>Applicable Taxes (GST {agreement.tax_percentage}%):</b>", style_body), Paragraph(format_inr(agreement.tax_amount), style_body)],
        [Paragraph("<b>Total Contract Value:</b>", style_body), Paragraph(f"<b>{format_inr(agreement.total_amount)}</b>", style_body)]
    ]
    t_comm = Table(comm_summary, colWidths=[240, 240])
    t_comm.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAF8F5')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#C9A67D')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E0D8')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_comm)
    story.append(Spacer(1, 8))

    # Milestones table
    milestones_rows = [
        [
            Paragraph("<b>Seq</b>", style_body),
            Paragraph("<b>Milestone Name</b>", style_body),
            Paragraph("<b>%</b>", style_body),
            Paragraph("<b>Amount (INR)</b>", style_body),
            Paragraph("<b>Due Trigger</b>", style_body),
            Paragraph("<b>Status</b>", style_body)
        ]
    ]
    if agreement.milestones:
        for m in agreement.milestones:
            milestones_rows.append([
                Paragraph(str(m.sequence_order), style_body),
                Paragraph(m.milestone_name, style_body),
                Paragraph(f"{m.percentage}%", style_body),
                Paragraph(format_inr(m.amount), style_body),
                Paragraph(m.due_description, style_body),
                Paragraph(f"<b>{m.status}</b>", style_body)
            ])
    else:
        milestones_rows.append([
            Paragraph("1", style_body),
            Paragraph("Initial Advance Retainer", style_body),
            Paragraph("25.00%", style_body),
            Paragraph(format_inr(agreement.total_amount * Decimal("0.25")), style_body),
            Paragraph("Upon contract signing & calendar reservation", style_body),
            Paragraph("PENDING", style_body)
        ])
        milestones_rows.append([
            Paragraph("2", style_body),
            Paragraph("Design Approval Milestone", style_body),
            Paragraph("35.00%", style_body),
            Paragraph(format_inr(agreement.total_amount * Decimal("0.35")), style_body),
            Paragraph("90 days prior to wedding date", style_body),
            Paragraph("PENDING", style_body)
        ])
        milestones_rows.append([
            Paragraph("3", style_body),
            Paragraph("Vendor Lock & Final Balance", style_body),
            Paragraph("40.00%", style_body),
            Paragraph(format_inr(agreement.total_amount * Decimal("0.40")), style_body),
            Paragraph("30 days prior to first celebration", style_body),
            Paragraph("PENDING", style_body)
        ])

    t_milestones = Table(milestones_rows, colWidths=[30, 140, 40, 90, 130, 50])
    t_milestones.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F2EFE8')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E0D8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E0D8')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_milestones)
    story.append(Spacer(1, 14))

    # Section 5: Standard Legal Clauses & Cancellation Policy
    story.append(Paragraph("5. CONTRACTUAL TERMS, RESCHEDULING & CANCELLATION", style_h1))
    legal_text = (
        "<b>5.1 Binding Contract:</b> This Service Agreement represents the final understanding between the parties. "
        "Execution via secure digital OTP and cryptographic signature constitutes a valid and legally binding contract under the Information Technology Act, 2000.<br/>"
        "<b>5.2 Non-Refundable Booking Retainer:</b> The Initial Advance Milestone secures exclusive calendar reservation, principal planner commitment, and palace holds. In the event of voluntary client cancellation, the advance fee is non-refundable.<br/>"
        "<b>5.3 Rescheduling:</b> Postponement requested at least 90 calendar days prior to the wedding date is permissible without penalty, subject to agency calendar availability across Rajasthan heritage properties.<br/>"
        "<b>5.4 Force Majeure:</b> Neither party shall be held liable for failure to perform due to acts of God, civil emergencies, or state-mandated heritage monument closures. Dates will be mutually renegotiated in good faith.<br/>"
        "<b>5.5 Jurisdiction:</b> All disputes arising out of or in connection with this Agreement shall be subject to the exclusive jurisdiction of the competent courts in Jaipur, Rajasthan."
    )
    story.append(Paragraph(legal_text, style_legal))
    story.append(Spacer(1, 14))

    # Section 6: Execution Block / Signatures
    story.append(KeepTogether([
        Paragraph("6. EXECUTION & ELECTRONIC SIGNING ACKNOWLEDGEMENT", style_h1),
        Paragraph(
            "By signing electronically below, the Client explicitly consents to all clauses, service specifications, deliverables, and payment obligations contained herein.",
            style_body
        ),
        Spacer(1, 10),
        Table([
            [
                Paragraph("<b>FOR THE ROYAL KNOT:</b><br/><br/><br/>_____________________________________<br/><b>Maharani Gayatri Singh</b><br/>Principal Wedding Planner<br/>The Royal Knot Agency, Jaipur", style_body),
                _render_client_signature_cell(agreement, style_body)
            ]
        ], colWidths=[240, 240], style=[
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E0D8')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E0D8')),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAF8F5'))
        ])
    ]))

    doc.build(story, canvasmaker=NumberedCanvas)

    if output_path:
        with open(output_path, "rb") as f:
            return f.read()
    return buffer.getvalue()


def _render_client_signature_cell(agreement: ServiceAgreement, style_body: ParagraphStyle) -> Paragraph:
    """Renders the client signature box with digital signature image and audit metadata if signed."""
    if agreement.status == "SIGNED" and agreement.signed_at:
        date_str = agreement.signed_at.strftime("%d %b %Y, %I:%M %p UTC")
        signer = agreement.signed_by_name or "Authorized Client"
        email = agreement.signed_by_email or ""
        ip = agreement.signer_ip or "Verified Terminal"
        return Paragraph(
            f"<b>DIGITALLY SIGNED & VERIFIED</b><br/>"
            f"<font color='#2D5A3C'><b>✓ Cryptographically Signed via Email OTP</b></font><br/>"
            f"<b>Signer:</b> {signer}<br/>"
            f"<b>Email:</b> {email}<br/>"
            f"<b>Timestamp:</b> {date_str}<br/>"
            f"<b>Audit IP:</b> {ip}<br/>"
            f"<b>Consent:</b> Explicit Acceptance Recorded",
            style_body
        )
    return Paragraph(
        "<b>FOR CLIENT / COUPLE:</b><br/><br/><br/>"
        "_____________________________________<br/>"
        "<b>Authorized Client Signature</b><br/>"
        "Pending In-App Digital Execution",
        style_body
    )

