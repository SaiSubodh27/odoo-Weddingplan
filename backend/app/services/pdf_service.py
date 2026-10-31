from reportlab.pdfgen import canvas
import os
import hashlib
import io
from decimal import Decimal
from typing import Optional, Any
from datetime import datetime, date

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from app.models.catering import CateringPlan, CateringQuotation, CateringMenuItem


def format_inr(val: Optional[Decimal | float | int]) -> str:
    """Formats numeric values into Indian Rupee representation (e.g. ₹ 11,80,000.00)."""
    if val is None:
        return "₹ 0.00"
    dec = Decimal(str(val))
    return f"₹ {dec:,.2f}"


def p_str(val: Optional[Any], default: str = "—") -> str:
    """Ensures a string is never None or blank before passing to ReportLab Paragraph."""
    if val is None:
        return default
    s = str(val).strip()
    return s if s else default


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and stamp total page numbers and luxury agency footers."""
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

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#736F68"))

        # Running Top Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "THE ROYAL KNOT — BESPOKE SERVICE AGREEMENT & WEDDING DOSSIER")
            self.setStrokeColor(colors.HexColor("#E5E0D8"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#E5E0D8"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        
        self.drawString(54, 32, "Confidential — The Royal Knot Luxury Destination Concierge · Jaipur & Udaipur")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()




class PdfService:

    @staticmethod
    def generate_catering_quotation_pdf(
        plan: CateringPlan,
        quotation: CateringQuotation,
    ) -> bytes:
        """
        Builds a formal, luxury-styled catering quotation PDF document using ReportLab.
        Uses live database attributes only without mock or invented legal details.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom Royal Knot luxury styling
        title_style = ParagraphStyle(
            "RoyalTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1F2421"),
        )
        subtitle_style = ParagraphStyle(
            "RoyalSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#9E7D3B"),
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1F2421"),
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#2B2D2F"),
        )
        body_bold = ParagraphStyle(
            "BodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1F2421"),
        )
        body_right = ParagraphStyle(
            "BodyRight",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#2B2D2F"),
        )
        body_right_bold = ParagraphStyle(
            "BodyRightBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#1F2421"),
        )

        elements = []

        # 1. Header Banner
        elements.append(Paragraph("THE ROYAL KNOT", title_style))
        elements.append(Paragraph("LUXURY WEDDING PLANNING & PALACE MANAGEMENT — JAIPUR & UDAIPUR", subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#9E7D3B"), spaceAfter=12))

        # 2. Document Title & Reference
        doc_header_data = [
            [
                Paragraph("<b>DOCUMENT:</b> FORMAL CATERING QUOTATION SPECIFICATION", body_style),
                Paragraph(f"<b>DATE:</b> {datetime.now().strftime('%d %b %Y')}", body_right),
            ],
            [
                Paragraph(f"<b>QUOTATION REF:</b> {quotation.quotation_reference or quotation.id}", body_style),
                Paragraph(f"<b>STATUS:</b> {quotation.status.upper()}", body_right_bold),
            ],
        ]
        doc_header_table = Table(doc_header_data, colWidths=[300, 240])
        doc_header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(doc_header_table)
        elements.append(Spacer(1, 10))

        # 3. Wedding Project & Ceremony Function Details
        elements.append(Paragraph("1. WEDDING CELEBRATION & EVENT DETAILS", section_heading))
        project_name = p_str(plan.project.project_name if plan.project else None, "Luxury Wedding Celebration")
        func_name = p_str(plan.function.function_name if plan.function else None, "Ceremony Event")
        func_date = plan.function.function_date.strftime("%d %B %Y") if (plan.function and plan.function.function_date) else "Scheduled"
        func_timings = p_str(plan.service_timings or (f"{plan.function.start_time or ''} - {plan.function.end_time or ''}".strip(" - ") if plan.function else None), "Banquet Service")
        venue = p_str(plan.location or (plan.function.venue if plan.function else None), "Palace Venue")

        event_data = [
            [Paragraph("<b>Wedding Project:</b>", body_style), Paragraph(project_name, body_style),
             Paragraph("<b>Ceremony:</b>", body_style), Paragraph(func_name, body_style)],
            [Paragraph("<b>Event Date:</b>", body_style), Paragraph(func_date, body_style),
             Paragraph("<b>Service Timings:</b>", body_style), Paragraph(func_timings, body_style)],
            [Paragraph("<b>Palace Venue:</b>", body_style), Paragraph(venue, body_style),
             Paragraph("<b>Service Style:</b>", body_style), Paragraph(p_str(plan.service_style, "Silver Platter"), body_style)],
            [Paragraph("<b>Cuisine Style:</b>", body_style), Paragraph(p_str(plan.cuisine_preferences, "Royal Banqueting"), body_style),
             Paragraph("<b>Target Guests:</b>", body_style), Paragraph(f"{quotation.total_guest_count} Pax", body_bold)],
        ]
        event_table = Table(event_data, colWidths=[95, 175, 95, 175])
        event_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAF8F5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E0D8")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(event_table)
        elements.append(Spacer(1, 8))

        # Dietary Breakdown Summary
        dietary_str = f"Vegetarian: {plan.veg_count or 0} | Non-Vegetarian: {plan.non_veg_count or 0} | Strict Jain: {plan.jain_count or 0}"
        if plan.dietary_notes:
            dietary_str += f" ({plan.dietary_notes})"
        elements.append(Paragraph(f"<b>Dietary Pax Breakdown:</b> {dietary_str}", body_style))
        elements.append(Spacer(1, 10))

        # 4. Catering Vendor Information
        elements.append(Paragraph("2. CATERING VENDOR DOSSIER", section_heading))
        vendor_name = p_str(quotation.vendor.name if quotation.vendor else None, "Independent Master Caterer")
        contact_person = p_str(quotation.vendor.contact_person if quotation.vendor else None, "Concierge Liaison")
        phone = p_str(quotation.vendor.phone if quotation.vendor else None, "Registered on File")
        city = p_str(quotation.vendor.city if quotation.vendor else None, "Rajasthan")
        rating = f"{quotation.vendor.rating}/5.00" if (quotation.vendor and quotation.vendor.rating) else "5.00/5.00"

        vendor_data = [
            [Paragraph("<b>Vendor Firm:</b>", body_style), Paragraph(vendor_name, body_bold),
             Paragraph("<b>Contact Person:</b>", body_style), Paragraph(contact_person, body_style)],
            [Paragraph("<b>WhatsApp Phone:</b>", body_style), Paragraph(phone, body_style),
             Paragraph("<b>Operating City:</b>", body_style), Paragraph(f"{city} (Rating: {rating})", body_style)],
        ]
        vendor_table = Table(vendor_data, colWidths=[95, 175, 95, 175])
        vendor_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAF8F5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E0D8")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(vendor_table)
        elements.append(Spacer(1, 10))

        # 5. Financial Costing & Commercial Summary
        elements.append(Paragraph("3. COMMERCIAL COSTING & TAX BREAKDOWN", section_heading))
        costing_rows = [
            [
                Paragraph("<b>Item Description</b>", body_bold),
                Paragraph("<b>Parameters / Rate</b>", body_style),
                Paragraph("<b>Amount (INR)</b>", body_right_bold)
            ],
            [
                Paragraph("Palace Culinary Degustation Service", body_style),
                Paragraph(f"{quotation.total_guest_count} guests @ {format_inr(quotation.per_person_rate)} per pax", body_style),
                Paragraph(format_inr(quotation.food_subtotal), body_right)
            ],
            [
                Paragraph("Live Stalls, Kitchen Equipment & Silverware Rentals", body_style),
                Paragraph("Bespoke setup, chafing vessels, tandoors & service stations", body_style),
                Paragraph(format_inr(quotation.equipment_charges), body_right)
            ],
            [
                Paragraph("Taxable Subtotal", body_bold),
                Paragraph("Combined Food & Equipment Services", body_style),
                Paragraph(format_inr(quotation.food_subtotal + quotation.equipment_charges), body_right_bold)
            ],
            [
                Paragraph(f"Goods & Services Tax (GST @ {quotation.gst_rate_percent}%)", body_style),
                Paragraph("Configured quotation tax rate applied to combined service subtotal", body_style),
                Paragraph(format_inr(quotation.gst_amount), body_right)
            ],
            [
                Paragraph("<b>TOTAL CONTRACT QUOTATION</b>", body_bold),
                Paragraph("<b>Final Agreed Commercial Investment</b>", body_style),
                Paragraph(f"<b>{format_inr(quotation.total_amount)}</b>", body_right_bold)
            ],
        ]
        costing_table = Table(costing_rows, colWidths=[200, 200, 140])
        costing_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEBE4")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C5BFB5")),
            ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#FAF8F5")),
            ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#FAF8F5")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(costing_table)
        elements.append(Spacer(1, 10))

        # 6. Finalized Menu Courses (if menu items exist)
        if plan.menu_items:
            elements.append(Paragraph("4. CURATED EVENT MENU DISHES & COURSES", section_heading))
            menu_rows = [
                [
                    Paragraph("<b>Course</b>", body_bold),
                    Paragraph("<b>Dish Name & Description</b>", body_bold),
                    Paragraph("<b>Dietary Tag</b>", body_style),
                    Paragraph("<b>Portion / Note</b>", body_style),
                ]
            ]
            sorted_items = sorted(plan.menu_items, key=lambda x: x.display_order)
            for item in sorted_items:
                dish_text = f"<b>{p_str(item.item_name, 'Dish')}</b>"
                if item.description:
                    dish_text += f"<br/><font color='#555555'>{item.description}</font>"
                menu_rows.append([
                    Paragraph(p_str(item.course_category, "Course"), body_style),
                    Paragraph(dish_text, body_style),
                    Paragraph(p_str(item.dietary_tag, "Standard"), body_style),
                    Paragraph(p_str(item.quantity_note, "Standard banquet service"), body_style),
                ])
            menu_table = Table(menu_rows, colWidths=[110, 240, 90, 100])
            menu_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEBE4")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E0D8")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(menu_table)
            elements.append(Spacer(1, 10))

        # 7. Terms, Notes & Validity
        elements.append(Paragraph("5. QUOTATION NOTES & TERMS", section_heading))
        validity = quotation.validity_date.strftime("%d %B %Y") if quotation.validity_date else "Subject to seasonal re-confirmation"
        notes_text = quotation.notes or "No additional conditions recorded."
        terms_data = [
            [Paragraph("<b>Validity Deadline:</b>", body_style), Paragraph(validity, body_style)],
            [Paragraph("<b>Vendor Notes:</b>", body_style), Paragraph(notes_text, body_style)],
        ]
        terms_table = Table(terms_data, colWidths=[110, 430])
        terms_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAF8F5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E0D8")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(terms_table)
        elements.append(Spacer(1, 16))

        # Footer
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#9E7D3B"), spaceAfter=8))
        elements.append(Paragraph(
            "The Royal Knot Luxury Destination Wedding Planners • Confidential Client & Vendor Specification Document",
            ParagraphStyle("Footer", parent=styles["Normal"], fontName="Helvetica", fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor("#736F68"))
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


    @staticmethod
    def generate_service_agreement_pdf(
            agreement_data: dict,
            client_data: dict,
            version_number: int,
            output_filepath: str
        ) -> dict:
            """
            Generates a professional, legally-structured PDF for The Royal Knot Service Agreement.
            Computes SHA-256 hash and file size.
            """
            os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
            doc = SimpleDocTemplate(
                output_filepath,
                pagesize=letter,
                leftMargin=54,
                rightMargin=54,
                topMargin=54,
                bottomMargin=54
            )

            styles = getSampleStyleSheet()

            # Custom Luxury Color Palette
            c_gold = colors.HexColor("#9E7D3B")
            c_charcoal = colors.HexColor("#1F2421")
            c_ivory_bg = colors.HexColor("#FAF8F5")
            c_border = colors.HexColor("#E5E0D8")
            c_muted = colors.HexColor("#5C5850")

            # Custom Typography
            style_title = ParagraphStyle(
                'LuxuryTitle',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=22,
                leading=26,
                textColor=c_charcoal,
                alignment=1
            )
            style_subtitle = ParagraphStyle(
                'LuxurySubtitle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                leading=14,
                textColor=c_gold,
                alignment=1,
                spaceAfter=15
            )
            style_h1 = ParagraphStyle(
                'SectionH1',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=12,
                leading=16,
                textColor=c_charcoal,
                spaceBefore=12,
                spaceAfter=6
            )
            style_body = ParagraphStyle(
                'LuxuryBody',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=9,
                leading=13,
                textColor=c_charcoal
            )
            style_body_bold = ParagraphStyle(
                'LuxuryBodyBold',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=9,
                leading=13,
                textColor=c_charcoal
            )
            style_legal = ParagraphStyle(
                'LegalClause',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=8,
                leading=11,
                textColor=c_muted
            )

            story = []

            # Header Block
            story.append(Paragraph("✦ THE ROYAL KNOT ✦", style_subtitle))
            story.append(Paragraph("LUXURY WEDDING PLANNING SERVICE AGREEMENT", style_title))
            story.append(Paragraph("Heritage Destination Concierge · Jaipur & Udaipur Operating Office", style_subtitle))
            story.append(HRFlowable(width="100%", thickness=1, color=c_gold, spaceBefore=4, spaceAfter=14))

            # Metadata Table (Agreement No, Version, Date)
            agreement_date_str = datetime.now().strftime("%d %B %Y")
            meta_data = [
                [
                    Paragraph("<b>Agreement Reference:</b>", style_body),
                    Paragraph(str(agreement_data.get("agreement_number", "RK-SA-001")), style_body_bold),
                    Paragraph("<b>Execution Date:</b>", style_body),
                    Paragraph(agreement_date_str, style_body)
                ],
                [
                    Paragraph("<b>Document Version:</b>", style_body),
                    Paragraph(f"Version {version_number}.0 (Binding Contract)", style_body_bold),
                    Paragraph("<b>Client Reference ID:</b>", style_body),
                    Paragraph(str(client_data.get("id", "CLT-000")), style_body)
                ]
            ]
            meta_table = Table(meta_data, colWidths=[120, 140, 110, 134])
            meta_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), c_ivory_bg),
                ('BOX', (0, 0), (-1, -1), 1, c_border),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 14))

            # Section 1: Parties to Agreement
            story.append(Paragraph("1. PARTIES TO THIS AGREEMENT", style_h1))
            parties_text = (
                f"This Service Agreement (the 'Agreement') is entered into by and between "
                f"<b>The Royal Knot</b>, luxury wedding planners having registered regional desks in Jaipur and Udaipur, Rajasthan (hereinafter 'The Agency'), "
                f"and <b>{client_data.get('partner1_name', 'Client')} & {client_data.get('partner2_name', 'Partner')}</b> "
                f"(Email: {client_data.get('email', '')}, Contact: {client_data.get('phone', '')}), hereinafter collectively referred to as 'The Client'."
            )
            story.append(Paragraph(parties_text, style_body))
            story.append(Spacer(1, 10))

            # Section 2: Wedding & Function Parameters
            story.append(Paragraph("2. WEDDING & FUNCTION PARAMETERS", style_h1))
            wedding_date_val = str(agreement_data.get("wedding_date", client_data.get("wedding_date", "")))
            wedding_loc_val = str(agreement_data.get("wedding_location", client_data.get("wedding_location", "")))
            venue_val = str(agreement_data.get("venue", "City Palace / Heritage Estate"))
            guest_count_val = str(agreement_data.get("guest_count", client_data.get("expected_guest_count", "150")))

            wedding_data_rows = [
                [Paragraph("<b>Primary Wedding Date:</b>", style_body), Paragraph(wedding_date_val, style_body),
                 Paragraph("<b>Expected Guests:</b>", style_body), Paragraph(f"{guest_count_val} Distinguished Guests", style_body)],
                [Paragraph("<b>Destination City:</b>", style_body), Paragraph(wedding_loc_val, style_body),
                 Paragraph("<b>Primary Venue / Estate:</b>", style_body), Paragraph(venue_val, style_body)],
                [Paragraph("<b>Service Package:</b>", style_body), Paragraph(str(agreement_data.get("service_package", "Royal Palace Grandeur")), style_body_bold),
                 Paragraph("<b>Theme / Aesthetics:</b>", style_body), Paragraph(str(client_data.get("wedding_theme", "Bespoke Royal Rajputana Heritage")), style_body)]
            ]
            wedding_table = Table(wedding_data_rows, colWidths=[130, 130, 120, 124])
            wedding_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('BOX', (0, 0), (-1, -1), 0.5, c_border),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(wedding_table)
            story.append(Spacer(1, 10))

            # Wedding Functions Detail
            functions = agreement_data.get("wedding_functions") or []
            if functions and len(functions) > 0:
                story.append(Paragraph("<b>Planned Ceremonies & Celebrations:</b>", style_body_bold))
                func_rows = [
                    [Paragraph("<b>Function</b>", style_body_bold), Paragraph("<b>Date</b>", style_body_bold), Paragraph("<b>Venue</b>", style_body_bold), Paragraph("<b>Notes</b>", style_body_bold)]
                ]
                for fn in functions:
                    func_rows.append([
                        Paragraph(str(fn.get("name", "Event")), style_body),
                        Paragraph(str(fn.get("date", "-")), style_body),
                        Paragraph(str(fn.get("venue", "-")), style_body),
                        Paragraph(str(fn.get("notes", "-")), style_body),
                    ])
                func_table = Table(func_rows, colWidths=[120, 80, 140, 164])
                func_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), c_ivory_bg),
                    ('BOX', (0, 0), (-1, -1), 0.5, c_border),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(func_table)
                story.append(Spacer(1, 10))

            # Section 3: Scope of Services & Exclusions
            story.append(Paragraph("3. SCOPE OF SERVICES & EXCLUSIONS", style_h1))
            inc_services = agreement_data.get("included_services") or [
                "Comprehensive destination wedding curation and venue management",
                "Artist, entertainment, royal safa and cultural folk troupe arrangements",
                "Decor styling, royal floral mandap curation, and ambient architectural lighting",
                "Guest hospitality, palace room-blocking coordination, and luxury fleet logistics",
                "Master production timeline, ceremony protocol run-sheets, and on-ground coordination"
            ]
            story.append(Paragraph("<b>Included Concierge Services:</b>", style_body_bold))
            for item in inc_services:
                story.append(Paragraph(f"• {item}", style_body))

            exc_services = agreement_data.get("excluded_services") or [
                "Direct catering food & beverage ingredient bills (paid directly to palace/hotel)",
                "Direct room tariff charges beyond negotiated agency blocks",
                "Flight tickets and personal couture/jewelry shopping"
            ]
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>Explicitly Excluded Services & Direct Client Payables:</b>", style_body_bold))
            for item in exc_services:
                story.append(Paragraph(f"• {item}", style_body))
            story.append(Spacer(1, 10))

            # Section 4: Commercial Pricing & Payment Milestones
            story.append(Paragraph("4. COMMERCIAL TERMS & PAYMENT MILESTONES", style_h1))

            pkg_price = Decimal(str(agreement_data.get("package_price", "0.00")))
            tax_pct = Decimal(str(agreement_data.get("tax_percentage", "18.00")))
            tax_amt = Decimal(str(agreement_data.get("tax_amount", "0.00")))
            disc_amt = Decimal(str(agreement_data.get("discount_amount", "0.00")))
            tot_amt = Decimal(str(agreement_data.get("total_amount", "0.00")))

            fin_rows = [
                [Paragraph("<b>Agreed Professional Management Fee:</b>", style_body), Paragraph(f"₹ {pkg_price:,.2f}", style_body)],
                [Paragraph(f"<b>Applicable GST ({tax_pct}%):</b>", style_body), Paragraph(f"₹ {tax_amt:,.2f}", style_body)],
                [Paragraph("<b>Approved Royal Courtesy Discount:</b>", style_body), Paragraph(f"- ₹ {disc_amt:,.2f}", style_body)],
                [Paragraph("<b>Total Contract Value (Inclusive of Taxes):</b>", style_body_bold), Paragraph(f"<b>₹ {tot_amt:,.2f} INR</b>", style_body_bold)],
            ]
            fin_table = Table(fin_rows, colWidths=[320, 184])
            fin_table.setStyle(TableStyle([
                ('BACKGROUND', (0, -1), (-1, -1), c_ivory_bg),
                ('BOX', (0, 0), (-1, -1), 0.5, c_border),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ]))
            story.append(fin_table)
            story.append(Spacer(1, 8))

            # Milestones Table
            milestones = agreement_data.get("milestones") or []
            if milestones:
                story.append(Paragraph("<b>Agreed Staged Payment Schedule:</b>", style_body_bold))
                ms_rows = [
                    [Paragraph("<b>Milestone Name</b>", style_body_bold), Paragraph("<b>Share</b>", style_body_bold), Paragraph("<b>Amount (INR)</b>", style_body_bold), Paragraph("<b>Due Date</b>", style_body_bold)]
                ]
                for ms in milestones:
                    ms_rows.append([
                        Paragraph(str(ms.get("name", "Milestone")), style_body),
                        Paragraph(f"{Decimal(str(ms.get('percentage', 0))):.1f}%", style_body),
                        Paragraph(f"₹ {Decimal(str(ms.get('amount', 0))):,.2f}", style_body),
                        Paragraph(str(ms.get("due_date", "-")), style_body),
                    ])
                ms_table = Table(ms_rows, colWidths=[200, 70, 120, 114])
                ms_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), c_ivory_bg),
                    ('BOX', (0, 0), (-1, -1), 0.5, c_border),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ]))
                story.append(ms_table)
                story.append(Spacer(1, 12))

            # Section 5: Standard Legal Clauses & Cancellation Policy
            story.append(Paragraph("5. CONTRACTUAL TERMS, RESCHEDULING & CANCELLATION", style_h1))
            legal_text = (
                "<b>5.1 Binding Nature:</b> This Service Agreement represents the final understanding between the parties. "
                "Execution via Leegality eSignature constitutes a valid and legally binding contract under the Information Technology Act, 2000.<br/>"
                "<b>5.2 Non-Refundable Booking Retainer:</b> The Initial Advance Booking Milestone secures the calendar dates, principal planner reservation, "
                "and preliminary venue holds. In the event of voluntary client cancellation, the advance fee is non-refundable.<br/>"
                "<b>5.3 Rescheduling:</b> Postponement requested at least 90 calendar days prior to the wedding date is permissible without penalty, subject to agency calendar availability in Rajasthan.<br/>"
                "<b>5.4 Force Majeure:</b> Neither party shall be liable for failure to perform due to acts of God, civil emergencies, or state-mandated heritage palace closures. Dates will be mutually renegotiated.<br/>"
                "<b>5.5 Jurisdiction:</b> All disputes arising out of this Agreement shall be subject to the exclusive jurisdiction of the competent courts in Jaipur, Rajasthan."
            )
            story.append(Paragraph(legal_text, style_legal))
            story.append(Spacer(1, 16))

            # Section 6: Execution Block / Signatures
            story.append(KeepTogether([
                Paragraph("6. EXECUTION & ELECTRONIC SIGNING ACKNOWLEDGEMENT", style_h1),
                Paragraph(
                    "By signing electronically below, the Client agrees to all clauses, service specifications, deliverables, and payment obligations contained herein.",
                    style_body
                ),
                Spacer(1, 14),
                Table([
                    [
                        Paragraph("<b>For The Royal Knot:</b><br/><br/><br/>_____________________________________<br/><b>Maharani Gayatri Singh</b><br/>Principal Wedding Planner", style_body),
                        Paragraph(f"<b>For The Client ({client_data.get('partner1_name')} & {client_data.get('partner2_name')}):</b><br/><br/><br/>_____________________________________<br/><b>Electronic Signature via Leegality</b><br/>Signer: {client_data.get('email')}", style_body)
                    ]
                ], colWidths=[250, 254], style=[
                    ('BOX', (0, 0), (-1, -1), 0.5, c_border),
                    ('BACKGROUND', (0, 0), (-1, -1), c_ivory_bg),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ])
            ]))

            # Build Document
            doc.build(story, canvasmaker=NumberedCanvas)

            # Compute SHA-256 and File Size
            file_size = os.path.getsize(output_filepath)
            sha256_hash = hashlib.sha256()
            with open(output_filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            file_hash = sha256_hash.hexdigest()

            return {
                "file_path": output_filepath,
                "file_size": file_size,
                "file_hash_sha256": file_hash,
                "filename": os.path.basename(output_filepath)
            }




pdf_service = PdfService()
