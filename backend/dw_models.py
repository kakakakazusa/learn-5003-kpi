# -*- coding: utf-8 -*-
"""数仓库 `5003` 的 SQLAlchemy 数据模型。

表结构对齐 database/数据库设计文档.md，使用 Flask-SQLAlchemy 的 `dw` bind。
"""
from extensions import db


class BaseDW(db.Model):
    __abstract__ = True
    __bind_key__ = "dw"


# ---------- ODS ----------
class OdsHrEmployee(BaseDW):
    __tablename__ = "ods_hr_employee"

    employee_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    data_date = db.Column(db.Date, primary_key=True, nullable=False)
    employee_name = db.Column(db.String(80), nullable=False)
    department_id = db.Column(db.BigInteger)
    department_name = db.Column(db.String(80))
    team_id = db.Column(db.BigInteger)
    team_name = db.Column(db.String(80))
    domain_id = db.Column(db.BigInteger)
    domain_name = db.Column(db.String(80))
    position = db.Column(db.String(80))
    job_level = db.Column(db.String(32))
    employment_status = db.Column(db.String(16))
    join_date = db.Column(db.Date)
    manager_id = db.Column(db.BigInteger)
    etl_load_time = db.Column(db.DateTime, nullable=False)
    etl_source = db.Column(db.String(32), nullable=False)
    etl_batch_id = db.Column(db.String(64))
    etl_operation = db.Column(db.String(1), nullable=False)


class OdsPmPr(BaseDW):
    __tablename__ = "ods_pm_pr"

    pr_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    data_date = db.Column(db.Date, primary_key=True, nullable=False)
    pr_name = db.Column(db.String(128))
    employee_id = db.Column(db.BigInteger)
    project_id = db.Column(db.BigInteger)
    assign_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    complete_date = db.Column(db.Date)
    status = db.Column(db.String(16))
    rework_flag = db.Column(db.SmallInteger)
    work_hours = db.Column(db.Numeric(8, 2))
    etl_load_time = db.Column(db.DateTime, nullable=False)
    etl_source = db.Column(db.String(32), nullable=False)
    etl_batch_id = db.Column(db.String(64))
    etl_operation = db.Column(db.String(1), nullable=False)


class OdsItsmEc(BaseDW):
    __tablename__ = "ods_itsm_ec"

    ec_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    data_date = db.Column(db.Date, primary_key=True, nullable=False)
    ec_title = db.Column(db.String(128))
    employee_id = db.Column(db.BigInteger)
    project_id = db.Column(db.BigInteger)
    severity = db.Column(db.String(8))
    found_at = db.Column(db.DateTime)
    first_response_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    status = db.Column(db.String(16))
    recur_flag = db.Column(db.SmallInteger)
    etl_load_time = db.Column(db.DateTime, nullable=False)
    etl_source = db.Column(db.String(32), nullable=False)
    etl_batch_id = db.Column(db.String(64))
    etl_operation = db.Column(db.String(1), nullable=False)


# ---------- DWD ----------
class DwdPrFact(BaseDW):
    __tablename__ = "dwd_pr_fact"

    pr_key = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    pr_id = db.Column(db.BigInteger, nullable=False)
    employee_id = db.Column(db.BigInteger)
    assign_date_key = db.Column(db.Integer)
    due_date_key = db.Column(db.Integer)
    complete_date_key = db.Column(db.Integer)
    project_id = db.Column(db.BigInteger)
    status_code = db.Column(db.String(16))
    rework_flag = db.Column(db.SmallInteger)
    is_on_time = db.Column(db.SmallInteger)
    process_days = db.Column(db.Integer)
    work_hours = db.Column(db.Numeric(8, 2))


class DwdEcFact(BaseDW):
    __tablename__ = "dwd_ec_fact"

    ec_key = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    ec_id = db.Column(db.BigInteger, nullable=False)
    employee_id = db.Column(db.BigInteger)
    project_id = db.Column(db.BigInteger)
    severity_key = db.Column(db.SmallInteger)
    found_date_key = db.Column(db.Integer)
    resolved_date_key = db.Column(db.Integer)
    status_code = db.Column(db.String(16))
    recur_flag = db.Column(db.SmallInteger)
    is_severe = db.Column(db.SmallInteger)
    response_minutes = db.Column(db.Integer)
    resolve_minutes = db.Column(db.Integer)


# ---------- DIM ----------
class DimEmployee(BaseDW):
    __tablename__ = "dim_employee"

    employee_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    employee_name = db.Column(db.String(80), nullable=False)
    department_id = db.Column(db.BigInteger)
    team_id = db.Column(db.BigInteger)
    domain_id = db.Column(db.BigInteger)
    position_name = db.Column(db.String(80))
    job_level = db.Column(db.String(32))
    employment_status = db.Column(db.String(16))
    join_date = db.Column(db.Date)
    manager_id = db.Column(db.BigInteger)


class DimDepartment(BaseDW):
    __tablename__ = "dim_department"

    department_key = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    department_id = db.Column(db.BigInteger, nullable=False)
    department_name = db.Column(db.String(80), nullable=False)
    parent_department_id = db.Column(db.BigInteger)
    is_current = db.Column(db.SmallInteger, nullable=False, default=1)
    effective_date = db.Column(db.Date, nullable=False)
    expire_date = db.Column(db.Date, nullable=False)


class DimTeam(BaseDW):
    __tablename__ = "dim_team"

    team_key = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    team_id = db.Column(db.BigInteger, nullable=False)
    team_name = db.Column(db.String(80), nullable=False)
    department_id = db.Column(db.BigInteger)
    is_current = db.Column(db.SmallInteger, nullable=False, default=1)
    effective_date = db.Column(db.Date, nullable=False)
    expire_date = db.Column(db.Date, nullable=False)


class DimDomain(BaseDW):
    __tablename__ = "dim_domain"

    domain_key = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    domain_id = db.Column(db.BigInteger, nullable=False)
    domain_name = db.Column(db.String(80), nullable=False)
    is_current = db.Column(db.SmallInteger, nullable=False, default=1)
    effective_date = db.Column(db.Date, nullable=False)
    expire_date = db.Column(db.Date, nullable=False)


class DimDate(BaseDW):
    __tablename__ = "dim_date"

    date_key = db.Column(db.Integer, primary_key=True)
    full_date = db.Column(db.Date, nullable=False)
    year = db.Column(db.SmallInteger, nullable=False)
    quarter = db.Column(db.SmallInteger, nullable=False)
    month = db.Column(db.SmallInteger, nullable=False)
    week_of_year = db.Column(db.SmallInteger, nullable=False)
    day_of_week = db.Column(db.SmallInteger, nullable=False)
    is_weekend = db.Column(db.SmallInteger, nullable=False)
    is_holiday = db.Column(db.SmallInteger, nullable=False)


class DimSeverity(BaseDW):
    __tablename__ = "dim_severity"

    severity_key = db.Column(db.SmallInteger, primary_key=True)
    severity_code = db.Column(db.String(8), nullable=False)
    severity_name = db.Column(db.String(32), nullable=False)
    priority_order = db.Column(db.SmallInteger, nullable=False)


# ---------- DWM ----------
class DwmPrEmp1d(BaseDW):
    __tablename__ = "dwm_pr_emp_1d"

    stat_date = db.Column(db.Date, primary_key=True, nullable=False)
    employee_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    pr_assign_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_complete_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_due_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_on_time_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_rework_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_process_days_sum = db.Column(db.Integer, nullable=False, server_default="0")
    pr_work_hours_sum = db.Column(db.Numeric(12, 2), nullable=False, server_default="0")


class DwmEcEmp1d(BaseDW):
    __tablename__ = "dwm_ec_emp_1d"

    stat_date = db.Column(db.Date, primary_key=True, nullable=False)
    employee_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    ec_found_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolved_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_recur_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_severe_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_response_minutes_sum = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolve_minutes_sum = db.Column(db.Integer, nullable=False, server_default="0")


# ---------- DWS ----------
class DwsPrOrg1d(BaseDW):
    __tablename__ = "dws_pr_org_1d"

    stat_date = db.Column(db.Date, primary_key=True, nullable=False)
    org_type = db.Column(db.String(16), primary_key=True, nullable=False)
    org_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    pr_assign_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_complete_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_due_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_on_time_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_rework_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_process_days_sum = db.Column(db.Integer, nullable=False, server_default="0")
    pr_work_hours_sum = db.Column(db.Numeric(12, 2), nullable=False, server_default="0")


class DwsEcOrg1d(BaseDW):
    __tablename__ = "dws_ec_org_1d"

    stat_date = db.Column(db.Date, primary_key=True, nullable=False)
    org_type = db.Column(db.String(16), primary_key=True, nullable=False)
    org_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    ec_found_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolved_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_recur_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_severe_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_response_minutes_sum = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolve_minutes_sum = db.Column(db.Integer, nullable=False, server_default="0")


# ---------- ADS ----------
class AdsPrKpi(BaseDW):
    __tablename__ = "ads_pr_kpi"

    period_type = db.Column(db.String(16), primary_key=True, nullable=False)
    period_value = db.Column(db.String(32), primary_key=True, nullable=False)
    org_type = db.Column(db.String(16), primary_key=True, nullable=False)
    org_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    pr_assign_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_complete_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_due_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_on_time_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_process_days_sum = db.Column(db.Integer, nullable=False, server_default="0")
    pr_rework_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_completion_rate = db.Column(db.Numeric(8, 4))
    pr_on_time_rate = db.Column(db.Numeric(8, 4))
    pr_avg_process_days = db.Column(db.Numeric(8, 2))
    pr_rework_rate = db.Column(db.Numeric(8, 4))
    pr_work_hours_ratio = db.Column(db.Numeric(8, 4))


class AdsEcKpi(BaseDW):
    __tablename__ = "ads_ec_kpi"

    period_type = db.Column(db.String(16), primary_key=True, nullable=False)
    period_value = db.Column(db.String(32), primary_key=True, nullable=False)
    org_type = db.Column(db.String(16), primary_key=True, nullable=False)
    org_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    ec_found_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolved_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_response_minutes_sum = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolve_minutes_sum = db.Column(db.Integer, nullable=False, server_default="0")
    ec_recur_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolution_rate = db.Column(db.Numeric(8, 4))
    ec_avg_response_minutes = db.Column(db.Numeric(8, 2))
    ec_avg_resolve_minutes = db.Column(db.Numeric(8, 2))
    ec_recur_rate = db.Column(db.Numeric(8, 4))
    ec_severe_cnt = db.Column(db.Integer, nullable=False, server_default="0")


# ---------- 项目维度（与组织维度并列） ----------
class OdsPmProject(BaseDW):
    __tablename__ = "ods_pm_project"

    project_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    data_date = db.Column(db.Date, primary_key=True, nullable=False)
    project_name = db.Column(db.String(128))
    project_status = db.Column(db.String(16))
    owner_employee_id = db.Column(db.BigInteger)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    etl_load_time = db.Column(db.DateTime, nullable=False)
    etl_source = db.Column(db.String(32), nullable=False)
    etl_batch_id = db.Column(db.String(64))
    etl_operation = db.Column(db.String(1), nullable=False)


class DimProject(BaseDW):
    __tablename__ = "dim_project"

    project_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    project_name = db.Column(db.String(128), nullable=False)
    project_status = db.Column(db.String(16))
    owner_employee_id = db.Column(db.BigInteger)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)


class DwmPrProject1d(BaseDW):
    __tablename__ = "dwm_pr_project_1d"

    stat_date = db.Column(db.Date, primary_key=True, nullable=False)
    project_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    pr_assign_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_complete_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_due_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_on_time_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_rework_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_process_days_sum = db.Column(db.Integer, nullable=False, server_default="0")
    pr_work_hours_sum = db.Column(db.Numeric(12, 2), nullable=False, server_default="0")


class AdsPrProjectKpi(BaseDW):
    __tablename__ = "ads_pr_project_kpi"

    period_type = db.Column(db.String(16), primary_key=True, nullable=False)
    period_value = db.Column(db.String(32), primary_key=True, nullable=False)
    project_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    pr_assign_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_complete_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_due_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_on_time_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_process_days_sum = db.Column(db.Integer, nullable=False, server_default="0")
    pr_rework_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    pr_completion_rate = db.Column(db.Numeric(8, 4))
    pr_on_time_rate = db.Column(db.Numeric(8, 4))
    pr_avg_process_days = db.Column(db.Numeric(8, 2))
    pr_rework_rate = db.Column(db.Numeric(8, 4))
    pr_work_hours_ratio = db.Column(db.Numeric(8, 4))


class DwmEcProject1d(BaseDW):
    __tablename__ = "dwm_ec_project_1d"

    stat_date = db.Column(db.Date, primary_key=True, nullable=False)
    project_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    ec_found_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolved_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_recur_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_severe_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_response_minutes_sum = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolve_minutes_sum = db.Column(db.Integer, nullable=False, server_default="0")


class AdsEcProjectKpi(BaseDW):
    __tablename__ = "ads_ec_project_kpi"

    period_type = db.Column(db.String(16), primary_key=True, nullable=False)
    period_value = db.Column(db.String(32), primary_key=True, nullable=False)
    project_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    ec_found_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolved_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_response_minutes_sum = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolve_minutes_sum = db.Column(db.Integer, nullable=False, server_default="0")
    ec_recur_cnt = db.Column(db.Integer, nullable=False, server_default="0")
    ec_resolution_rate = db.Column(db.Numeric(8, 4))
    ec_avg_response_minutes = db.Column(db.Numeric(8, 2))
    ec_avg_resolve_minutes = db.Column(db.Numeric(8, 2))
    ec_recur_rate = db.Column(db.Numeric(8, 4))
    ec_severe_cnt = db.Column(db.Integer, nullable=False, server_default="0")


# 所有 dw 模型，供遍历/校验使用
DW_MODELS = [
    OdsHrEmployee, OdsPmPr, OdsItsmEc, OdsPmProject,
    DwdPrFact, DwdEcFact,
    DimEmployee, DimDepartment, DimTeam, DimDomain, DimDate, DimSeverity, DimProject,
    DwmPrEmp1d, DwmEcEmp1d, DwmPrProject1d, DwmEcProject1d,
    DwsPrOrg1d, DwsEcOrg1d,
    AdsPrKpi, AdsEcKpi, AdsPrProjectKpi, AdsEcProjectKpi,
]
