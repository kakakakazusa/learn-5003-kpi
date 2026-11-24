# -*- coding: utf-8 -*-
"""ADS 应用层同步（组织 × 周期 KPI）。"""


def sync(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM ads_pr_kpi")
    cur.execute("DELETE FROM ads_ec_kpi")
    cur.execute("DELETE FROM ads_pr_project_kpi")

    periods = {
        "week": "CONCAT(d.year, '-W', LPAD(d.week_of_year, 2, '0'))",
        "month": "CONCAT(d.year, '-', LPAD(d.month, 2, '0'))",
        "quarter": "CONCAT(d.year, '-Q', d.quarter)",
        "halfyear": "CONCAT(d.year, '-H', IF(d.month <= 6, 1, 2))",
        "year": "CAST(d.year AS CHAR)",
    }
    for ptype, expr in periods.items():
        cur.execute(
            """INSERT INTO ads_pr_kpi
               (period_type, period_value, org_type, org_id, pr_assign_cnt, pr_complete_cnt,
                pr_due_cnt, pr_on_time_cnt, pr_process_days_sum, pr_rework_cnt,
                pr_completion_rate, pr_on_time_rate, pr_avg_process_days, pr_rework_rate, pr_work_hours_ratio)
               SELECT '%s', %s, s.org_type, s.org_id, SUM(s.pr_assign_cnt), SUM(s.pr_complete_cnt),
                      SUM(s.pr_due_cnt), SUM(s.pr_on_time_cnt), SUM(s.pr_process_days_sum), SUM(s.pr_rework_cnt),
                      CASE WHEN SUM(s.pr_assign_cnt) > 0 THEN SUM(s.pr_complete_cnt) / SUM(s.pr_assign_cnt) ELSE NULL END,
                      CASE WHEN SUM(s.pr_due_cnt) > 0 THEN SUM(s.pr_on_time_cnt) / SUM(s.pr_due_cnt) ELSE NULL END,
                      CASE WHEN SUM(s.pr_complete_cnt) > 0 THEN SUM(s.pr_process_days_sum) / SUM(s.pr_complete_cnt) ELSE NULL END,
                      CASE WHEN SUM(s.pr_complete_cnt) > 0 THEN SUM(s.pr_rework_cnt) / SUM(s.pr_complete_cnt) ELSE NULL END,
                      NULL
               FROM dws_pr_org_1d s JOIN dim_date d ON d.full_date = s.stat_date
               GROUP BY %s, s.org_type, s.org_id""" % (ptype, expr, expr),
        )
        cur.execute(
            """INSERT INTO ads_ec_kpi
               (period_type, period_value, org_type, org_id, ec_found_cnt, ec_resolved_cnt,
                ec_response_minutes_sum, ec_resolve_minutes_sum, ec_recur_cnt,
                ec_resolution_rate, ec_avg_response_minutes, ec_avg_resolve_minutes, ec_recur_rate, ec_severe_cnt)
               SELECT '%s', %s, s.org_type, s.org_id, SUM(s.ec_found_cnt), SUM(s.ec_resolved_cnt),
                      SUM(s.ec_response_minutes_sum), SUM(s.ec_resolve_minutes_sum), SUM(s.ec_recur_cnt),
                      CASE WHEN SUM(s.ec_found_cnt) > 0 THEN SUM(s.ec_resolved_cnt) / SUM(s.ec_found_cnt) ELSE NULL END,
                      CASE WHEN SUM(s.ec_found_cnt) > 0 THEN SUM(s.ec_response_minutes_sum) / SUM(s.ec_found_cnt) ELSE NULL END,
                      CASE WHEN SUM(s.ec_resolved_cnt) > 0 THEN SUM(s.ec_resolve_minutes_sum) / SUM(s.ec_resolved_cnt) ELSE NULL END,
                      CASE WHEN SUM(s.ec_resolved_cnt) > 0 THEN SUM(s.ec_recur_cnt) / SUM(s.ec_resolved_cnt) ELSE NULL END,
                      SUM(s.ec_severe_cnt)
               FROM dws_ec_org_1d s JOIN dim_date d ON d.full_date = s.stat_date
               GROUP BY %s, s.org_type, s.org_id""" % (ptype, expr, expr),
        )
        cur.execute(
            """INSERT INTO ads_pr_project_kpi
               (period_type, period_value, project_id, pr_assign_cnt, pr_complete_cnt,
                pr_due_cnt, pr_on_time_cnt, pr_process_days_sum, pr_rework_cnt,
                pr_completion_rate, pr_on_time_rate, pr_avg_process_days, pr_rework_rate, pr_work_hours_ratio)
               SELECT '%s', %s, s.project_id, SUM(s.pr_assign_cnt), SUM(s.pr_complete_cnt),
                      SUM(s.pr_due_cnt), SUM(s.pr_on_time_cnt), SUM(s.pr_process_days_sum), SUM(s.pr_rework_cnt),
                      CASE WHEN SUM(s.pr_assign_cnt) > 0 THEN SUM(s.pr_complete_cnt) / SUM(s.pr_assign_cnt) ELSE NULL END,
                      CASE WHEN SUM(s.pr_due_cnt) > 0 THEN SUM(s.pr_on_time_cnt) / SUM(s.pr_due_cnt) ELSE NULL END,
                      CASE WHEN SUM(s.pr_complete_cnt) > 0 THEN SUM(s.pr_process_days_sum) / SUM(s.pr_complete_cnt) ELSE NULL END,
                      CASE WHEN SUM(s.pr_complete_cnt) > 0 THEN SUM(s.pr_rework_cnt) / SUM(s.pr_complete_cnt) ELSE NULL END,
                      NULL
               FROM dwm_pr_project_1d s JOIN dim_date d ON d.full_date = s.stat_date
               GROUP BY %s, s.project_id""" % (ptype, expr, expr),
        )

    conn.commit()
    cur.close()
    print("ADS 层同步完成")
