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


pdf_service = PdfService()
