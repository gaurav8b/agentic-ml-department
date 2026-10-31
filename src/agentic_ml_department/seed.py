"""Create a deterministic fictional-company dataset for the demonstration."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
import numpy as np

from .db import SessionLocal
from .models import Base, Campaign, Customer, Lead, SalesOrder, SupportTicket

COMPANY_NAME = "Northstar Office & Cloud"  # Entirely fictional demonstration company.


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-20.0, min(20.0, x))))


def seed_demo_data(force: bool = False) -> dict:
    """Seed business systems once; force=True replaces only synthetic demo rows."""
    db = SessionLocal()
    try:
        existing = db.query(Customer).count()
        if existing and not force:
            return {"seeded": False, "reason": "Demo data already exists", "customers": existing}
        if force:
            for model in (SupportTicket, SalesOrder, Campaign, Lead, Customer):
                db.query(model).delete()
            db.commit()

        rng = np.random.default_rng(20261031)
        now = datetime.now(timezone.utc)
        regions = ["North", "South", "East", "West", "Central"]
        segments = ["Small Business", "Mid-Market", "Enterprise"]
        channels = ["Organic", "Paid Search", "Referral", "Partner", "Events"]
        plans = ["Starter", "Growth", "Business", "Enterprise"]
        contracts = ["Monthly", "Annual", "Two-Year"]
        industries = ["Technology", "Healthcare", "Retail", "Manufacturing", "Professional Services"]

        customers: list[Customer] = []
        customer_refs: list[str] = []
        for i in range(1, 701):
            tenure = int(rng.integers(1, 73))
            spend = float(np.round(rng.lognormal(5.0, 0.62), 2))
            inactive = int(rng.integers(0, 100))
            tickets = int(rng.poisson(1.7))
            satisfaction = float(np.clip(rng.normal(7.1, 1.65), 1, 10))
            contract = str(rng.choice(contracts, p=[0.48, 0.40, 0.12]))
            plan = str(rng.choice(plans, p=[0.25, 0.36, 0.28, 0.11]))
            channel = str(rng.choice(channels))
            logit = (
                -2.20
                + 0.035 * max(0, inactive - 25)
                + 0.32 * tickets
                - 0.38 * (satisfaction - 5.0)
                - (0.75 if contract == "Annual" else 1.05 if contract == "Two-Year" else 0.0)
                + (0.30 if plan == "Starter" else 0.0)
            )
            is_current = i > 500
            churned = False if is_current else bool(rng.random() < _sigmoid(logit))
            ref = f"CUS-{i:05d}"
            customer_refs.append(ref)
            customers.append(Customer(
                customer_ref=ref,
                signup_date=now - timedelta(days=tenure * 30),
                region=str(rng.choice(regions)),
                segment=str(rng.choice(segments, p=[0.48, 0.34, 0.18])),
                acquisition_channel=channel,
                plan_type=plan,
                contract_type=contract,
                tenure_months=tenure,
                monthly_spend=spend,
                days_since_last_purchase=inactive,
                support_tickets_90d=tickets,
                satisfaction_score=satisfaction,
                churned=churned, is_current=is_current,
            ))
        db.add_all(customers)

        leads: list[Lead] = []
        for i in range(1, 901):
            source = str(rng.choice(channels))
            industry = str(rng.choice(industries))
            size = int(rng.choice([5, 15, 40, 90, 180, 450, 1200], p=[.10, .16, .18, .18, .17, .13, .08]))
            budget = float(np.round(rng.lognormal(9.2, .72), 2))
            visits = int(rng.poisson(5) + 1)
            engagement = float(np.clip(rng.beta(2.1, 2.3), 0, 1))
            touchpoints = int(rng.integers(0, 12))
            source_bonus = {"Referral": .65, "Partner": .48, "Events": .18}.get(source, 0.0)
            logit = -2.25 + .16 * visits + 2.0 * engagement + .14 * touchpoints + .000012 * budget + source_bonus + (.35 if size > 100 else 0)
            is_open = i > 650
            converted = False if is_open else bool(rng.random() < _sigmoid(logit))
            deal_value = float(np.round(max(1200, budget * rng.uniform(.55, 1.8)), 2))
            leads.append(Lead(
                lead_ref=f"LED-{i:05d}",
                created_at=now - timedelta(days=int(rng.integers(0, 240))),
                lead_source=source,
                industry=industry,
                company_size=size,
                budget_usd=budget,
                website_visits_30d=visits,
                email_engagement=engagement,
                sales_touchpoints=touchpoints,
                converted=converted, is_open=is_open,
                estimated_deal_value=deal_value,
            ))
        db.add_all(leads)

        categories = ["Furniture", "Hardware", "Software", "Services", "Supplies"]
        orders: list[SalesOrder] = []
        for i in range(1, 2201):
            cust_ref = str(rng.choice(customer_refs))
            day_offset = int(rng.integers(0, 365))
            order_value = float(np.round(rng.lognormal(5.3, .78), 2))
            orders.append(SalesOrder(
                order_ref=f"ORD-{i:06d}", customer_ref=cust_ref,
                order_date=now - timedelta(days=day_offset),
                category=str(rng.choice(categories)), order_value=order_value,
                discount_pct=float(np.round(rng.choice([0, 0, 5, 10, 15, 20]), 2)),
                status=str(rng.choice(["fulfilled", "fulfilled", "fulfilled", "returned", "cancelled"], p=[.77, .08, .05, .06, .04])),
            ))
        db.add_all(orders)

        tickets: list[SupportTicket] = []
        for i in range(1, 641):
            cust_ref = str(rng.choice(customer_refs))
            tickets.append(SupportTicket(
                ticket_ref=f"TCK-{i:05d}", customer_ref=cust_ref,
                opened_at=now - timedelta(days=int(rng.integers(0, 120))),
                category=str(rng.choice(["Billing", "Product", "Delivery", "Technical", "Account"])),
                priority=str(rng.choice(["Low", "Medium", "High", "Urgent"], p=[.35, .42, .18, .05])),
                resolved_hours=float(np.round(rng.lognormal(2.2, .8), 2)),
                satisfaction_after=float(np.clip(rng.normal(7.0, 1.8), 1, 10)),
            ))
        db.add_all(tickets)

        campaigns = []
        for i in range(1, 13):
            spend = float(np.round(rng.uniform(2500, 28000), 2))
            campaigns.append(Campaign(
                campaign_ref=f"CAM-{i:03d}", channel=str(rng.choice(channels)),
                objective=str(rng.choice(["Lead generation", "Retention", "Upsell"])),
                spend_usd=spend, leads_generated=int(rng.integers(30, 180)),
                start_date=now - timedelta(days=int(rng.integers(15, 330))),
            ))
        db.add_all(campaigns)
        db.commit()
        return {
            "seeded": True,
            "company": COMPANY_NAME,
            "customers": len(customers),
            "leads": len(leads),
            "orders": len(orders),
            "support_tickets": len(tickets),
            "campaigns": len(campaigns),
            "note": "All records are synthetic; no real people or businesses are represented.",
        }
    finally:
        db.close()
