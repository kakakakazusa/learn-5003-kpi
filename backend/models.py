# -*- coding: utf-8 -*-
"""业务库（默认 bind）的 SQLAlchemy 数据模型。"""
from extensions import db


class SalesRecord(db.Model):
    __tablename__ = "sales_records"

    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.Date, nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    region = db.Column(db.String(80), nullable=False, index=True)
    revenue = db.Column(db.Numeric(12, 2), nullable=False)
    order_count = db.Column(db.Integer, nullable=False)


class EmployeeKPIRecord(db.Model):
    __tablename__ = "employee_kpi_records"

    id = db.Column(db.Integer, primary_key=True)
    record_date = db.Column(db.Date, nullable=False, index=True)
    employee_name = db.Column(db.String(80), nullable=False, index=True)
    department = db.Column(db.String(80), nullable=False, index=True)
    revenue = db.Column(db.Numeric(12, 2), nullable=False)
    revenue_target = db.Column(db.Numeric(12, 2), nullable=False)
    orders = db.Column(db.Integer, nullable=False)
    satisfaction = db.Column(db.Numeric(4, 2), nullable=False)
