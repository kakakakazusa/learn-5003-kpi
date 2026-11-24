# -*- coding: utf-8 -*-
"""经营分析接口（业务库）。

- GET /api/health
- GET /api/analytics/overview
"""
from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy import func, text

from extensions import db
from models import EmployeeKPIRecord, SalesRecord

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api")


def _sum_metrics(start_date, end_date):
    row = (
        db.session.query(
            func.coalesce(func.sum(SalesRecord.revenue), 0).label("revenue"),
            func.coalesce(func.sum(SalesRecord.order_count), 0).label("orders"),
        )
        .filter(SalesRecord.sale_date >= start_date, SalesRecord.sale_date <= end_date)
        .one()
    )
    return {"revenue": Decimal(str(row.revenue)), "orders": int(row.orders)}


def _percent_change(current, previous):
    if previous == 0:
        return None
    return round(float((current - previous) / previous * 100), 1)


def _money(value):
    return round(float(value), 2)


def _shift_months(value, months):
    month_index = value.year * 12 + value.month - 1 + months
    year, month_zero = divmod(month_index, 12)
    return date(year, month_zero + 1, 1)


def _period_start(end_date, period):
    if period == "week":
        week_start = end_date - timedelta(days=end_date.weekday())
        return week_start - timedelta(days=11 * 7)
    if period == "month":
        return _shift_months(date(end_date.year, end_date.month, 1), -11)
    if period == "quarter":
        current_quarter = (end_date.month - 1) // 3 * 3 + 1
        current_start = date(end_date.year, current_quarter, 1)
        return _shift_months(current_start, -21)
    if period == "halfyear":
        current_half = 1 if end_date.month <= 6 else 7
        current_start = date(end_date.year, current_half, 1)
        return _shift_months(current_start, -30)
    if period == "year":
        return date(end_date.year - 4, 1, 1)
    raise ValueError("period")


def _bucket_info(sale_date, period):
    if period == "week":
        week_start = sale_date - timedelta(days=sale_date.weekday())
        iso = week_start.isocalendar()
        return week_start, f"{iso.year}-W{iso.week:02d}"
    if period == "month":
        return date(sale_date.year, sale_date.month, 1), f"{sale_date.year}-{sale_date.month:02d}"
    if period == "quarter":
        quarter = (sale_date.month - 1) // 3 + 1
        return date(sale_date.year, (quarter - 1) * 3 + 1, 1), f"{sale_date.year}-Q{quarter}"
    if period == "halfyear":
        half = 1 if sale_date.month <= 6 else 2
        return date(sale_date.year, 1 if half == 1 else 7, 1), f"{sale_date.year}-H{half}"
    if period == "year":
        return date(sale_date.year, 1, 1), str(sale_date.year)
    raise ValueError("period")


def _period_buckets(start_date, end_date, period):
    buckets = {}
    current = start_date
    while current <= end_date:
        key, label = _bucket_info(current, period)
        buckets[key] = {"key": key, "label": label, "revenue": 0.0, "orders": 0}
        if period == "week":
            current = current + timedelta(days=7)
        elif period == "month":
            current = _shift_months(current, 1)
        elif period == "quarter":
            current = _shift_months(current, 3)
        elif period == "halfyear":
            current = _shift_months(current, 6)
        else:
            current = date(current.year + 1, 1, 1)
    return buckets


def _employee_metrics(start_date, end_date):
    rows = (
        db.session.query(
            func.count(func.distinct(EmployeeKPIRecord.employee_name)).label("employees"),
            func.coalesce(func.sum(EmployeeKPIRecord.revenue), 0).label("revenue"),
            func.coalesce(func.sum(EmployeeKPIRecord.revenue_target), 0).label("revenue_target"),
            func.coalesce(func.sum(EmployeeKPIRecord.orders), 0).label("orders"),
            func.coalesce(func.avg(EmployeeKPIRecord.satisfaction), 0).label("satisfaction"),
        )
        .filter(
            EmployeeKPIRecord.record_date >= start_date,
            EmployeeKPIRecord.record_date <= end_date,
        )
        .one()
    )
    revenue = Decimal(str(rows.revenue))
    revenue_target = Decimal(str(rows.revenue_target))
    employees = int(rows.employees or 0)
    orders = int(rows.orders or 0)
    completion = float(revenue / revenue_target * 100) if revenue_target else 0
    return {
        "employees": employees,
        "revenue": revenue,
        "revenue_target": revenue_target,
        "completion": round(completion, 1),
        "orders": orders,
        "average_revenue": revenue / employees if employees else Decimal("0"),
        "satisfaction": round(float(rows.satisfaction or 0), 1),
    }


@analytics_bp.get("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify(code=0, message="ok", data={"service": "flask-backend", "database": "connected"})


@analytics_bp.get("/analytics/overview")
def analytics_overview():
    period = request.args.get("period", "month")
    if period not in {"week", "month", "quarter", "halfyear", "year"}:
        return jsonify(code=400, message="period 必须是 week、month、quarter、halfyear 或 year", data=None), 400

    end_date = date.today()
    start_date = _period_start(end_date, period)
    range_days = (end_date - start_date).days + 1
    previous_end = start_date - timedelta(days=1)
    previous_start = previous_end - timedelta(days=range_days - 1)
    current = _sum_metrics(start_date, end_date)
    previous = _sum_metrics(previous_start, previous_end)
    current_average = current["revenue"] / current["orders"] if current["orders"] else Decimal("0")
    previous_average = previous["revenue"] / previous["orders"] if previous["orders"] else Decimal("0")
    employee_current = _employee_metrics(start_date, end_date)
    employee_previous = _employee_metrics(previous_start, previous_end)
    employee_revenue_change = _percent_change(employee_current["revenue"], employee_previous["revenue"])
    employee_orders_change = _percent_change(employee_current["orders"], employee_previous["orders"])
    employee_satisfaction_change = round(
        employee_current["satisfaction"] - employee_previous["satisfaction"],
        1,
    ) if employee_previous["employees"] else None

    daily_rows = (
        db.session.query(
            SalesRecord.sale_date,
            func.sum(SalesRecord.revenue).label("revenue"),
            func.sum(SalesRecord.order_count).label("orders"),
        )
        .filter(SalesRecord.sale_date >= start_date, SalesRecord.sale_date <= end_date)
        .group_by(SalesRecord.sale_date)
        .order_by(SalesRecord.sale_date)
        .all()
    )
    buckets = _period_buckets(start_date, end_date, period)
    for row in daily_rows:
        bucket_key, _ = _bucket_info(row.sale_date, period)
        if bucket_key in buckets:
            buckets[bucket_key]["revenue"] += _money(row.revenue)
            buckets[bucket_key]["orders"] += int(row.orders)
    trend = [
        {
            "date": bucket["key"].isoformat(),
            "label": bucket["label"],
            "revenue": round(bucket["revenue"], 2),
            "target": round(bucket["revenue"] * 1.08, 2),
            "orders": bucket["orders"],
        }
        for bucket in buckets.values()
    ]

    category_rows = (
        db.session.query(
            SalesRecord.category.label("name"),
            func.sum(SalesRecord.revenue).label("revenue"),
            func.sum(SalesRecord.order_count).label("orders"),
        )
        .filter(SalesRecord.sale_date >= start_date, SalesRecord.sale_date <= end_date)
        .group_by(SalesRecord.category)
        .order_by(func.sum(SalesRecord.revenue).desc())
        .all()
    )
    region_rows = (
        db.session.query(
            SalesRecord.region.label("name"),
            func.sum(SalesRecord.revenue).label("revenue"),
            func.sum(SalesRecord.order_count).label("orders"),
        )
        .filter(SalesRecord.sale_date >= start_date, SalesRecord.sale_date <= end_date)
        .group_by(SalesRecord.region)
        .order_by(func.sum(SalesRecord.revenue).desc())
        .all()
    )
    recent_rows = (
        SalesRecord.query.filter(
            SalesRecord.sale_date >= start_date,
            SalesRecord.sale_date <= end_date,
        )
        .order_by(SalesRecord.sale_date.desc(), SalesRecord.id.desc())
        .limit(8)
        .all()
    )
    employee_rows = (
        db.session.query(
            EmployeeKPIRecord.employee_name.label("name"),
            EmployeeKPIRecord.department.label("department"),
            func.sum(EmployeeKPIRecord.revenue).label("revenue"),
            func.sum(EmployeeKPIRecord.revenue_target).label("revenue_target"),
            func.sum(EmployeeKPIRecord.orders).label("orders"),
            func.avg(EmployeeKPIRecord.satisfaction).label("satisfaction"),
        )
        .filter(
            EmployeeKPIRecord.record_date >= start_date,
            EmployeeKPIRecord.record_date <= end_date,
        )
        .group_by(EmployeeKPIRecord.employee_name, EmployeeKPIRecord.department)
        .order_by(func.sum(EmployeeKPIRecord.revenue).desc())
        .limit(8)
        .all()
    )
    regions_count = (
        db.session.query(func.count(func.distinct(SalesRecord.region)))
        .filter(SalesRecord.sale_date >= start_date, SalesRecord.sale_date <= end_date)
        .scalar()
    )

    data = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "period": period,
        "metrics": {
            "revenue": _money(current["revenue"]),
            "revenue_change": _percent_change(current["revenue"], previous["revenue"]),
            "revenue_target": _money(previous["revenue"] * Decimal("1.08")) if previous["revenue"] else _money(current["revenue"] * Decimal("1.08")),
            "revenue_completion": round(float(current["revenue"] / (previous["revenue"] * Decimal("1.08") if previous["revenue"] else current["revenue"] * Decimal("1.08"))) * 100, 1),
            "orders": current["orders"],
            "orders_change": _percent_change(current["orders"], previous["orders"]),
            "orders_target": int(previous["orders"] * 1.05) if previous["orders"] else int(current["orders"] * 1.05),
            "orders_completion": round(current["orders"] / (previous["orders"] * 1.05 if previous["orders"] else current["orders"] * 1.05) * 100, 1),
            "average_order_value": _money(current_average),
            "average_order_value_change": _percent_change(current_average, previous_average),
            "average_order_value_target": _money(previous_average * Decimal("1.03")) if previous_average else _money(current_average * Decimal("1.03")),
            "average_order_value_completion": round(float(current_average / (previous_average * Decimal("1.03") if previous_average else current_average * Decimal("1.03"))) * 100, 1),
            "regions": regions_count or 0,
            "regions_target": max(regions_count or 0, 5),
            "regions_completion": 100.0 if (regions_count or 0) >= 5 else round((regions_count or 0) / 5 * 100, 1),
        },
        "trend": trend,
        "categories": [
            {"name": row.name, "revenue": _money(row.revenue), "orders": int(row.orders)}
            for row in category_rows
        ],
        "regions": [
            {"name": row.name, "revenue": _money(row.revenue), "orders": int(row.orders)}
            for row in region_rows
        ],
        "recent": [
            {
                "date": row.sale_date.isoformat(),
                "category": row.category,
                "region": row.region,
                "revenue": _money(row.revenue),
                "orders": row.order_count,
            }
            for row in recent_rows
        ],
    }
    return jsonify(code=0, message="ok", data=data)
