# -*- coding: utf-8 -*-
"""DWM 中间层同步。"""


def sync(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM dwm_pr_emp_1d")
    cur.execute("DELETE FROM dwm_ec_emp_1d")
    cur.execute("DELETE FROM dwm_pr_project_1d")

    # PR：承接按 assign_date，完成按 complete_date，分两次聚合后合并
    cur.execute("""INSERT INTO dwm_pr_emp_1d (stat_date, employee_id, pr_assign_cnt)
        SELECT d.full_date, f.employee_id, COUNT(*)
        FROM dwd_pr_fact f JOIN dim_date d ON d.date_key = f.assign_date_key
        WHERE f.employee_id IS NOT NULL
        GROUP BY d.full_date, f.employee_id
        ON DUPLICATE KEY UPDATE pr_assign_cnt = VALUES(pr_assign_cnt)""")

    cur.execute("""INSERT INTO dwm_pr_emp_1d
        (stat_date, employee_id, pr_complete_cnt, pr_due_cnt, pr_on_time_cnt, pr_rework_cnt, pr_process_days_sum)
        SELECT d.full_date, f.employee_id, COUNT(*), COUNT(*),
               SUM(f.is_on_time), SUM(f.rework_flag), SUM(f.process_days)
        FROM dwd_pr_fact f JOIN dim_date d ON d.date_key = f.complete_date_key
        WHERE f.employee_id IS NOT NULL AND f.complete_date_key IS NOT NULL
        GROUP BY d.full_date, f.employee_id
        ON DUPLICATE KEY UPDATE
          pr_complete_cnt = VALUES(pr_complete_cnt),
          pr_due_cnt = VALUES(pr_due_cnt),
          pr_on_time_cnt = VALUES(pr_on_time_cnt),
          pr_rework_cnt = VALUES(pr_rework_cnt),
          pr_process_days_sum = VALUES(pr_process_days_sum)""")

    # EC：发现按 found，解决按 resolved
    cur.execute("""INSERT INTO dwm_ec_emp_1d (stat_date, employee_id, ec_found_cnt, ec_response_minutes_sum)
        SELECT d.full_date, f.employee_id, COUNT(*), SUM(f.response_minutes)
        FROM dwd_ec_fact f JOIN dim_date d ON d.date_key = f.found_date_key
        WHERE f.employee_id IS NOT NULL
        GROUP BY d.full_date, f.employee_id
        ON DUPLICATE KEY UPDATE
          ec_found_cnt = VALUES(ec_found_cnt),
          ec_response_minutes_sum = VALUES(ec_response_minutes_sum)""")

    cur.execute("""INSERT INTO dwm_ec_emp_1d
        (stat_date, employee_id, ec_resolved_cnt, ec_recur_cnt, ec_severe_cnt, ec_resolve_minutes_sum)
        SELECT d.full_date, f.employee_id, COUNT(*), SUM(f.recur_flag), SUM(f.is_severe), SUM(f.resolve_minutes)
        FROM dwd_ec_fact f JOIN dim_date d ON d.date_key = f.resolved_date_key
        WHERE f.employee_id IS NOT NULL AND f.resolved_date_key IS NOT NULL
        GROUP BY d.full_date, f.employee_id
        ON DUPLICATE KEY UPDATE
          ec_resolved_cnt = VALUES(ec_resolved_cnt),
          ec_recur_cnt = VALUES(ec_recur_cnt),
          ec_severe_cnt = VALUES(ec_severe_cnt),
          ec_resolve_minutes_sum = VALUES(ec_resolve_minutes_sum)""")

    # 项目维度：按 project_id 聚合（承接按 assign_date，完成按 complete_date）
    cur.execute("""INSERT INTO dwm_pr_project_1d (stat_date, project_id, pr_assign_cnt)
        SELECT d.full_date, f.project_id, COUNT(*)
        FROM dwd_pr_fact f JOIN dim_date d ON d.date_key = f.assign_date_key
        WHERE f.project_id IS NOT NULL
        GROUP BY d.full_date, f.project_id
        ON DUPLICATE KEY UPDATE pr_assign_cnt = VALUES(pr_assign_cnt)""")

    cur.execute("""INSERT INTO dwm_pr_project_1d
        (stat_date, project_id, pr_complete_cnt, pr_due_cnt, pr_on_time_cnt, pr_rework_cnt, pr_process_days_sum)
        SELECT d.full_date, f.project_id, COUNT(*), COUNT(*),
               SUM(f.is_on_time), SUM(f.rework_flag), SUM(f.process_days)
        FROM dwd_pr_fact f JOIN dim_date d ON d.date_key = f.complete_date_key
        WHERE f.project_id IS NOT NULL AND f.complete_date_key IS NOT NULL
        GROUP BY d.full_date, f.project_id
        ON DUPLICATE KEY UPDATE
          pr_complete_cnt = VALUES(pr_complete_cnt),
          pr_due_cnt = VALUES(pr_due_cnt),
          pr_on_time_cnt = VALUES(pr_on_time_cnt),
          pr_rework_cnt = VALUES(pr_rework_cnt),
          pr_process_days_sum = VALUES(pr_process_days_sum)""")

    # EC 项目维度：按 project_id 聚合（发现按 found，解决按 resolved）
    cur.execute("""INSERT INTO dwm_ec_project_1d (stat_date, project_id, ec_found_cnt, ec_response_minutes_sum)
        SELECT d.full_date, f.project_id, COUNT(*), SUM(f.response_minutes)
        FROM dwd_ec_fact f JOIN dim_date d ON d.date_key = f.found_date_key
        WHERE f.project_id IS NOT NULL
        GROUP BY d.full_date, f.project_id
        ON DUPLICATE KEY UPDATE
          ec_found_cnt = VALUES(ec_found_cnt),
          ec_response_minutes_sum = VALUES(ec_response_minutes_sum)""")

    cur.execute("""INSERT INTO dwm_ec_project_1d
        (stat_date, project_id, ec_resolved_cnt, ec_recur_cnt, ec_severe_cnt, ec_resolve_minutes_sum)
        SELECT d.full_date, f.project_id, COUNT(*), SUM(f.recur_flag), SUM(f.is_severe), SUM(f.resolve_minutes)
        FROM dwd_ec_fact f JOIN dim_date d ON d.date_key = f.resolved_date_key
        WHERE f.project_id IS NOT NULL AND f.resolved_date_key IS NOT NULL
        GROUP BY d.full_date, f.project_id
        ON DUPLICATE KEY UPDATE
          ec_resolved_cnt = VALUES(ec_resolved_cnt),
          ec_recur_cnt = VALUES(ec_recur_cnt),
          ec_severe_cnt = VALUES(ec_severe_cnt),
          ec_resolve_minutes_sum = VALUES(ec_resolve_minutes_sum)""")

    conn.commit()
    cur.close()
    print("DWM 层同步完成")
