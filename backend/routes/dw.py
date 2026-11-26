# -*- coding: utf-8 -*-
"""Warehouse (5003) API.

- GET /api/dw/health
- GET /api/dw/meta
- GET /api/dw/kpi/pr
- GET /api/dw/kpi/ec
- GET /api/dw/board
- GET /api/dw/project/meta
- GET /api/dw/project/kpi
- GET /api/dw/project/board
"""
from flask import Blueprint, jsonify, request
from sqlalchemy import func

from cache import clear as cache_clear_prefix
from cache import get as cache_get
from cache import set as cache_set
from dw_models import (
    AdsEcKpi,
    AdsEcProjectKpi,
    AdsPrKpi,
    AdsPrProjectKpi,
    DimDepartment,
    DimDomain,
    DimEmployee,
    DimProject,
    DimTeam,
    DW_MODELS,
)
from extensions import db

dw_bp = Blueprint("dw", __name__, url_prefix="/api/dw")

ORG_TYPE_LABELS = {
    "employee": "Employee",
    "team": "Team",
    "domain": "Domain",
    "department": "Department",
}
PERIOD_TYPE_LABELS = {
    "week": "Week",
    "month": "Month",
    "quarter": "Quarter",
    "halfyear": "Half-year",
    "year": "Year",
}


def _float(value):
    return round(float(value), 4) if value is not None else None


def _org_name(org_type, org_id):
    if org_type == "employee":
        row = (
            db.session.query(DimEmployee.employee_name)
            .filter(DimEmployee.employee_id == org_id)
            .first()
        )
        return row[0] if row else None

    model_map = {
        "department": (DimDepartment, DimDepartment.department_id, DimDepartment.department_name),
        "team": (DimTeam, DimTeam.team_id, DimTeam.team_name),
        "domain": (DimDomain, DimDomain.domain_id, DimDomain.domain_name),
    }
    mapping = model_map.get(org_type)
    if not mapping:
        return None
    model, id_col, name_col = mapping
    row = (
        db.session.query(name_col)
        .filter(id_col == org_id, model.is_current == 1)
        .order_by(model.effective_date.desc())
        .first()
    )
    return row[0] if row else None


@dw_bp.get("/health")
def dw_health():
    counts = {
        model.__tablename__: db.session.query(func.count()).select_from(model).scalar()
        for model in DW_MODELS
    }
    return jsonify(code=0, message="ok", data={"database": "5003", "tables": counts})


@dw_bp.get("/meta")
def dw_meta():
    cache_key = "dw:meta"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(code=0, message="ok", data=cached)

    def list_dim(model, id_col, name_col, scd=True):
        query = db.session.query(id_col, name_col)
        if scd:
            query = query.filter(model.is_current == 1)
        rows = query.order_by(id_col).all()
        return [{"id": row[0], "name": row[1]} for row in rows]

    data = {
        "org_types": [
            {"value": key, "label": label} for key, label in ORG_TYPE_LABELS.items()
        ],
        "period_types": [
            {"value": key, "label": label} for key, label in PERIOD_TYPE_LABELS.items()
        ],
        "dimensions": {
            "department": list_dim(DimDepartment, DimDepartment.department_id, DimDepartment.department_name),
            "team": list_dim(DimTeam, DimTeam.team_id, DimTeam.team_name),
            "domain": list_dim(DimDomain, DimDomain.domain_id, DimDomain.domain_name),
            "employee": list_dim(DimEmployee, DimEmployee.employee_id, DimEmployee.employee_name, scd=False),
        },
    }
    cache_set(cache_key, data)
    return jsonify(code=0, message="ok", data=data)


@dw_bp.get("/kpi/pr")
def dw_kpi_pr():
    org_type = request.args.get("org_type")
    period_type = request.args.get("period_type")
    period_value = request.args.get("period_value")
    org_id = request.args.get("org_id", type=int)

    cache_key = f"dw:kpi:pr:{org_type}:{period_type}:{period_value}:{org_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(code=0, message="ok", data=cached)

    query = db.session.query(AdsPrKpi)
    if org_type:
        query = query.filter(AdsPrKpi.org_type == org_type)
    if period_type:
        query = query.filter(AdsPrKpi.period_type == period_type)
    if period_value:
        query = query.filter(AdsPrKpi.period_value == period_value)
    if org_id is not None:
        query = query.filter(AdsPrKpi.org_id == org_id)

    rows = query.order_by(
        AdsPrKpi.period_type, AdsPrKpi.period_value, AdsPrKpi.org_type, AdsPrKpi.org_id
    ).all()
    data = [
        {
            "period_type": row.period_type,
            "period_value": row.period_value,
            "org_type": row.org_type,
            "org_id": row.org_id,
            "org_name": _org_name(row.org_type, row.org_id),
            "assign_cnt": row.pr_assign_cnt,
            "complete_cnt": row.pr_complete_cnt,
            "completion_rate": _float(row.pr_completion_rate),
            "on_time_rate": _float(row.pr_on_time_rate),
            "avg_process_days": _float(row.pr_avg_process_days),
            "rework_rate": _float(row.pr_rework_rate),
            "work_hours_ratio": _float(row.pr_work_hours_ratio),
        }
        for row in rows
    ]
    cache_set(cache_key, data)
    return jsonify(code=0, message="ok", data=data)


@dw_bp.get("/kpi/ec")
def dw_kpi_ec():
    org_type = request.args.get("org_type")
    period_type = request.args.get("period_type")
    period_value = request.args.get("period_value")
    org_id = request.args.get("org_id", type=int)

    cache_key = f"dw:kpi:ec:{org_type}:{period_type}:{period_value}:{org_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(code=0, message="ok", data=cached)

    query = db.session.query(AdsEcKpi)
    if org_type:
        query = query.filter(AdsEcKpi.org_type == org_type)
    if period_type:
        query = query.filter(AdsEcKpi.period_type == period_type)
    if period_value:
        query = query.filter(AdsEcKpi.period_value == period_value)
    if org_id is not None:
        query = query.filter(AdsEcKpi.org_id == org_id)

    rows = query.order_by(
        AdsEcKpi.period_type, AdsEcKpi.period_value, AdsEcKpi.org_type, AdsEcKpi.org_id
    ).all()
    data = [
        {
            "period_type": row.period_type,
            "period_value": row.period_value,
            "org_type": row.org_type,
            "org_id": row.org_id,
            "org_name": _org_name(row.org_type, row.org_id),
            "found_cnt": row.ec_found_cnt,
            "resolved_cnt": row.ec_resolved_cnt,
            "resolution_rate": _float(row.ec_resolution_rate),
            "avg_response_minutes": _float(row.ec_avg_response_minutes),
            "avg_resolve_minutes": _float(row.ec_avg_resolve_minutes),
            "recur_rate": _float(row.ec_recur_rate),
            "severe_cnt": row.ec_severe_cnt,
        }
        for row in rows
    ]
    cache_set(cache_key, data)
    return jsonify(code=0, message="ok", data=data)


@dw_bp.get("/board")
def dw_board():
    org_type = request.args.get("org_type", "department")
    period_type = request.args.get("period_type", "month")
    if org_type not in ORG_TYPE_LABELS:
        return jsonify(code=400, message="org_type must be one of employee, team, domain, or department", data=None), 400
    if period_type not in PERIOD_TYPE_LABELS:
        return jsonify(code=400, message="period_type must be one of week, month, quarter, halfyear, or year", data=None), 400

    cache_key = f"dw:board:{org_type}:{period_type}"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(code=0, message="ok", data=cached)

    pr_rows = (
        db.session.query(AdsPrKpi)
        .filter(AdsPrKpi.org_type == org_type, AdsPrKpi.period_type == period_type)
        .order_by(AdsPrKpi.period_value.desc(), AdsPrKpi.pr_completion_rate.desc())
        .all()
    )
    ec_rows = (
        db.session.query(AdsEcKpi)
        .filter(AdsEcKpi.org_type == org_type, AdsEcKpi.period_type == period_type)
        .all()
    )
    ec_map = {(row.period_value, row.org_id): row for row in ec_rows}

    items = []
    for row in pr_rows:
        ec = ec_map.get((row.period_value, row.org_id))
        items.append({
            "period_type": row.period_type,
            "period_value": row.period_value,
            "org_type": row.org_type,
            "org_id": row.org_id,
            "org_name": _org_name(row.org_type, row.org_id),
            "pr": {
                "assign_cnt": row.pr_assign_cnt,
                "complete_cnt": row.pr_complete_cnt,
                "due_cnt": row.pr_due_cnt,
                "on_time_cnt": row.pr_on_time_cnt,
                "process_days_sum": row.pr_process_days_sum,
                "rework_cnt": row.pr_rework_cnt,
                "completion_rate": _float(row.pr_completion_rate),
                "on_time_rate": _float(row.pr_on_time_rate),
                "avg_process_days": _float(row.pr_avg_process_days),
                "rework_rate": _float(row.pr_rework_rate),
                "work_hours_ratio": _float(row.pr_work_hours_ratio),
            },
            "ec": {
                "found_cnt": ec.ec_found_cnt,
                "resolved_cnt": ec.ec_resolved_cnt,
                "response_minutes_sum": ec.ec_response_minutes_sum,
                "resolve_minutes_sum": ec.ec_resolve_minutes_sum,
                "recur_cnt": ec.ec_recur_cnt,
                "resolution_rate": _float(ec.ec_resolution_rate),
                "avg_response_minutes": _float(ec.ec_avg_response_minutes),
                "avg_resolve_minutes": _float(ec.ec_avg_resolve_minutes),
                "recur_rate": _float(ec.ec_recur_rate),
                "severe_cnt": ec.ec_severe_cnt,
            } if ec else None,
        })
    cache_set(cache_key, items)
    return jsonify(code=0, message="ok", data=items)


def _project_name(project_id):
    row = (
        db.session.query(DimProject.project_name)
        .filter(DimProject.project_id == project_id)
        .first()
    )
    return row[0] if row else None


@dw_bp.get("/project/meta")
def project_meta():
    cache_key = "dw:project:meta"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(code=0, message="ok", data=cached)
    rows = (
        db.session.query(DimProject.project_id, DimProject.project_name)
        .order_by(DimProject.project_id)
        .all()
    )
    data = [{"id": row[0], "name": row[1]} for row in rows]
    cache_set(cache_key, data)
    return jsonify(code=0, message="ok", data=data)


@dw_bp.get("/project/kpi")
def project_kpi():
    period_type = request.args.get("period_type")
    period_value = request.args.get("period_value")
    project_id = request.args.get("project_id", type=int)

    cache_key = f"dw:project:kpi:{period_type}:{period_value}:{project_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(code=0, message="ok", data=cached)

    query = db.session.query(AdsPrProjectKpi)
    if period_type:
        query = query.filter(AdsPrProjectKpi.period_type == period_type)
    if period_value:
        query = query.filter(AdsPrProjectKpi.period_value == period_value)
    if project_id is not None:
        query = query.filter(AdsPrProjectKpi.project_id == project_id)

    rows = query.order_by(
        AdsPrProjectKpi.period_type, AdsPrProjectKpi.period_value, AdsPrProjectKpi.project_id
    ).all()
    data = [
        {
            "period_type": row.period_type,
            "period_value": row.period_value,
            "project_id": row.project_id,
            "project_name": _project_name(row.project_id),
            "assign_cnt": row.pr_assign_cnt,
            "complete_cnt": row.pr_complete_cnt,
            "due_cnt": row.pr_due_cnt,
            "on_time_cnt": row.pr_on_time_cnt,
            "process_days_sum": row.pr_process_days_sum,
            "rework_cnt": row.pr_rework_cnt,
            "completion_rate": _float(row.pr_completion_rate),
            "on_time_rate": _float(row.pr_on_time_rate),
            "avg_process_days": _float(row.pr_avg_process_days),
            "rework_rate": _float(row.pr_rework_rate),
            "work_hours_ratio": _float(row.pr_work_hours_ratio),
        }
        for row in rows
    ]
    cache_set(cache_key, data)
    return jsonify(code=0, message="ok", data=data)


@dw_bp.get("/project/board")
def project_board():
    period_type = request.args.get("period_type", "month")
    if period_type not in PERIOD_TYPE_LABELS:
        return jsonify(code=400, message="period_type must be one of week, month, quarter, halfyear, or year", data=None), 400

    cache_key = f"dw:project:board:{period_type}"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(code=0, message="ok", data=cached)

    rows = (
        db.session.query(AdsPrProjectKpi)
        .filter(AdsPrProjectKpi.period_type == period_type)
        .order_by(AdsPrProjectKpi.period_value.desc(), AdsPrProjectKpi.pr_completion_rate.desc())
        .all()
    )
    data = [
        {
            "period_type": row.period_type,
            "period_value": row.period_value,
            "project_id": row.project_id,
            "project_name": _project_name(row.project_id),
            "assign_cnt": row.pr_assign_cnt,
            "complete_cnt": row.pr_complete_cnt,
            "due_cnt": row.pr_due_cnt,
            "on_time_cnt": row.pr_on_time_cnt,
            "process_days_sum": row.pr_process_days_sum,
            "rework_cnt": row.pr_rework_cnt,
            "completion_rate": _float(row.pr_completion_rate),
            "on_time_rate": _float(row.pr_on_time_rate),
            "avg_process_days": _float(row.pr_avg_process_days),
            "rework_rate": _float(row.pr_rework_rate),
            "work_hours_ratio": _float(row.pr_work_hours_ratio),
        }
        for row in rows
    ]
    cache_set(cache_key, data)
    return jsonify(code=0, message="ok", data=data)


@dw_bp.post("/cache/clear")
def cache_clear():
    cleared = cache_clear_prefix("dw:")
    return jsonify(code=0, message="ok", data={"cleared": cleared})


@dw_bp.get("/project/ec")
def project_ec():
    period_type = request.args.get("period_type")
    period_value = request.args.get("period_value")
    project_id = request.args.get("project_id", type=int)

    cache_key = f"dw:project:ec:{period_type}:{period_value}:{project_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(code=0, message="ok", data=cached)

    query = db.session.query(AdsEcProjectKpi)
    if period_type:
        query = query.filter(AdsEcProjectKpi.period_type == period_type)
    if period_value:
        query = query.filter(AdsEcProjectKpi.period_value == period_value)
    if project_id is not None:
        query = query.filter(AdsEcProjectKpi.project_id == project_id)

    rows = query.order_by(
        AdsEcProjectKpi.period_type, AdsEcProjectKpi.period_value, AdsEcProjectKpi.project_id
    ).all()
    data = [
        {
            "period_type": row.period_type,
            "period_value": row.period_value,
            "project_id": row.project_id,
            "project_name": _project_name(row.project_id),
            "found_cnt": row.ec_found_cnt,
            "resolved_cnt": row.ec_resolved_cnt,
            "response_minutes_sum": row.ec_response_minutes_sum,
            "resolve_minutes_sum": row.ec_resolve_minutes_sum,
            "recur_cnt": row.ec_recur_cnt,
            "resolution_rate": _float(row.ec_resolution_rate),
            "avg_response_minutes": _float(row.ec_avg_response_minutes),
            "avg_resolve_minutes": _float(row.ec_avg_resolve_minutes),
            "recur_rate": _float(row.ec_recur_rate),
            "severe_cnt": row.ec_severe_cnt,
        }
        for row in rows
    ]
    cache_set(cache_key, data)
    return jsonify(code=0, message="ok", data=data)
