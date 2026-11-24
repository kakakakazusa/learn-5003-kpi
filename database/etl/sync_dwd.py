# -*- coding: utf-8 -*-
"""DWD 明细层同步。"""


def sync(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM dwd_pr_fact")
    cur.execute("DELETE FROM dwd_ec_fact")

    cur.execute("""INSERT INTO dwd_pr_fact
        (pr_id, employee_id, assign_date_key, due_date_key, complete_date_key, project_id, status_code,
         rework_flag, is_on_time, process_days, work_hours)
        SELECT p.pr_id, e.employee_id,
               CAST(DATE_FORMAT(p.assign_date, '%Y%m%d') AS UNSIGNED),
               CAST(DATE_FORMAT(p.due_date, '%Y%m%d') AS UNSIGNED),
               CAST(DATE_FORMAT(p.complete_date, '%Y%m%d') AS UNSIGNED),
               p.project_id, p.status, p.rework_flag,
               CASE WHEN p.complete_date IS NOT NULL AND p.complete_date <= p.due_date THEN 1 ELSE 0 END,
               CASE WHEN p.complete_date IS NOT NULL THEN DATEDIFF(p.complete_date, p.assign_date) ELSE NULL END,
               p.work_hours
        FROM ods_pm_pr p
        LEFT JOIN dim_employee e ON e.employee_id = p.employee_id""")

    cur.execute("""INSERT INTO dwd_ec_fact
        (ec_id, employee_id, project_id, severity_key, found_date_key, resolved_date_key, status_code,
         recur_flag, is_severe, response_minutes, resolve_minutes)
        SELECT c.ec_id, e.employee_id, c.project_id, s.severity_key,
               CAST(DATE_FORMAT(c.found_at, '%Y%m%d') AS UNSIGNED),
               CAST(DATE_FORMAT(c.resolved_at, '%Y%m%d') AS UNSIGNED),
               c.status, c.recur_flag,
               CASE WHEN c.severity IN ('P0','P1') THEN 1 ELSE 0 END,
               TIMESTAMPDIFF(MINUTE, c.found_at, c.first_response_at),
               CASE WHEN c.resolved_at IS NOT NULL THEN TIMESTAMPDIFF(MINUTE, c.found_at, c.resolved_at) ELSE NULL END
        FROM ods_itsm_ec c
        LEFT JOIN dim_employee e ON e.employee_id = c.employee_id
        LEFT JOIN dim_severity s ON s.severity_code = c.severity""")

    conn.commit()
    cur.close()
    print("DWD 层同步完成")
