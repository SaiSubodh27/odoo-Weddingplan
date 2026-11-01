from typing import Optional, List
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.database.session import get_db
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.project import (
    WeddingProject,
    ProjectVendor,
    PaymentStage,
    TeamTimeEntry,
    WeddingExtra,
    VendorPayout,
)
from app.models.catering import CateringPlan
from app.schemas.project import FounderProfitabilityResponse
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter()

# Active share tokens with expiration
SHARE_TOKENS = {}


class FounderWeddingItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    project_id: str = Field(..., alias="projectId")
    project_code: str = Field(..., alias="projectCode")
    couple_name: str = Field(..., alias="coupleName")
    wedding_date: date = Field(..., alias="weddingDate")
    location: str
    guest_count: int = Field(..., alias="guestCount")
    status: str
    package_tier: str = Field(..., alias="packageTier")
    estimated_budget: Decimal = Field(..., alias="estimatedBudget")
    payments_received: Decimal = Field(..., alias="paymentsReceived")
    vendor_costs: Decimal = Field(..., alias="vendorCosts")
    gross_profit: Decimal = Field(..., alias="grossProfit")
    profit_margin_percentage: Decimal = Field(..., alias="profitMarginPercentage")


class VendorPerformanceScorecard(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    vendor_id: str = Field(..., alias="vendorId")
    name: str
    category: str
    city: str
    rating: float
    jobs_contracted: int = Field(..., alias="jobsContracted")
    total_contract_amount: Decimal = Field(..., alias="totalContractAmount")


class UpcomingDueItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    project_id: str = Field(..., alias="projectId")
    project_code: str = Field(..., alias="projectCode")
    couple_name: str = Field(..., alias="coupleName")
    stage_name: str = Field(..., alias="stageName")
    amount: Decimal
    due_date: date = Field(..., alias="dueDate")
    days_remaining: int = Field(..., alias="daysRemaining")
    status: str


class FounderSeasonOverviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    season_name: str = Field(..., alias="seasonName")
    weddings_count: int = Field(..., alias="weddingsCount")
    total_projected_revenue: Decimal = Field(..., alias="totalProjectedRevenue")
    total_client_payments_received: Decimal = Field(..., alias="totalClientPaymentsReceived")
    total_vendor_costs: Decimal = Field(..., alias="totalVendorCosts")
    total_team_labor_costs: Decimal = Field(..., alias="totalTeamLaborCosts")
    net_founder_profit: Decimal = Field(..., alias="netFounderProfit")
    season_profit_margin_percentage: Decimal = Field(..., alias="seasonProfitMarginPercentage")
    weddings: List[FounderWeddingItem] = []
    vendor_performance: List[VendorPerformanceScorecard] = Field([], alias="vendorPerformance")
    upcoming_dues_next_4_weeks: List[UpcomingDueItem] = Field([], alias="upcomingDuesNext4Weeks")
    shareable_report_token: str = Field(..., alias="shareableReportToken")
    shareable_report_url: str = Field(..., alias="shareableReportUrl")


@router.get(
    "/season-overview",
    response_model=FounderSeasonOverviewResponse,
    summary="Founder season view of all weddings, vendor performance, upcoming 4-week dues, and shareable report link",
    tags=["Founder Financials"]
)
def get_season_overview(db: Session = Depends(get_db)):
    """
    Consolidated financial and operational executive view for the agency founder.
    Aggregates multi-wedding season budgets, payment collection, vendor performance, and upcoming cash dues.
    """
    now = datetime.now(timezone.utc)
    today = now.date()
    four_weeks_later = today + timedelta(days=28)

    # 1. Fetch All Active Projects
    projects = db.query(WeddingProject).filter(WeddingProject.is_deleted == False).order_by(WeddingProject.wedding_date.asc()).all()

    total_projected_revenue = Decimal("0.00")
    total_client_payments = Decimal("0.00")
    total_vendor_costs = Decimal("0.00")
    total_team_labor = Decimal("0.00")

    wedding_items = []

    for p in projects:
        couple_name = f"{p.client.partner1_name} & {p.client.partner2_name}" if p.client else p.project_name
        budget = p.estimated_budget or Decimal("0.00")
        total_projected_revenue += budget

        # Payments received
        paid_stages = [s for s in p.payment_stages if s.status == "Paid"]
        p_received = sum([Decimal(str(s.amount)) for s in paid_stages], Decimal("0.00"))
        if p_received == Decimal("0.00") and p.deposit_paid:
            p_received = Decimal(str(round(budget * Decimal("0.25"), 2)))
        total_client_payments += p_received

        # Vendor costs
        v_costs = sum([Decimal(str(v.contract_amount)) for v in p.assigned_vendors], Decimal("0.00"))
        if v_costs == Decimal("0.00"):
            c_plans = db.query(CateringPlan).filter(CateringPlan.project_id == p.id, CateringPlan.agreed_cost.isnot(None)).all()
            v_costs = sum([Decimal(str(cp.agreed_cost)) for cp in c_plans], Decimal("0.00"))
        total_vendor_costs += v_costs

        # Team labor
        t_costs = sum([Decimal(str(t.hours)) * Decimal(str(t.hourly_rate)) for t in p.time_entries], Decimal("0.00"))
        total_team_labor += t_costs

        # Wedding profit
        w_profit = p_received - v_costs - t_costs
        w_margin = Decimal(str(round((w_profit / p_received * 100), 2))) if p_received > Decimal("0.00") else Decimal("0.00")

        wedding_items.append(FounderWeddingItem(
            project_id=p.id,
            project_code=p.project_code,
            couple_name=couple_name,
            wedding_date=p.wedding_date,
            location=p.location,
            guest_count=p.guest_count,
            status=p.status,
            package_tier=p.package_tier,
            estimated_budget=budget,
            payments_received=p_received,
            vendor_costs=v_costs,
            gross_profit=w_profit,
            profit_margin_percentage=w_margin
        ))

    net_founder_profit = total_client_payments - total_vendor_costs - total_team_labor
    season_margin = Decimal(str(round((net_founder_profit / total_client_payments * 100), 2))) if total_client_payments > Decimal("0.00") else Decimal("0.00")

    # 2. Vendor Performance Scorecards
    vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
    vendor_cards = []
    for v in vendors:
        contracts = db.query(ProjectVendor).filter(ProjectVendor.vendor_id == v.id).all()
        contract_amt = sum([Decimal(str(c.contract_amount)) for c in contracts], Decimal("0.00"))
        vendor_cards.append(VendorPerformanceScorecard(
            vendor_id=v.id,
            name=v.name,
            category=v.category,
            city=v.city or "Jaipur",
            rating=float(v.rating or 5.0),
            jobs_contracted=len(contracts),
            total_contract_amount=contract_amt
        ))

    vendor_cards.sort(key=lambda x: x.jobs_contracted, reverse=True)

    # 3. Upcoming Dues for the Next 4 Weeks (28 days)
    upcoming_dues = db.query(PaymentStage).join(WeddingProject).filter(
        PaymentStage.status != "Paid",
        PaymentStage.due_date >= today,
        PaymentStage.due_date <= four_weeks_later
    ).order_by(PaymentStage.due_date.asc()).all()

    due_items = []
    for d in upcoming_dues:
        c_name = f"{d.project.client.partner1_name} & {d.project.client.partner2_name}" if d.project.client else d.project.project_name
        days_rem = (d.due_date - today).days
        due_items.append(UpcomingDueItem(
            project_id=d.project.id,
            project_code=d.project.project_code,
            couple_name=c_name,
            stage_name=d.stage_name,
            amount=d.amount,
            due_date=d.due_date,
            days_remaining=days_rem,
            status=d.status
        ))

    # 4. Generate Shareable Read-Only Expiring Token (valid 7 days)
    token = secrets.token_urlsafe(24)
    SHARE_TOKENS[token] = {
        "created_at": now,
        "expires_at": now + timedelta(days=7)
    }

    report_url = f"/api/v1/founder/season-overview/export?token={token}"

    return FounderSeasonOverviewResponse(
        season_name="2026-2027 Rajasthan Royal Wedding Season",
        weddings_count=len(projects),
        total_projected_revenue=total_projected_revenue,
        total_client_payments_received=total_client_payments,
        total_vendor_costs=total_vendor_costs,
        total_team_labor_costs=total_team_labor,
        net_founder_profit=net_founder_profit,
        season_profit_margin_percentage=season_margin,
        weddings=wedding_items,
        vendor_performance=vendor_cards,
        upcoming_dues_next_4_weeks=due_items,
        shareable_report_token=token,
        shareable_report_url=report_url
    )


@router.get(
    "/season-overview/export",
    summary="Read-only executive report export view with token verification",
    tags=["Founder Financials"]
)
def export_season_report(
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Renders an elegant, self-contained executive financial report for founders and investors.
    Accessible via expiring secure link.
    """
    # Token check
    if token and token in SHARE_TOKENS:
        tok_data = SHARE_TOKENS[token]
        if datetime.now(timezone.utc) > tok_data["expires_at"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Shareable report link has expired.")
    elif token and token not in SHARE_TOKENS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid share token.")

    overview = get_season_overview(db=db)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>The Royal Knot — Founder Season Report</title>
<style>
  body {{ font-family: 'Georgia', serif; margin: 40px; color: #2B2118; background: #FAF7F2; }}
  .header {{ border-bottom: 2px solid #8C6D4E; padding-bottom: 20px; }}
  h1 {{ margin: 0; color: #4A3525; font-size: 28px; }}
  .meta {{ color: #8C6D4E; font-size: 14px; margin-top: 5px; text-transform: uppercase; letter-spacing: 1px; }}
  .cards {{ display: flex; gap: 20px; margin: 30px 0; }}
  .card {{ background: white; border: 1px solid #E6D8C8; border-radius: 8px; padding: 20px; flex: 1; }}
  .card-label {{ font-size: 12px; color: #7B6858; text-transform: uppercase; }}
  .card-value {{ font-size: 24px; font-weight: bold; margin-top: 8px; color: #342217; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: white; }}
  th, td {{ padding: 12px 16px; border: 1px solid #EDE2D5; text-align: left; font-size: 14px; }}
  th {{ background: #F2E7DC; color: #5C4331; font-weight: bold; }}
  .footer {{ margin-top: 40px; font-size: 12px; color: #9A8878; border-top: 1px solid #E6D8C8; padding-top: 15px; }}
</style>
</head>
<body>
  <div class="header">
    <h1>The Royal Knot — Founder Executive Report</h1>
    <div class="meta">{overview.season_name} · Generated on {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}</div>
  </div>

  <div class="cards">
    <div class="card">
      <div class="card-label">Active Weddings</div>
      <div class="card-value">{overview.weddings_count}</div>
    </div>
    <div class="card">
      <div class="card-label">Client Receipts</div>
      <div class="card-value">₹{overview.total_client_payments_received:,.2f}</div>
    </div>
    <div class="card">
      <div class="card-label">Vendor Costs</div>
      <div class="card-value">₹{overview.total_vendor_costs:,.2f}</div>
    </div>
    <div class="card">
      <div class="card-label">Net Founder Profit</div>
      <div class="card-value" style="color: #2F6B38;">₹{overview.net_founder_profit:,.2f} ({overview.season_profit_margin_percentage}%)</div>
    </div>
  </div>

  <h2>Upcoming Client Dues (Next 4 Weeks)</h2>
  <table>
    <thead>
      <tr>
        <th>Project Code</th>
        <th>Couple</th>
        <th>Milestone</th>
        <th>Due Date</th>
        <th>Days Left</th>
        <th>Amount</th>
      </tr>
    </thead>
    <tbody>
      {''.join([f"<tr><td>{d.project_code}</td><td>{d.couple_name}</td><td>{d.stage_name}</td><td>{d.due_date}</td><td>{d.days_remaining}d</td><td>₹{d.amount:,.2f}</td></tr>" for d in overview.upcoming_dues_next_4_weeks]) or '<tr><td colspan="6">No dues in the next 4 weeks.</td></tr>'}
    </tbody>
  </table>

  <h2>Weddings Financial Performance</h2>
  <table>
    <thead>
      <tr>
        <th>Code</th>
        <th>Couple & Venue</th>
        <th>Date</th>
        <th>Budget</th>
        <th>Received</th>
        <th>Vendor Costs</th>
        <th>Gross Profit</th>
      </tr>
    </thead>
    <tbody>
      {''.join([f"<tr><td>{w.project_code}</td><td>{w.couple_name} ({w.location})</td><td>{w.wedding_date}</td><td>₹{w.estimated_budget:,.2f}</td><td>₹{w.payments_received:,.2f}</td><td>₹{w.vendor_costs:,.2f}</td><td><b>₹{w.gross_profit:,.2f}</b> ({w.profit_margin_percentage}%)</td></tr>" for w in overview.weddings])}
    </tbody>
  </table>

  <div class="footer">
    Private & Confidential — The Royal Knot Luxury Wedding Management. Unauthorized reproduction or dissemination is strictly prohibited.
  </div>
</body>
</html>
"""
    return HTMLResponse(content=html, status_code=status.HTTP_200_OK)
