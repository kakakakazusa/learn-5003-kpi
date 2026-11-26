# -*- coding: utf-8 -*-
"""DWS summary layer sync (organization x day)."""


def sync(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM dws_pr_org_1d")
    cur.execute("DELETE FROM dws_ec_org_1d")

    # Employee x day -> team / domain / department x day (rolling aggregation)
    cur.execute("""INSERT INTO dws_pr_org_1d
        SELECT m.stat_date, 'employee', e.employee_id, SUM(m.pr_assign_cnt), SUM(m.pr_complete_cnt),
               SUM(m.pr_due_cnt), SUM(m.pr_on_time_cnt), SUM(m.pr_rework_cnt),
               SUM(m.pr_process_days_sum), SUM(m.pr_work_hours_sum)
        FROM dwm_pr_emp_1d m JOIN dim_employee e ON e.employee_id = m.employee_id
        GROUP BY m.stat_date, e.employee_id""")
    for org_type, col in (("team", "team_id"), ("domain", "domain_id"), ("department", "department_id")):
        cur.execute(
            """INSERT INTO dws_pr_org_1d
               SELECT m.stat_date, '%s', e.%s, SUM(m.pr_assign_cnt), SUM(m.pr_complete_cnt),
                      SUM(m.pr_due_cnt), SUM(m.pr_on_time_cnt), SUM(m.pr_rework_cnt),
                      SUM(m.pr_process_days_sum), SUM(m.pr_work_hours_sum)
               FROM dwm_pr_emp_1d m JOIN dim_employee e ON e.employee_id = m.employee_id
               WHERE e.%s IS NOT NULL GROUP BY m.stat_date, e.%s""" % (org_type, col, col, col),
        )

    cur.execute("""INSERT INTO dws_ec_org_1d
        SELECT m.stat_date, 'employee', e.employee_id, SUM(m.ec_found_cnt), SUM(m.ec_resolved_cnt),
               SUM(m.ec_recur_cnt), SUM(m.ec_severe_cnt), SUM(m.ec_response_minutes_sum), SUM(m.ec_resolve_minutes_sum)
        FROM dwm_ec_emp_1d m JOIN dim_employee e ON e.employee_id = m.employee_id
        GROUP BY m.stat_date, e.employee_id""")
    for org_type, col in (("team", "team_id"), ("domain", "domain_id"), ("department", "department_id")):
        cur.execute(
            """INSERT INTO dws_ec_org_1d
               SELECT m.stat_date, '%s', e.%s, SUM(m.ec_found_cnt), SUM(m.ec_resolved_cnt),
                      SUM(m.ec_recur_cnt), SUM(m.ec_severe_cnt), SUM(m.ec_response_minutes_sum), SUM(m.ec_resolve_minutes_sum)
               FROM dwm_ec_emp_1d m JOIN dim_employee e ON e.employee_id = m.employee_id
               WHERE e.%s IS NOT NULL GROUP BY m.stat_date, e.%s""" % (org_type, col, col, col),
        )

    conn.commit()
    cur.close()
    print("DWS layer sync complete")
