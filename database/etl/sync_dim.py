# -*- coding: utf-8 -*-
"""DIM 维度层同步。"""
from datetime import date, timedelta


def sync(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM dim_employee")
    cur.execute("DELETE FROM dim_department")
    cur.execute("DELETE FROM dim_team")
    cur.execute("DELETE FROM dim_domain")
    cur.execute("DELETE FROM dim_date")
    cur.execute("DELETE FROM dim_severity")
    cur.execute("DELETE FROM dim_project")

    cur.execute("""INSERT INTO dim_employee
        (employee_id, employee_name, department_id, team_id, domain_id, position_name, job_level,
         employment_status, join_date, manager_id)
        SELECT employee_id, employee_name, department_id, team_id, domain_id, position, job_level,
               employment_status, join_date, manager_id
        FROM ods_hr_employee
        WHERE data_date = (SELECT MAX(data_date) FROM ods_hr_employee)""")

    cur.execute("""INSERT INTO dim_department
        (department_id, department_name, is_current, effective_date, expire_date)
        SELECT DISTINCT department_id, department_name, 1, CURDATE(), '9999-12-31'
        FROM ods_hr_employee WHERE department_id IS NOT NULL""")

    cur.execute("""INSERT INTO dim_team
        (team_id, team_name, department_id, is_current, effective_date, expire_date)
        SELECT DISTINCT team_id, team_name, department_id, 1, CURDATE(), '9999-12-31'
        FROM ods_hr_employee WHERE team_id IS NOT NULL""")

    cur.execute("""INSERT INTO dim_domain
        (domain_id, domain_name, is_current, effective_date, expire_date)
        SELECT DISTINCT domain_id, domain_name, 1, CURDATE(), '9999-12-31'
        FROM ods_hr_employee WHERE domain_id IS NOT NULL""")

    cur.execute("""INSERT INTO dim_project
        (project_id, project_name, project_status, owner_employee_id, start_date, end_date)
        SELECT project_id, project_name, project_status, owner_employee_id, start_date, end_date
        FROM ods_pm_project
        WHERE data_date = (SELECT MAX(data_date) FROM ods_pm_project)""")

    year_min = date.today().year - 1
    year_max = date.today().year + 1
    d = date(year_min, 1, 1)
    end = date(year_max, 12, 31)
    while d <= end:
        cur.execute(
            """INSERT INTO dim_date (date_key, full_date, year, quarter, month, week_of_year, day_of_week, is_weekend, is_holiday)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0)""",
            (int(d.strftime("%Y%m%d")), d.isoformat(), d.year, (d.month - 1) // 3 + 1, d.month,
             d.isocalendar()[1], d.weekday(), 1 if d.weekday() >= 5 else 0),
        )
        d += timedelta(days=1)

    for key, code, name in [(1, "P0", "致命"), (2, "P1", "严重"), (3, "P2", "一般"), (4, "P3", "轻微")]:
        cur.execute("INSERT INTO dim_severity (severity_key, severity_code, severity_name, priority_order) VALUES (%s,%s,%s,%s)",
                    (key, code, name, key))

    conn.commit()
    cur.close()
    print("DIM 层同步完成")
